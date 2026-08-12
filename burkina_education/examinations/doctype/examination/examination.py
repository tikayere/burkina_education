# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Examination(Document):
	"""A named examination session (e.g. "Composition du 1er trimestre") that
	groups one ``Examination Schedule`` row per Grade/Course sitting (master.md
	§21). Marks for each sitting are entered through the same Assessment
	Plan/Result engine as ordinary coursework - see Examination Schedule.
	"""

	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw(_("From Date cannot be after To Date."))
