# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, nowdate

OPEN_STATUSES = ("Emprunté", "En retard")


class LibraryTransaction(Document):
	"""One borrow/return of one Library Book Copy by one Library Membership
	(master.md §39: "borrowing, returns, due dates, penalties"). The book
	copy's own ``status`` (docs/architecture.md section K) is kept in sync
	here rather than edited directly on Library Book Copy.
	"""

	def validate(self):
		if self.is_new():
			self._validate_can_borrow()
			if not self.due_date:
				self.due_date = self._compute_due_date()

		if self.return_date and self.status not in ("Retourné", "Perdu"):
			self.status = "Retourné"

		if self.status == "Retourné" and self.return_date:
			self.fine_amount = self._compute_fine()
		elif self.status == "Emprunté":
			self.fine_amount = 0

	def on_update(self):
		self._sync_copy_status()

	def _validate_can_borrow(self):
		copy_status = frappe.db.get_value("Library Book Copy", self.book_copy, "status")
		if copy_status != "Disponible":
			frappe.throw(frappe._("Cet exemplaire n'est pas disponible ({0}).").format(copy_status))

		membership_status = frappe.db.get_value("Library Membership", self.membership, "status")
		if membership_status != "Active":
			frappe.throw(frappe._("Cette adhésion n'est pas active ({0}).").format(membership_status))

		max_books = frappe.db.get_value("Library Membership", self.membership, "max_books") or 0
		outstanding = frappe.db.count(
			"Library Transaction", {"membership": self.membership, "status": ["in", OPEN_STATUSES]}
		)
		if outstanding >= max_books:
			frappe.throw(
				frappe._("Cet élève a déjà atteint la limite de {0} livre(s) emprunté(s) simultanément.").format(
					max_books
				)
			)

	def _compute_due_date(self):
		loan_period = frappe.db.get_single_value("Burkina Education Settings", "library_loan_period_days") or 14
		return add_days(self.issue_date or nowdate(), loan_period)

	def _compute_fine(self):
		if not self.due_date or not self.return_date:
			return 0
		days_late = date_diff(getdate(self.return_date), getdate(self.due_date))
		if days_late <= 0:
			return 0
		per_day = frappe.db.get_single_value("Burkina Education Settings", "library_fine_per_day") or 0
		return days_late * per_day

	def _sync_copy_status(self):
		if self.status == "Perdu":
			new_status = "Perdu"
		elif self.status == "Retourné":
			new_status = "Disponible"
		else:
			new_status = "Emprunté"

		if frappe.db.get_value("Library Book Copy", self.book_copy, "status") == new_status:
			return

		frappe.db.set_value("Library Book Copy", self.book_copy, "status", new_status)
		# db_set above skips controller hooks - Library Book's total/available
		# counts need the explicit refresh Library Book Copy.on_update() would
		# otherwise have done.
		book_name = frappe.db.get_value("Library Book Copy", self.book_copy, "book")
		book = frappe.get_doc("Library Book", book_name)
		book.recompute_copy_counts()
		book.db_update()
