# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LibraryBook(Document):
	def before_save(self):
		self.recompute_copy_counts()

	def recompute_copy_counts(self):
		"""``total_copies``/``available_copies`` are derived from the actual
		``Library Book Copy`` rows, never edited directly - kept in sync here
		(called on every save) and by ``Library Book Copy`` itself whenever a
		copy is added/removed/its status changes (see that doctype's
		``on_update``/``on_trash``)."""
		if not self.name:
			return

		self.total_copies = frappe.db.count("Library Book Copy", {"book": self.name})
		self.available_copies = frappe.db.count(
			"Library Book Copy", {"book": self.name, "status": "Disponible"}
		)
