# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Permission-boundary regression tests (master.md §64: "teacher cannot
access accounting" / "accountant cannot modify grades")."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic.tests.fixtures import get_or_create_user
from burkina_education.finance.tests.fixtures import FinanceFixture


class TestFinancePermissions(FrappeTestCase):
	def setUp(self):
		self.fixture = FinanceFixture()
		self.invoice = self.fixture.create_invoice(self.fixture.students[0], submit=False)

		self.accountant = get_or_create_user(f"accountant.{self.fixture.tag}@test-fixture.bf", ["Accountant"])
		# A real teacher is provisioned with both roles: "Instructor" is the
		# identity/profile role, while Education's Assessment Result write
		# permission is actually granted to "Academics User" (see
		# assessment_result.json) - not to "Instructor" itself.
		self.instructor = get_or_create_user(
			f"instructor.{self.fixture.tag}@test-fixture.bf", ["Instructor", "Academics User"]
		)

	def test_accountant_cannot_access_assessment_result(self):
		self.assertFalse(
			frappe.has_permission("Assessment Result", "write", user=self.accountant.name)
		)
		self.assertFalse(
			frappe.has_permission("Assessment Result", "read", user=self.accountant.name)
		)

	def test_accountant_can_access_sales_invoice_and_payment_entry(self):
		self.assertTrue(frappe.has_permission("Sales Invoice", "write", user=self.accountant.name))
		self.assertTrue(frappe.has_permission("Payment Entry", "write", user=self.accountant.name))
		self.assertTrue(frappe.has_permission("Scholarship", "write", user=self.accountant.name))

	def test_instructor_cannot_access_sales_invoice_or_payment_entry(self):
		self.assertFalse(frappe.has_permission("Sales Invoice", "write", user=self.instructor.name))
		self.assertFalse(frappe.has_permission("Payment Entry", "write", user=self.instructor.name))
		self.assertFalse(frappe.has_permission("Mobile Money Transaction", "read", user=self.instructor.name))

	def test_instructor_can_still_access_assessment_result(self):
		# Positive control: the finance permission grants above must not have
		# narrowed Instructor's existing (Phase 2) academic access.
		self.assertTrue(frappe.has_permission("Assessment Result", "write", user=self.instructor.name))
