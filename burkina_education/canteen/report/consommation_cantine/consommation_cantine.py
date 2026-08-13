# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Daily/monthly meal consumption reporting (master.md §41), grouped by date
and meal type - the two cuts a canteen manager actually needs (how many
meals were served on a given day, per meal type), filterable to a date range.
"""

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": _("Repas"), "fieldname": "meal_type", "fieldtype": "Data", "width": 150},
		{"label": _("Repas consommés"), "fieldname": "consumed_count", "fieldtype": "Int", "width": 150},
	]


def get_data(filters):
	conditions = ["consumed = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("date >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("date <= %(to_date)s")
		values["to_date"] = filters.to_date
	if filters.get("meal_type"):
		conditions.append("meal_type = %(meal_type)s")
		values["meal_type"] = filters.meal_type

	return frappe.db.sql(
		"""
		select date, meal_type, count(name) as consumed_count
		from `tabMeal Consumption`
		where {conditions}
		group by date, meal_type
		order by date desc, meal_type
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)
