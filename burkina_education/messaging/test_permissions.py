# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Direct tests of the ``has_permission`` hook itself (messaging/
permissions.py) - the layer behind ``/printview`` and any other generic
``frappe.has_permission`` check, independent of the portal.py API tested in
test_portal.py (master.md §54: never rely on a single layer)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic.tests.fixtures import get_or_create_user
from burkina_education.messaging.tests.fixtures import CommunicationFixture


class TestPortalPermissions(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()
		self.owned_student = self.fx.students[0]
		self.other_student = self.fx.students[1]

		self.report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": self.owned_student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)

		self.other_report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": self.other_student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)

	def test_guardian_can_read_own_childs_report(self):
		user = self.fx.link_guardian_to_user()
		self.assertTrue(frappe.has_permission(self.report.doctype, "read", self.report, user=user.name))

	def test_guardian_cannot_read_unrelated_report(self):
		user = self.fx.link_guardian_to_user()
		self.assertFalse(frappe.has_permission(self.other_report.doctype, "read", self.other_report, user=user.name))

	def test_student_can_read_own_report_only(self):
		user = self.fx.link_student_to_user(self.owned_student)
		self.assertTrue(frappe.has_permission(self.report.doctype, "read", self.report, user=user.name))
		self.assertFalse(frappe.has_permission(self.other_report.doctype, "read", self.other_report, user=user.name))

	def test_staff_role_is_unaffected_by_the_hook(self):
		# A user with a real staff role (not just Guardian/Student) must keep
		# whatever access their own Custom DocPerm already grants - this
		# module never narrows that.
		staff = get_or_create_user(f"director.{self.fx.tag}@test-fixture.bf", ["Academic Director"])
		self.assertTrue(frappe.has_permission(self.other_report.doctype, "read", self.other_report, user=staff.name))
