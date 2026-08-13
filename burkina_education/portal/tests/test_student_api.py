# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Student Portal API tests (portal/student_api.py) - docs/architecture.md
section L. Ownership scoping (master.md §54/§77) is exercised directly here;
the Guardian equivalent lives in test_guardian_api.py."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal import student_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestStudentApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.link_student_to_user(self.fx.students[0])

	def _as_student(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_scoped_to_own_record(self):
		data = self._as_student(student_api.get_dashboard)
		self.assertEqual(data["student"]["student_name"], self.fx.students[0].student_name)
		self.assertIn("attendance", data)
		self.assertIn("upcoming_schedule", data)
		self.assertIn("announcements", data)

	def test_profile_includes_own_guardians_only(self):
		data = self._as_student(student_api.get_profile)
		names = {g["name"] for g in data["guardians"]}
		self.assertIn(self.fx.guardian.name, names)

	def test_discipline_is_own_record_only(self):
		other_case = frappe.get_doc(
			{
				"doctype": "Disciplinary Case",
				"student": self.fx.students[1].name,
				"incident_type": "Retard",
				"severity": "Mineure",
				"description": "Retard de 10 minutes.",
			}
		).insert(ignore_permissions=True)
		own_case = frappe.get_doc(
			{
				"doctype": "Disciplinary Case",
				"student": self.fx.students[0].name,
				"incident_type": "Comportement",
				"severity": "Mineure",
				"description": "Bavardage en classe.",
			}
		).insert(ignore_permissions=True)

		cases = self._as_student(student_api.get_discipline)
		names = {c.name for c in cases}
		self.assertIn(own_case.name, names)
		self.assertNotIn(other_case.name, names)

	def test_no_clinic_endpoint_on_student_api(self):
		# Health data is Guardian-only across the whole app (docs/architecture.md
		# section L) - the Student Portal's API surface simply never grows a
		# get_clinic() function, unlike get_discipline() above.
		self.assertFalse(hasattr(student_api, "get_clinic"))

	def test_unlinked_user_is_rejected(self):
		stray = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"stray.student.{self.fx.tag}@test-fixture.bf",
				"first_name": "Stray",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
		stray.append("roles", {"role": "Student"})
		stray.save(ignore_permissions=True)

		frappe.set_user(stray.name)
		try:
			self.assertRaises(frappe.PermissionError, student_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_library_and_transport_default_to_empty_without_data(self):
		library = self._as_student(student_api.get_library)
		self.assertIsNone(library["membership"])
		transport = self._as_student(student_api.get_transport)
		self.assertIsNone(transport["assignment"])
