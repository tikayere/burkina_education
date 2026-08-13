# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Leadership Portal API tests (portal/roles/leadership_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import leadership_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestLeadershipApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("School Director")
		self.case = frappe.get_doc(
			{
				"doctype": "Disciplinary Case",
				"student": self.fx.students[0].name,
				"incident_type": "Comportement",
				"severity": "Mineure",
				"date": frappe.utils.nowdate(),
				"description": "Bavardage en classe.",
				"status": "Ouvert",
			}
		).insert(ignore_permissions=True)

	def _as_director(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_requires_school_director_role(self):
		other = self.fx.staff_user("Librarian", "not-director")
		frappe.set_user(other.name)
		try:
			self.assertRaises(frappe.PermissionError, leadership_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_surfaces_open_discipline_case(self):
		data = self._as_director(leadership_api.get_dashboard)
		self.assertGreaterEqual(data["school"]["open_discipline_cases"], 1)
		self.assertIn(self.case.name, {c["name"] for c in data["recent_discipline"]})
