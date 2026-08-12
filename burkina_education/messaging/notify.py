# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""The Communication Center's delivery engine (master.md §32): every other
notification-triggering module (attendance alerts, mobile money/Payment
Entry confirmation, fee reminders, result-available, announcements) calls
``notify_event`` here rather than talking to Message Log/Messaging Provider
directly - see docs/architecture.md section J.

    notify_event(event_key, guardians=[...], students=[...], ...)
       |
    resolve_template(event_key, channel)         (Notification Template)
       |
    render (Jinja, per-recipient context)
       |
    queue_message()  -> Message Log (status=Queued)
       |
    dispatch_message() -> Messaging Provider adapter (messaging/gateway.py)
       |                  or frappe.core Notification Log (In-App)
       |                  or frappe.sendmail (Email)
    Message Log status=Sent/Failed

A guardian is only ever contacted on a channel they've consented to
(``sms_consent``/``portal_access``) - master.md §12/§34 ("opt-in/opt-out",
"respect preferences"). Nothing here assumes a template exists for every
channel; a missing template silently skips that channel/recipient rather
than throwing, since schools configure their own message wording (master.md
§57: "configuration over hard-coding").
"""

import json

import frappe
from frappe.utils import now_datetime

#: Channels we know how to actually deliver today - see Messaging Provider's
#: PROVIDER_ADAPTERS / this module's _dispatch_* dispatch table. Real
#: providers can be added later without touching call sites.
DELIVERABLE_CHANNELS = ("SMS", "WhatsApp", "Email", "In-App")


def resolve_template(event_key, channel, language=None):
	filters = {"event_key": event_key, "channel": channel, "is_active": 1}
	if language:
		filters["language"] = language
	name = frappe.db.get_value("Notification Template", filters, order_by="modified desc")
	if not name and language:
		# Fall back to any active template for this event/channel regardless
		# of language, rather than silently sending nothing.
		name = frappe.db.get_value(
			"Notification Template", {"event_key": event_key, "channel": channel, "is_active": 1}
		)
	return frappe.get_cached_doc("Notification Template", name) if name else None


def render(text, context):
	if not text:
		return text
	return frappe.render_template(text, context or {})


def notify_event(
	event_key,
	*,
	guardians=None,
	students=None,
	users=None,
	context=None,
	channels=None,
	reference_doctype=None,
	reference_name=None,
	background=False,
):
	"""High-level fan-out entry point. ``context`` is merged with per-recipient
	fields (student_name/guardian_name/...) before rendering. ``channels``
	restricts delivery to a subset (e.g. an Announcement's checked boxes);
	omitted, it defaults to each guardian's own ``preferred_channel`` plus
	in-app for any linked User.

	Returns a summary dict; safe to call from a scheduled job, a webhook, or
	a Desk button.
	"""
	if background:
		frappe.enqueue(
			"burkina_education.messaging.notify.notify_event",
			queue="short",
			event_key=event_key,
			guardians=guardians,
			students=students,
			users=users,
			context=context,
			channels=channels,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			background=False,
		)
		return {"queued": True}

	context = dict(context or {})
	summary = {"queued": 0, "sent": 0, "failed": 0, "skipped": 0}

	for guardian_name in guardians or []:
		_notify_guardian(event_key, guardian_name, context, channels, reference_doctype, reference_name, summary)

	for user_name in users or []:
		_notify_user(event_key, user_name, context, channels, reference_doctype, reference_name, summary)

	# Students only get In-App/Email (no phone-based channel of their own
	# tracked yet) via their linked portal User, if any.
	if students:
		student_rows = frappe.get_all(
			"Student", filters={"name": ["in", students]}, fields=["name", "student_name", "user"]
		)
		for row in student_rows:
			if not row.user:
				summary["skipped"] += 1
				continue
			row_context = dict(context, student_name=row.student_name)
			_notify_user(
				event_key, row.user, row_context, channels or ["In-App"], reference_doctype, reference_name, summary
			)

	return summary


def _notify_guardian(event_key, guardian_name, context, channels, reference_doctype, reference_name, summary):
	guardian = frappe.db.get_value(
		"Guardian",
		guardian_name,
		["name", "guardian_name", "mobile_number", "whatsapp_number", "email_address", "user",
		 "preferred_channel", "sms_consent", "whatsapp_consent", "portal_access"],
		as_dict=True,
	)
	if not guardian:
		summary["skipped"] += 1
		return

	row_context = dict(context, guardian_name=guardian.guardian_name)
	# Guardian.preferred_channel's own options ("Portail") don't literally
	# match this module's channel names ("In-App") - translate rather than
	# renaming the user-facing field option.
	preferred = "In-App" if guardian.preferred_channel == "Portail" else (guardian.preferred_channel or "SMS")
	wanted_channels = channels or [preferred]

	for channel in wanted_channels:
		if channel == "SMS":
			if not (guardian.sms_consent and guardian.mobile_number):
				summary["skipped"] += 1
				continue
			_send(
				event_key, "SMS", "Guardian", guardian.name, row_context,
				phone_number=guardian.mobile_number, reference_doctype=reference_doctype,
				reference_name=reference_name, summary=summary,
			)
		elif channel == "WhatsApp":
			if not (guardian.whatsapp_consent and guardian.whatsapp_number):
				summary["skipped"] += 1
				continue
			_send(
				event_key, "WhatsApp", "Guardian", guardian.name, row_context,
				phone_number=guardian.whatsapp_number, reference_doctype=reference_doctype,
				reference_name=reference_name, summary=summary,
			)
		elif channel == "Email":
			if not guardian.email_address:
				summary["skipped"] += 1
				continue
			_send(
				event_key, "Email", "Guardian", guardian.name, row_context,
				email_address=guardian.email_address, reference_doctype=reference_doctype,
				reference_name=reference_name, summary=summary,
			)
		elif channel == "In-App":
			if not (guardian.portal_access and guardian.user):
				summary["skipped"] += 1
				continue
			_notify_user(event_key, guardian.user, row_context, ["In-App"], reference_doctype, reference_name, summary)


def _notify_user(event_key, user_name, context, channels, reference_doctype, reference_name, summary):
	channels = channels or ["In-App"]
	for channel in channels:
		if channel == "In-App":
			_send(
				event_key, "In-App", "User", user_name, context,
				reference_doctype=reference_doctype, reference_name=reference_name, summary=summary,
			)
		elif channel == "Email":
			email = frappe.db.get_value("User", user_name, "email")
			if not email:
				summary["skipped"] += 1
				continue
			_send(
				event_key, "Email", "User", user_name, context, email_address=email,
				reference_doctype=reference_doctype, reference_name=reference_name, summary=summary,
			)


def _send(
	event_key, channel, recipient_doctype, recipient, context,
	*, phone_number=None, email_address=None, reference_doctype=None, reference_name=None, summary,
):
	template = resolve_template(event_key, channel)
	if not template and channel != "In-App":
		# No template configured for this event/channel - the school hasn't
		# set one up (master.md §57), nothing to send. Not an error.
		summary["skipped"] += 1
		return

	subject = render(template.subject, context) if template else context.get("title")
	body = render(template.body, context) if template else context.get("content")
	if not body:
		summary["skipped"] += 1
		return

	log = frappe.get_doc(
		{
			"doctype": "Message Log",
			"channel": channel,
			"status": "Queued",
			"event_key": event_key,
			"template": template.name if template else None,
			"recipient_doctype": recipient_doctype,
			"recipient": recipient,
			"phone_number": phone_number,
			"email_address": email_address,
			"subject": subject,
			"message": body,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"queued_on": now_datetime(),
		}
	).insert(ignore_permissions=True)
	summary["queued"] += 1

	try:
		dispatch_message(log)
		summary["sent"] += 1
	except Exception:
		summary["failed"] += 1
		frappe.log_error(title="Message Log dispatch failed", reference_doctype="Message Log", reference_name=log.name)


def dispatch_message(log):
	"""Actually deliver one Message Log. Raises on failure (state already
	recorded on ``log`` either way) so callers can count failures."""
	if isinstance(log, str):
		log = frappe.get_doc("Message Log", log)

	try:
		if log.channel == "In-App":
			_dispatch_in_app(log)
		elif log.channel == "Email":
			_dispatch_email(log)
		elif log.channel in ("SMS", "WhatsApp"):
			_dispatch_sms_or_whatsapp(log)
		else:
			raise ValueError(f"Canal non pris en charge: {log.channel}")
	except Exception as e:
		log.db_set("status", "Failed")
		log.db_set("error", str(e))
		log.db_set("retry_count", (log.retry_count or 0) + 1)
		raise

	log.db_set("status", "Sent")
	log.db_set("sent_on", now_datetime())


def _dispatch_in_app(log):
	for_user = log.recipient if log.recipient_doctype == "User" else None
	if not for_user:
		raise ValueError("Notification In-App sans utilisateur destinataire.")

	notification = frappe.new_doc("Notification Log")
	notification.for_user = for_user
	notification.set("type", "Alert")
	notification.title = log.subject or log.message[:140]
	notification.subject = log.subject or log.message[:140]
	notification.description = log.message
	notification.email_content = log.message
	notification.document_type = log.reference_doctype
	notification.document_name = log.reference_name
	notification.insert(ignore_permissions=True)


def _dispatch_email(log):
	frappe.sendmail(
		recipients=[log.email_address],
		subject=log.subject or "Burkina Education",
		message=log.message,
		reference_doctype=log.reference_doctype,
		reference_name=log.reference_name,
		now=True,
	)


def _dispatch_sms_or_whatsapp(log):
	from burkina_education.messaging.gateway import get_adapter, get_default_provider

	provider = get_default_provider(log.channel)
	if not provider:
		raise ValueError(f"Aucun fournisseur de messagerie actif configuré pour le canal {log.channel}.")

	log.db_set("provider", provider.name)
	adapter = get_adapter(provider)
	result = adapter.send(log)

	log.db_set("provider_response", json.dumps(result.get("response")) if result.get("response") else None)
	if result.get("provider_message_id"):
		log.db_set("provider_message_id", result["provider_message_id"])

	if result.get("status") != "Sent":
		raise ValueError(result.get("response") or "Échec d'envoi signalé par le fournisseur")
