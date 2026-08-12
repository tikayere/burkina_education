# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Finance-triggered notifications (master.md §32 examples "Payment
confirmation"/"Fee reminder") - thin glue between finance events and
communication.notify.notify_event(), mirroring finance/discounts.py's own
"only acts on invoices generated from a school Fee Schedule" guard so this
never fires for an arbitrary ERPNext sale. See docs/architecture.md section J.
"""

import frappe
from frappe.utils import add_days, fmt_money, getdate, nowdate

from burkina_education.messaging.notify import notify_event

#: How many days an overdue invoice must go without a reminder before
#: another one is sent - avoids nagging a guardian daily for the same bill.
DEFAULT_REMINDER_INTERVAL_DAYS = 7


def _fee_guardians(student):
	"""Guardians flagged ``payment_responsibility`` for this student; falls
	back to every guardian if none is explicitly flagged (master.md §12:
	"payment responsibility" is opt-in per guardian, not mandatory)."""
	rows = frappe.get_all(
		"Student Guardian", filters={"parent": student}, pluck="guardian"
	)
	if not rows:
		return []
	responsible = frappe.get_all(
		"Guardian", filters={"name": ["in", rows], "payment_responsibility": 1}, pluck="name"
	)
	return responsible or rows


def notify_payment_confirmation(doc, method=None):
	"""``doc_events`` hook on Payment Entry.on_submit - covers both a normal
	cash/bank payment and a mobile money confirmation (finance/mobile_money/
	api.py creates and submits a real Payment Entry too, so this single hook
	is the one place this fires, never duplicated).

	A notification failure must never block the payment itself from being
	recorded (master.md §63) - the whole body is defensive; any error is
	logged, not raised.
	"""
	try:
		_notify_payment_confirmation(doc)
	except Exception:
		frappe.log_error(
			title="Payment Confirmation notification failed",
			reference_doctype="Payment Entry",
			reference_name=doc.name,
		)


def _notify_payment_confirmation(doc):
	if doc.payment_type != "Receive" or doc.party_type != "Customer":
		return

	student = None
	outstanding = None
	for ref in doc.references:
		if ref.reference_doctype != "Sales Invoice":
			continue
		row = frappe.db.get_value("Sales Invoice", ref.reference_name, ["student", "outstanding_amount"], as_dict=True)
		if row and row.student:
			student, outstanding = row.student, row.outstanding_amount
			break
	if not student:
		return

	guardians = _fee_guardians(student)
	if not guardians:
		return

	student_name = frappe.db.get_value("Student", student, "student_name")
	notify_event(
		"Payment Confirmation",
		guardians=guardians,
		context={
			"student_name": student_name,
			"amount": fmt_money(doc.paid_amount, currency=doc.paid_to_account_currency),
			"currency": doc.paid_to_account_currency,
			"reference": doc.reference_no or doc.name,
			"balance": fmt_money(outstanding, currency=doc.paid_to_account_currency),
		},
		reference_doctype="Payment Entry",
		reference_name=doc.name,
	)


@frappe.whitelist()
def run_fee_reminders(interval_days=None):
	"""Scheduled daily (hooks.py) - one reminder per overdue school-fee
	invoice at most every ``interval_days`` (Burkina Education Settings, or
	DEFAULT_REMINDER_INTERVAL_DAYS)."""
	interval_days = (
		interval_days
		or frappe.db.get_single_value("Burkina Education Settings", "fee_reminder_interval_days")
		or DEFAULT_REMINDER_INTERVAL_DAYS
	)

	overdue = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"outstanding_amount": [">", 0],
			"due_date": ["<", nowdate()],
			"student": ["is", "set"],
		},
		fields=["name", "student", "outstanding_amount", "currency", "due_date"],
	)

	notified = []
	for inv in overdue:
		last_reminder = frappe.db.get_value(
			"Message Log",
			{"event_key": "Fee Reminder", "reference_doctype": "Sales Invoice", "reference_name": inv.name},
			"queued_on",
			order_by="queued_on desc",
		)
		if last_reminder and getdate(last_reminder) > getdate(add_days(nowdate(), -interval_days)):
			continue

		guardians = _fee_guardians(inv.student)
		if not guardians:
			continue

		student_name = frappe.db.get_value("Student", inv.student, "student_name")
		notify_event(
			"Fee Reminder",
			guardians=guardians,
			context={
				"student_name": student_name,
				"amount": fmt_money(inv.outstanding_amount, currency=inv.currency),
				"currency": inv.currency,
				"due_date": frappe.utils.formatdate(inv.due_date),
				"invoice": inv.name,
			},
			reference_doctype="Sales Invoice",
			reference_name=inv.name,
		)
		notified.append(inv.name)

	return notified
