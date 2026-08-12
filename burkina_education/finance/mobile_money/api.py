# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted entry points for the mobile money flow (docs/architecture.md
section H). Every external call is logged through Frappe's own
``Integration Request`` doctype; every accounting side-effect (crediting a
Sales Invoice) happens only after ``gateway.get_adapter(...).verify()``
confirms success server-side - never from the raw webhook payload or a
client redirect (master.md §28).
"""

import hmac
import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime, nowdate

from burkina_education.finance.mobile_money.gateway import get_adapter

REFERENCE_DOCTYPES = {"Sales Invoice"}


def _log_integration_request(service, description, reference_name=None, data=None):
	return frappe.get_doc(
		{
			"doctype": "Integration Request",
			"integration_request_service": service,
			"request_description": description,
			"reference_doctype": "Mobile Money Transaction" if reference_name else None,
			"reference_docname": reference_name,
			"data": json.dumps(data) if data else None,
			"is_remote_request": 1,
			"status": "Queued",
		}
	).insert(ignore_permissions=True)


@frappe.whitelist()
def initiate_payment(reference_doctype, reference_name, provider, phone_number, amount=None):
	"""Start a mobile money payment against an outstanding Sales Invoice."""
	if reference_doctype not in REFERENCE_DOCTYPES:
		frappe.throw(_("Type de document non pris en charge pour le paiement mobile money."))

	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	frappe.has_permission(reference_doctype, "read", ref_doc, throw=True)
	if ref_doc.docstatus != 1:
		frappe.throw(_("Ce document n'est pas encore validé."))

	outstanding = flt(ref_doc.outstanding_amount)
	if outstanding <= 0:
		frappe.throw(_("Ce document ne présente aucun montant impayé."))

	amount = flt(amount) or outstanding
	if amount > outstanding:
		frappe.throw(_("Le montant dépasse le solde impayé."))

	provider_doc = frappe.get_doc("Mobile Money Provider", provider)
	if not provider_doc.is_active:
		frappe.throw(_("Ce fournisseur de paiement mobile money n'est pas actif."))

	transaction = frappe.get_doc(
		{
			"doctype": "Mobile Money Transaction",
			"provider": provider_doc.name,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"student": ref_doc.get("student"),
			"phone_number": phone_number,
			"amount": amount,
			"currency": provider_doc.currency or ref_doc.get("currency"),
			"status": "Initiated",
			"initiated_by": frappe.session.user,
			"initiated_on": now_datetime(),
		}
	).insert(ignore_permissions=True)

	log = _log_integration_request(
		provider_doc.provider_name, f"Initiation paiement {transaction.name}", transaction.name
	)

	adapter = get_adapter(provider_doc)
	try:
		result = adapter.initiate(transaction)
	except Exception:
		transaction.db_set("status", "Failed")
		log.db_set("status", "Failed")
		log.db_set("error", frappe.get_traceback())
		frappe.log_error(
			title="Mobile Money initiate failed",
			reference_doctype="Mobile Money Transaction",
			reference_name=transaction.name,
		)
		frappe.throw(_("Le paiement n'a pas pu être initié. Veuillez réessayer ou contacter l'administration."))

	transaction.db_set("gateway_transaction_id", result.get("gateway_transaction_id"))
	transaction.db_set("status", result.get("status") or "Pending")
	log.db_set("status", "Completed")
	log.db_set("output", json.dumps(result))

	return {"transaction": transaction.name, "status": transaction.status}


@frappe.whitelist(allow_guest=True)
def webhook(provider, gateway_transaction_id, status=None, signature=None, **kwargs):
	"""Server-to-server payment confirmation callback. Idempotent (a repeated
	callback for an already-processed transaction is a no-op, not an error)
	and rejects anything that doesn't match a known, active provider + a
	transaction it actually issued.
	"""
	log = _log_integration_request(
		provider,
		f"Callback {gateway_transaction_id}",
		data={"provider": provider, "gateway_transaction_id": gateway_transaction_id, "status": status, **kwargs},
	)

	def reject(reason):
		log.db_set("status", "Failed")
		log.db_set("error", reason)
		# French, user-facing, no stack trace (master.md §63).
		frappe.throw(_("Le paiement n'a pas pu être confirmé. Veuillez réessayer ou contacter l'administration."))

	if not frappe.db.exists("Mobile Money Provider", provider):
		reject("Fournisseur inconnu")
	provider_doc = frappe.get_doc("Mobile Money Provider", provider)
	if not provider_doc.is_active:
		reject("Fournisseur inactif")

	expected_secret = provider_doc.get_password("webhook_secret", raise_exception=False)
	if expected_secret and not hmac.compare_digest(str(signature or ""), expected_secret):
		reject("Signature de callback invalide")

	transaction_name = frappe.db.get_value(
		"Mobile Money Transaction",
		{"gateway_transaction_id": gateway_transaction_id, "provider": provider_doc.name},
	)
	if not transaction_name:
		reject("Transaction inconnue pour ce fournisseur")

	transaction = frappe.get_doc("Mobile Money Transaction", transaction_name)
	log.db_set("reference_docname", transaction.name)

	if transaction.status == "Success":
		# Duplicate/replayed callback - not an error, just don't reprocess.
		log.db_set("status", "Completed")
		log.db_set("output", json.dumps({"already_processed": True}))
		return {"status": "already_processed", "transaction": transaction.name}

	adapter = get_adapter(provider_doc)
	verified = adapter.verify(transaction)
	transaction.db_set("raw_response", json.dumps({"payload_status": status, "verified": verified}))

	if verified.get("status") == "Success":
		payment_entry = _create_payment_entry(transaction, provider_doc)
		transaction.db_set("status", "Success")
		transaction.db_set("payment_entry", payment_entry)
		transaction.db_set("verified_on", now_datetime())
		log.db_set("status", "Completed")
		log.db_set("output", json.dumps(verified))
		return {"status": "success", "transaction": transaction.name, "payment_entry": payment_entry}

	transaction.db_set("status", "Failed")
	transaction.db_set("failure_reason", verified.get("message") or "Vérification échouée auprès du fournisseur")
	log.db_set("status", "Failed")
	log.db_set("error", json.dumps(verified))
	return {"status": "failed", "transaction": transaction.name}


def _create_payment_entry(transaction, provider_doc):
	"""Reconcile a confirmed mobile money transaction as a normal Payment
	Entry, reusing ERPNext's own helper so party/accounts/currency are set
	exactly the way the "Payment" button in the UI would set them."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	pe = get_payment_entry(
		transaction.reference_doctype, transaction.reference_name, party_amount=transaction.amount
	)
	pe.mode_of_payment = provider_doc.mode_of_payment
	pe.reference_no = transaction.gateway_transaction_id or transaction.name
	pe.reference_date = nowdate()
	for ref in pe.references:
		ref.allocated_amount = transaction.amount
	pe.insert(ignore_permissions=True)
	pe.submit()
	return pe.name
