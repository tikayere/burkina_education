# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class ClinicVisit(Document):
	"""One school-clinic visit for one student (master.md §38). Health data
	is highly restricted - granted only to School Director/Clinic Staff (see
	the doctype's own permissions and docs/architecture.md section K), not
	Instructor/Class Teacher, even though those roles can see the same
	student's Disciplinary Case records.
	"""

	def before_insert(self):
		if not self.attended_by:
			self.attended_by = frappe.session.user

	def validate(self):
		if self.parent_notified and not self.parent_notified_on:
			self.parent_notified_on = nowdate()

		if self.referral and self.referral != "Aucun" and not self.referral_details:
			frappe.throw(frappe._("Veuillez préciser les détails de l'orientation."))
