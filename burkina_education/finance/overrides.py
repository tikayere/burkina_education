# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Targeted ``override_doctype_class`` fixes for genuine Education/Frappe
version incompatibilities (docs/architecture.md section A: Education's
``develop`` branch has no version-15-tracking release). Each override
subclasses the real controller and replaces only the broken method - never a
full rewrite, and never editing Education's source directly (master.md's
"never modify upstream source files").
"""

import frappe
from education.education.doctype.fee_schedule.fee_schedule import FeeSchedule as EducationFeeSchedule


class FeeSchedule(EducationFeeSchedule):
	def validate_total_against_fee_strucuture(self):
		# Education's own implementation calls
		# ``frappe.db.get_all(..., fields=[{"SUM": "total_amount", "as": "total"}])``
		# - a dict-based aggregate ``fields`` entry that this Frappe version's
		# query builder doesn't support (``db_query.sanitize_fields`` assumes
		# every field is a string and crashes with
		# ``AttributeError: 'dict' object has no attribute 'lower'``), which
		# made *every* Fee Schedule save fail. Same result, plain SQL instead.
		fee_schedules_total = (
			frappe.db.sql(
				"select sum(total_amount) from `tabFee Schedule` where fee_structure=%s",
				self.fee_structure,
			)[0][0]
			or 0
		)
		fee_structure_total = frappe.db.get_value("Fee Structure", self.fee_structure, "total_amount") or 0

		if fee_schedules_total > fee_structure_total:
			frappe.msgprint(
				frappe._("Total amount of Fee Schedules exceeds the Total Amount of Fee Structure"),
				alert=True,
			)
