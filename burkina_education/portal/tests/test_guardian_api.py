# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Guardian Portal API tests (portal/guardian_api.py) - docs/architecture.md
section L. Ownership scoping is the load-bearing property here: every
``get_child_*`` function must refuse a student that isn't actually one of
the caller's own children (master.md §54/§77), and Clinic Visit access must
stay Guardian-only (never reachable from student_api.py, see
test_student_api.py::test_no_clinic_endpoint_on_student_api)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal import guardian_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestGuardianApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.link_guardian_to_user()
		self.own_student = self.fx.students[0]
		self.other_student = self.fx.students[1]

	def _as_guardian(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_lists_only_own_children(self):
		data = self._as_guardian(guardian_api.get_dashboard)
		names = {c["name"] for c in data["children"]}
		self.assertIn(self.own_student.name, names)
		self.assertNotIn(self.other_student.name, names)

	def test_get_child_rejects_unrelated_student(self):
		frappe.set_user(self.user.name)
		try:
			self.assertRaises(frappe.PermissionError, guardian_api.get_child, self.other_student.name)
		finally:
			frappe.set_user("Administrator")

	def test_get_child_clinic_rejects_unrelated_student(self):
		frappe.set_user(self.user.name)
		try:
			self.assertRaises(frappe.PermissionError, guardian_api.get_child_clinic, self.other_student.name)
		finally:
			frappe.set_user("Administrator")

	def test_get_child_clinic_returns_own_childs_visits(self):
		visit = frappe.get_doc(
			{
				"doctype": "Clinic Visit",
				"student": self.own_student.name,
				"date": frappe.utils.now_datetime(),
				"complaint": "Mal de tête",
				"status": "Ouvert",
			}
		).insert(ignore_permissions=True)

		visits = self._as_guardian(guardian_api.get_child_clinic, self.own_student.name)
		self.assertIn(visit.name, {v.name for v in visits})

	def test_pay_child_invoice_rejects_invoice_not_belonging_to_child(self):
		# A guardian who owns student A must not be able to pay an invoice
		# that belongs to student B, even by just guessing/reusing an
		# invoice name - the ownership check runs before the invoice is
		# even looked at via has_permission.
		frappe.set_user(self.user.name)
		try:
			self.assertRaises(
				frappe.PermissionError,
				guardian_api.pay_child_invoice,
				student=self.other_student.name,
				invoice="SOME-INVOICE-THAT-NEED-NOT-EXIST",
				provider="whatever",
				phone_number="+22670000000",
			)
		finally:
			frappe.set_user("Administrator")

	def test_get_mobile_money_providers_is_secret_free(self):
		mode_of_payment = frappe.db.get_value("Mode of Payment", {}, "name") or frappe.get_doc(
			{"doctype": "Mode of Payment", "mode_of_payment": f"Mobile Money {self.fx.tag}"}
		).insert(ignore_permissions=True).name

		provider = frappe.get_doc(
			{
				"doctype": "Mobile Money Provider",
				"provider_name": f"Orange Money {self.fx.tag}",
				"provider_code": "Orange Money",
				"mode_of_payment": mode_of_payment,
				"is_active": 1,
				"sandbox_mode": 1,
				"currency": "XOF",
			}
		).insert(ignore_permissions=True)

		rows = self._as_guardian(guardian_api.get_mobile_money_providers)
		names = {r["name"] for r in rows}
		self.assertIn(provider.name, names)
		for row in rows:
			self.assertNotIn("api_secret", row)
			self.assertNotIn("api_key", row)
