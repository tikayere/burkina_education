# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Portal API + permission-boundary tests (master.md §29/§30/§54/§77:
"a guardian only sees students they are authorized to access" / "student
cannot access another student's information")."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.messaging import portal
from burkina_education.messaging.tests.fixtures import CommunicationFixture


class TestPortal(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()

	def test_guardian_dashboard_scoped_to_own_children(self):
		self.fx.link_guardian_to_user()

		frappe.set_user(self.fx.guardian.user)
		try:
			data = portal.guardian_dashboard()
		finally:
			frappe.set_user("Administrator")

		names = {c["name"] for c in data["children"]}
		self.assertIn(self.fx.students[0].name, names)
		self.assertNotIn(self.fx.students[1].name, names)

	def test_guardian_cannot_view_unrelated_student(self):
		self.fx.link_guardian_to_user()

		frappe.set_user(self.fx.guardian.user)
		try:
			self.assertRaises(frappe.PermissionError, portal.guardian_student_detail, self.fx.students[1].name)
		finally:
			frappe.set_user("Administrator")

	def test_student_dashboard_requires_linked_user(self):
		user = self.fx.link_student_to_user(self.fx.students[0])

		frappe.set_user(user.name)
		try:
			data = portal.student_dashboard()
		finally:
			frappe.set_user("Administrator")

		self.assertEqual(data["student"]["student_name"], self.fx.students[0].student_name)

	def test_user_with_no_guardian_record_is_rejected(self):
		from burkina_education.academic.tests.fixtures import get_or_create_user

		stray_user = get_or_create_user(f"stray.{self.fx.tag}@test-fixture.bf", ["Guardian"])
		frappe.set_user(stray_user.name)
		try:
			self.assertRaises(frappe.PermissionError, portal.guardian_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_invite_guardian_links_user_and_role(self):
		user_name = portal.invite_guardian(self.fx.guardian.name)
		self.fx.guardian.reload()
		self.assertEqual(self.fx.guardian.user, user_name)
		user = frappe.get_doc("User", user_name)
		self.assertIn("Guardian", [r.role for r in user.roles])

	def test_invite_student_links_user_and_role(self):
		student = self.fx.students[0]
		user_name = portal.invite_student(student.name)
		self.assertEqual(frappe.db.get_value("Student", student.name, "user"), user_name)
		user = frappe.get_doc("User", user_name)
		self.assertIn("Student", [r.role for r in user.roles])
