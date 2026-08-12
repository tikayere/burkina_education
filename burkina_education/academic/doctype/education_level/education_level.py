# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EducationLevel(Document):
	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Education Level",
			{
				"school": self.school,
				"education_level_name": self.education_level_name,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				_("Education Level {0} already exists for this school").format(
					frappe.bold(self.education_level_name)
				)
			)
