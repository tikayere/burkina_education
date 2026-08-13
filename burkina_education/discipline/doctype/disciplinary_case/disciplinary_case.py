# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class DisciplinaryCase(Document):
	"""One disciplinary incident for one student (master.md §37). Access is
	restricted to school administration (School Director/Academic Director/
	Class Teacher) - see docs/architecture.md section K; not granted to
	Instructor, Accountant, Guardian or Student.
	"""

	def before_insert(self):
		if not self.reported_by:
			self.reported_by = frappe.session.user

	def validate(self):
		if self.parent_contacted and not self.parent_contacted_on:
			self.parent_contacted_on = nowdate()

		if self.status == "Résolu" and not self.resolved_on:
			self.resolved_on = nowdate()
		elif self.status != "Résolu":
			self.resolved_on = None
