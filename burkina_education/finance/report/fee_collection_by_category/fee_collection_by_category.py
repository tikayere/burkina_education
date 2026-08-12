# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Revenue by fee type (master.md §69 "revenue by fee type") — the one cut
Education's own ``Program Wise Fee Collection`` (revenue by class) and
ERPNext's ``Accounts Receivable`` (outstanding/overdue) don't provide; see
docs/architecture.md section H.

Reports on submitted Sales Invoices generated from a Fee Schedule only (never
an arbitrary ERPNext sale), grouped by Fee Category via the Item each Fee
Component is backed by.
"""

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data, None, chart


def get_columns():
	return [
		{
			"label": _("Catégorie de frais"),
			"fieldname": "fee_category",
			"fieldtype": "Link",
			"options": "Fee Category",
			"width": 250,
		},
		{
			"label": _("Montant facturé"),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"width": 200,
		},
		{
			"label": _("Nombre de factures"),
			"fieldname": "invoice_count",
			"fieldtype": "Int",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = ["si.docstatus = 1", "si.student is not null", "si.fee_schedule is not null"]
	values = {}

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters.to_date
	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		values["company"] = filters.company

	return frappe.db.sql(
		"""
		select
			fc.name as fee_category,
			sum(sii.base_net_amount) as invoiced_amount,
			count(distinct si.name) as invoice_count
		from `tabSales Invoice Item` sii
		inner join `tabSales Invoice` si on si.name = sii.parent
		inner join `tabFee Category` fc on fc.item = sii.item_code
		where {conditions}
		group by fc.name
		order by invoiced_amount desc
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)


def get_chart_data(data):
	if not data:
		return None
	return {
		"data": {
			"labels": [row.fee_category for row in data],
			"datasets": [{"name": _("Montant facturé"), "values": [row.invoiced_amount for row in data]}],
		},
		"type": "bar",
	}
