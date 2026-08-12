# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Cycle(Document):
	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Cycle",
			{
				"education_level": self.education_level,
				"cycle_name": self.cycle_name,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				_("Cycle {0} already exists for this Education Level").format(frappe.bold(self.cycle_name))
			)
