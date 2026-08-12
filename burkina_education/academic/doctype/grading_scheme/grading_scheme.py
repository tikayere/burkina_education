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

		duplicate = frappe.db.exists(
			"Grading Scheme",
			{
				"education_level": self.education_level,
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
