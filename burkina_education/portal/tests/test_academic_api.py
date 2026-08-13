# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Academic Portal API tests (portal/roles/academic_api.py) -
docs/architecture.md section M. The one thing worth testing here is that
the dashboard's shape actually tracks which of the three roles (Registrar /
Examination Coordinator / Academic Director) the caller holds - a Registrar
must never see the ``director`` section, and vice versa."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import academic_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestAcademicApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()

	def _as(self, user, fn, *args, **kwargs):
		frappe.set_user(user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_requires_one_of_the_three_roles(self):
		other = self.fx.staff_user("Librarian", "not-academic")
		frappe.set_user(other.name)
		try:
			self.assertRaises(frappe.PermissionError, academic_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_registrar_sees_structure_only(self):
		user = self.fx.staff_user("Registrar")
		data = self._as(user, academic_api.get_dashboard)
		self.assertIn("structure", data)
		self.assertNotIn("exams", data)
		self.assertNotIn("director", data)

	def test_examination_coordinator_sees_exams_only(self):
		user = self.fx.staff_user("Examination Coordinator")
		data = self._as(user, academic_api.get_dashboard)
		self.assertIn("exams", data)
		self.assertNotIn("structure", data)
		self.assertNotIn("director", data)

	def test_academic_director_sees_everything(self):
		user = self.fx.staff_user("Academic Director")
		data = self._as(user, academic_api.get_dashboard)
		self.assertIn("structure", data)
		self.assertIn("exams", data)
		self.assertIn("director", data)
