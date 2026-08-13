# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from burkina_education.school.tests.fixtures import MinimalSchoolFixture


class TestBoarding(IntegrationTestCase):
	def setUp(self):
		self.fixture = MinimalSchoolFixture(student_count=2)
		self.building = frappe.get_doc(
			{"doctype": "Boarding Building", "building_name": f"Bâtiment {self.fixture.tag}"}
		).insert(ignore_permissions=True)
		self.room = frappe.get_doc(
			{
				"doctype": "Boarding Room",
				"building": self.building.name,
				"room_number": "101",
				"capacity": 1,
			}
		).insert(ignore_permissions=True)
		self.bed = frappe.get_doc(
			{"doctype": "Boarding Bed", "room": self.room.name, "bed_number": "A"}
		).insert(ignore_permissions=True)

	def test_bed_creation_respects_room_capacity(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{"doctype": "Boarding Bed", "room": self.room.name, "bed_number": "B"}
			).insert(ignore_permissions=True)

	def test_check_in_occupies_bed(self):
		assignment = frappe.get_doc(
			{
				"doctype": "Student Boarding Assignment",
				"student": self.fixture.students[0].name,
				"bed": self.bed.name,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(assignment.status, "Actif")
		self.assertEqual(frappe.db.get_value("Boarding Bed", self.bed.name, "status"), "Occupé")

	def test_cannot_assign_occupied_bed(self):
		frappe.get_doc(
			{
				"doctype": "Student Boarding Assignment",
				"student": self.fixture.students[0].name,
				"bed": self.bed.name,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Student Boarding Assignment",
					"student": self.fixture.students[1].name,
					"bed": self.bed.name,
				}
			).insert(ignore_permissions=True)

	def test_check_out_frees_bed(self):
		assignment = frappe.get_doc(
			{
				"doctype": "Student Boarding Assignment",
				"student": self.fixture.students[0].name,
				"bed": self.bed.name,
			}
		).insert(ignore_permissions=True)

		assignment.check_out()
		self.assertEqual(assignment.status, "Terminé")
		self.assertEqual(frappe.db.get_value("Boarding Bed", self.bed.name, "status"), "Disponible")
