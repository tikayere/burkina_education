# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LibraryBookCopy(Document):
	def on_update(self):
		self._recompute_book_counts()

	def on_trash(self):
		self._recompute_book_counts()

	def _recompute_book_counts(self):
		book = frappe.get_doc("Library Book", self.book)
		book.recompute_copy_counts()
		book.db_update()
