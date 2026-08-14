# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Finance (Accountant) Portal. Sales
Invoice/Payment Entry/Scholarship/Mobile Money Transaction listing and
detail is done directly from the frontend via ``frappe-ui``'s generic list/
document resources — the Accountant role already has full permissions on
every one of those doctypes (docs/architecture.md section M). This module
supplies the dashboard and the two actions a generic form can't express
cleanly: recording a manual payment against an invoice (reuses ERPNext's own
``get_payment_entry`` so accounts/party are populated exactly as the "Pay"
button in Desk would) and retrying a stuck mobile money verification.
"""

import frappe
from frappe.utils import flt, get_first_day, get_last_day, nowdate

from burkina_education.portal.permissions import elevated, require_any_role


@frappe.whitelist()
def get_dashboard():
	require_any_role("Accountant")

	outstanding_rows = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "outstanding_amount", "due_date"],
	)
	outstanding_total = sum(flt(r.outstanding_amount) for r in outstanding_rows)
	overdue_rows = [r for r in outstanding_rows if r.due_date and r.due_date < frappe.utils.getdate(nowdate())]
	overdue_total = sum(flt(r.outstanding_amount) for r in overdue_rows)

	month_start, month_end = get_first_day(nowdate()), get_last_day(nowdate())
	collected_this_month = frappe.db.sql(
		"""
		select coalesce(sum(paid_amount), 0)
		from `tabPayment Entry`
		where docstatus = 1 and payment_type = 'Receive'
		and posting_date between %(start)s and %(end)s
		""",
		{"start": month_start, "end": month_end},
	)[0][0]

	pending_scholarships = frappe.db.count("Scholarship", {"status": "Brouillon"})
	pending_mobile_money = frappe.db.count("Mobile Money Transaction", {"status": ["in", ("Initiated", "Pending")]})

	by_category = []
	try:
		from burkina_education.finance.report.fee_collection_by_category.fee_collection_by_category import (
			get_data,
		)

		by_category = get_data(frappe._dict())[:6]
	except Exception:
		# Best-effort chart data - a report-query regression shouldn't take
		# the whole dashboard down with it.
		frappe.log_error(title="Finance dashboard: fee_collection_by_category unavailable")

	top_overdue = sorted(overdue_rows, key=lambda r: flt(r.outstanding_amount), reverse=True)[:10]
	for r in top_overdue:
		r["student"] = frappe.db.get_value("Sales Invoice", r.name, "student")
		r["student_name"] = r.student and frappe.db.get_value("Student", r.student, "student_name")

	return {
		"outstanding_total": outstanding_total,
		"outstanding_count": len(outstanding_rows),
		"overdue_total": overdue_total,
		"overdue_count": len(overdue_rows),
		"collected_this_month": flt(collected_this_month),
		"pending_scholarships": pending_scholarships,
		"pending_mobile_money": pending_mobile_money,
		"by_category": by_category,
		"top_overdue": top_overdue,
		"monthly_collections": monthly_collections(),
	}


def monthly_collections(months=6):
	"""Payment Entry receipts, summed by calendar month, for the last
	``months`` months - powers the finance dashboard's collection-trend
	chart. Same Payment Entry scope/table ``get_dashboard`` already reads
	above (``collected_this_month``), just grouped instead of collapsed to
	one figure - no permission expansion.
	"""
	from frappe.utils import add_months, getdate

	from burkina_education.portal.common import MONTH_ABBR_FR

	start = getdate(add_months(nowdate(), -(months - 1))).replace(day=1)
	rows = frappe.db.sql(
		"""
		select date_format(posting_date, '%%Y-%%m') as ym, coalesce(sum(paid_amount), 0) as total
		from `tabPayment Entry`
		where docstatus = 1 and payment_type = 'Receive' and posting_date >= %(start)s
		group by ym
		""",
		{"start": start},
		as_dict=True,
	)
	by_month = {r.ym: flt(r.total) for r in rows}

	out = []
	cursor = start
	for _ in range(months):
		key = cursor.strftime("%Y-%m")
		out.append({"month": key, "label": MONTH_ABBR_FR[cursor.month], "amount": by_month.get(key, 0.0)})
		cursor = getdate(add_months(cursor, 1))
	return out


@frappe.whitelist()
def record_payment(invoice, amount=None, mode_of_payment="Espèces", reference_no=None):
	require_any_role("Accountant")

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	inv = frappe.get_doc("Sales Invoice", invoice)
	frappe.has_permission(inv.doctype, "read", inv, throw=True)
	if inv.docstatus != 1:
		frappe.throw(frappe._("Cette facture n'est pas encore validée."))
	outstanding = flt(inv.outstanding_amount)
	if outstanding <= 0:
		frappe.throw(frappe._("Cette facture ne présente aucun solde impayé."))

	amount = flt(amount) or outstanding
	if amount > outstanding:
		frappe.throw(frappe._("Le montant dépasse le solde impayé."))

	# Payment Entry.validate() re-derives outstanding invoices for the
	# invoice's Customer (erpnext get_outstanding_reference_documents),
	# which runs its own `frappe.has_permission("Customer", "read", ...)`
	# check against the real session user - the Accountant role doesn't
	# carry Customer permission (it works through Student/Sales Invoice,
	# never the Customer doctype directly - docs/architecture.md section M),
	# and `doc.insert()` alone doesn't cover ad hoc internal permission
	# checks like this one. Same gap, same fix as teacher_api.py's
	# mark_attendance/save_assessment_results - see permissions.elevated().
	with elevated():
		pe = get_payment_entry("Sales Invoice", invoice, party_amount=amount)
		pe.mode_of_payment = mode_of_payment
		pe.reference_no = reference_no or f"Paiement manuel {frappe.utils.now_datetime():%Y-%m-%d %H:%M}"
		pe.reference_date = nowdate()
		for ref in pe.references:
			ref.allocated_amount = amount
		pe.insert()
		pe.submit()
	return {"payment_entry": pe.name, "outstanding_amount": frappe.db.get_value("Sales Invoice", invoice, "outstanding_amount")}


@frappe.whitelist()
def retry_mobile_money_verification(transaction):
	require_any_role("Accountant")

	from burkina_education.finance.mobile_money.api import _create_payment_entry
	from burkina_education.finance.mobile_money.gateway import get_adapter

	txn = frappe.get_doc("Mobile Money Transaction", transaction)
	if txn.status == "Success":
		return {"status": "Success", "payment_entry": txn.payment_entry}
	if txn.status not in ("Initiated", "Pending", "Failed"):
		frappe.throw(frappe._("Cette transaction n'est plus vérifiable ({0}).").format(txn.status))

	provider_doc = frappe.get_doc("Mobile Money Provider", txn.provider)
	verified = get_adapter(provider_doc).verify(txn)

	if verified.get("status") == "Success":
		payment_entry = _create_payment_entry(txn, provider_doc)
		txn.db_set("status", "Success")
		txn.db_set("payment_entry", payment_entry)
		txn.db_set("verified_on", frappe.utils.now_datetime())
		return {"status": "Success", "payment_entry": payment_entry}

	txn.db_set("status", "Failed")
	txn.db_set("failure_reason", verified.get("message") or "Vérification échouée auprès du fournisseur")
	return {"status": "Failed"}
