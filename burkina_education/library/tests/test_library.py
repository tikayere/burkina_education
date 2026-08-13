# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from burkina_education.library.tests.fixtures import LibraryFixture


class TestLibrary(IntegrationTestCase):
	def setUp(self):
		self.fixture = LibraryFixture()

	def _borrow(self, copy=None):
		return frappe.get_doc(
			{
				"doctype": "Library Transaction",
				"membership": self.fixture.membership.name,
				"book_copy": (copy or self.fixture.copy_1).name,
			}
		).insert(ignore_permissions=True)

	def test_borrow_sets_copy_unavailable_and_due_date(self):
		loan = self._borrow()
		self.assertEqual(loan.status, "Emprunté")
		self.assertIsNotNone(loan.due_date)
		self.assertEqual(frappe.db.get_value("Library Book Copy", self.fixture.copy_1.name, "status"), "Emprunté")

		book = frappe.get_doc("Library Book", self.fixture.book.name)
		self.assertEqual(book.total_copies, 2)
		self.assertEqual(book.available_copies, 1)

	def test_cannot_borrow_unavailable_copy(self):
		self._borrow()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Library Transaction",
					"membership": self.fixture.membership.name,
					"book_copy": self.fixture.copy_1.name,
				}
			).insert(ignore_permissions=True)

	def test_cannot_exceed_max_books(self):
		# fixture's membership has max_books=1
		self._borrow(self.fixture.copy_1)
		with self.assertRaises(frappe.ValidationError):
			self._borrow(self.fixture.copy_2)

	def test_return_on_time_has_no_fine(self):
		loan = self._borrow()
		loan.return_date = nowdate()
		loan.save()
		self.assertEqual(loan.status, "Retourné")
		self.assertEqual(loan.fine_amount, 0)
		self.assertEqual(frappe.db.get_value("Library Book Copy", self.fixture.copy_1.name, "status"), "Disponible")

		book = frappe.get_doc("Library Book", self.fixture.book.name)
		self.assertEqual(book.available_copies, 2)

	def test_late_return_computes_fine(self):
		fine_per_day = frappe.db.get_single_value("Burkina Education Settings", "library_fine_per_day") or 25
		loan = self._borrow()
		loan.db_set("due_date", add_days(nowdate(), -3))
		loan.reload()
		loan.return_date = nowdate()
		loan.save()
		self.assertEqual(loan.status, "Retourné")
		self.assertEqual(loan.fine_amount, 3 * fine_per_day)

	def test_overdue_job_flips_status_and_notifies_once(self):
		from burkina_education.library.notifications import run_overdue_notices

		loan = self._borrow()
		loan.db_set("due_date", add_days(nowdate(), -1))

		run_overdue_notices()
		loan.reload()
		self.assertEqual(loan.status, "En retard")

		# Second run must not re-match (status is no longer 'Emprunté') -
		# i.e. no duplicate notification for the same overdue loan.
		before = frappe.db.count("Message Log", {"reference_name": loan.name})
		run_overdue_notices()
		after = frappe.db.count("Message Log", {"reference_name": loan.name})
		self.assertEqual(before, after)
