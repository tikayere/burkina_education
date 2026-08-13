# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from burkina_education.school.tests.fixtures import MinimalSchoolFixture


class TestTransport(IntegrationTestCase):
	def setUp(self):
		self.fixture = MinimalSchoolFixture()
		self.route = frappe.get_doc(
			{
				"doctype": "Transport Route",
				"route_name": f"Route {self.fixture.tag}",
				"stops": [{"stop_name": "Marché Central"}, {"stop_name": "Rond-Point"}],
			}
		).insert(ignore_permissions=True)

	def test_stop_sequence_autofills(self):
		self.assertEqual(self.route.stops[0].sequence, 1)
		self.assertEqual(self.route.stops[1].sequence, 2)

	def test_assignment_requires_stop_on_route(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Student Transport Assignment",
					"student": self.fixture.student.name,
					"route": self.route.name,
					"stop_name": "Arrêt Inexistant",
				}
			).insert(ignore_permissions=True)

	def test_assignment_with_valid_stop_succeeds(self):
		assignment = frappe.get_doc(
			{
				"doctype": "Student Transport Assignment",
				"student": self.fixture.student.name,
				"route": self.route.name,
				"stop_name": "Marché Central",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(assignment.status, "Actif")

	def test_only_one_active_assignment_per_student(self):
		frappe.get_doc(
			{
				"doctype": "Student Transport Assignment",
				"student": self.fixture.student.name,
				"route": self.route.name,
				"stop_name": "Marché Central",
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Student Transport Assignment",
					"student": self.fixture.student.name,
					"route": self.route.name,
					"stop_name": "Rond-Point",
				}
			).insert(ignore_permissions=True)
