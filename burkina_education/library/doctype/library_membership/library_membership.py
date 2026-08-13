# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LibraryMembership(Document):
	def validate(self):
		if not self.max_books or self.max_books < 1:
			frappe.throw(frappe._("Le nombre maximal de livres simultanés doit être d'au moins 1."))
