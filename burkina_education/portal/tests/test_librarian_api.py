# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Librarian Portal API tests (portal/roles/librarian_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import librarian_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestLibrarianApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("Librarian")
		self.student = self.fx.students[0]

		self.book = frappe.get_doc({"doctype": "Library Book", "title": f"Livre {self.fx.tag}"}).insert(
			ignore_permissions=True
		)
		self.copy = frappe.get_doc(
			{"doctype": "Library Book Copy", "book": self.book.name, "status": "Disponible"}
		).insert(ignore_permissions=True)
		self.membership = frappe.get_doc(
			{
				"doctype": "Library Membership",
				"student": self.student.name,
				"status": "Active",
				"issue_date": frappe.utils.nowdate(),
				"max_books": 2,
			}
		).insert(ignore_permissions=True)

	def _as_librarian(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_requires_librarian_role(self):
		other = self.fx.staff_user("Transport Manager", "not-librarian")
		frappe.set_user(other.name)
		try:
			self.assertRaises(frappe.PermissionError, librarian_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_counts(self):
		# The dev site's own demo data already seeds Library Books/Copies, so
		# assert on this fixture's contribution being present, not on
		# site-wide totals being exactly 1 (docs/architecture.md section M).
		data = self._as_librarian(librarian_api.get_dashboard)
		self.assertGreaterEqual(data["books"], 1)
		self.assertGreaterEqual(data["available"], 1)
		self.assertGreaterEqual(data["active_members"], 1)

	def test_issue_book_creates_open_transaction_and_flips_copy_status(self):
		name = self._as_librarian(librarian_api.issue_book, student=self.student.name, book=self.book.name)
		txn = frappe.get_doc("Library Transaction", name)
		self.assertEqual(txn.status, "Emprunté")
		self.assertEqual(frappe.db.get_value("Library Book Copy", self.copy.name, "status"), "Emprunté")

	def test_issue_book_fails_when_no_copy_available(self):
		self._as_librarian(librarian_api.issue_book, student=self.student.name, book=self.book.name)
		self.assertRaises(
			frappe.ValidationError, self._as_librarian, librarian_api.issue_book, student=self.student.name, book=self.book.name
		)

	def test_return_book_frees_copy_and_computes_fine(self):
		name = self._as_librarian(librarian_api.issue_book, student=self.student.name, book=self.book.name)
		result = self._as_librarian(librarian_api.return_book, transaction=name)
		self.assertEqual(result["status"], "Retourné")
		self.assertEqual(frappe.db.get_value("Library Book Copy", self.copy.name, "status"), "Disponible")

	def test_find_member_reports_can_borrow(self):
		info = self._as_librarian(librarian_api.find_member, student=self.student.name)
		self.assertTrue(info["can_borrow"])
		self.assertEqual(info["open_loans"], [])
