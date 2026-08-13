# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Transport Manager Portal API tests (portal/roles/transport_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import transport_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestTransportApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("Transport Manager")
		self.route = frappe.get_doc(
			{
				"doctype": "Transport Route",
				"route_name": f"Route {self.fx.tag}",
				"distance_km": 8.5,
				"stops": [{"stop_name": "Arrêt A"}, {"stop_name": "Arrêt B"}],
			}
		).insert(ignore_permissions=True)
		self.assignment = frappe.get_doc(
			{
				"doctype": "Student Transport Assignment",
				"student": self.fx.students[0].name,
				"academic_year": self.fx.academic_year.name,
				"route": self.route.name,
				"stop_name": "Arrêt A",
				"status": "Actif",
				"start_date": frappe.utils.nowdate(),
			}
		).insert(ignore_permissions=True)

	def _as_manager(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_requires_role(self):
		frappe.set_user("Guest")
		try:
			self.assertRaises(frappe.PermissionError, transport_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_counts_route_occupancy(self):
		# Scoped to this fixture's own route (by name) rather than site-wide
		# totals, which the dev site's demo data also contributes to.
		data = self._as_manager(transport_api.get_dashboard)
		self.assertGreaterEqual(data["active_assignments"], 1)
		route = next(r for r in data["routes"] if r["name"] == self.route.name)
		self.assertEqual(route["student_count"], 1)
		self.assertEqual(route["stop_count"], 2)

	def test_get_route_students(self):
		rows = self._as_manager(transport_api.get_route_students, route=self.route.name)
		self.assertEqual([r.student for r in rows], [self.fx.students[0].name])
