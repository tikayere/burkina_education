# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GradingScheme(Document):
	"""Configurable grading rules (master.md §19: "do NOT hard-code formulas").

	One scheme can be scoped to an Education Level, or left blank to apply
	everywhere. ``academic.grading.resolve_grading_scheme`` picks the right
	one for a given student at compute time.
	"""

	def validate(self):
		self.validate_single_default()

	def validate_single_default(self):
		if not (self.is_default and self.is_active):
			return

		# An unset Link field is stored as NULL, not "" - a plain equality
		# filter with None silently becomes `= ''` (which matches nothing),
		# so a blank (global) scope needs the explicit "is not set" operator.
		education_level_filter = self.education_level or ["is", "not set"]

		duplicate = frappe.db.exists(
			"Grading Scheme",
			{
				"education_level": education_level_filter,
				"is_default": 1,
				"is_active": 1,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			scope = self.education_level or _("all education levels")
			frappe.throw(
				_("{0} is already the default active Grading Scheme for {1}.").format(
					frappe.bold(duplicate), scope
				)
			)
