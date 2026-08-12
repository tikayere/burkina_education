# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class Scholarship(Document):
	"""A per-student fee exemption (master.md §26: partial/full scholarships).

	Applied automatically to future Sales Invoices generated from a Fee
	Schedule for this student/academic year — see ``finance.discounts``.
	"""

	def validate(self):
		self.validate_percent()
		self.set_approval_fields()

	def validate_percent(self):
		if self.scholarship_type == "Bourse Totale":
			self.discount_percent = 100
		if not (0 < (self.discount_percent or 0) <= 100):
			frappe.throw(_("Le pourcentage de réduction doit être compris entre 0 et 100."))

	def set_approval_fields(self):
		if self.status == "Approuvée" and not self.approved_by:
			self.approved_by = frappe.session.user
			self.approval_date = today()
		if self.status != "Approuvée":
			self.approved_by = None
			self.approval_date = None
