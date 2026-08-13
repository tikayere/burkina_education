# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Boarding Manager Portal API tests (portal/roles/boarding_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import boarding_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestBoardingApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("Boarding Manager")

		self.building = frappe.get_doc(
			{"doctype": "Boarding Building", "building_name": f"Pavillon {self.fx.tag}"}
		).insert(ignore_permissions=True)
		self.room = frappe.get_doc(
			{"doctype": "Boarding Room", "building": self.building.name, "room_number": "101", "capacity": 2}
		).insert(ignore_permissions=True)
		self.bed = frappe.get_doc(
			{"doctype": "Boarding Bed", "room": self.room.name, "bed_number": "A", "status": "Disponible"}
		).insert(ignore_permissions=True)

	def _as_manager(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_counts(self):
		# >= rather than == - the dev site's demo data also contributes
		# Boarding Beds/assignments (see test_librarian_api.py).
		data = self._as_manager(boarding_api.get_dashboard)
		self.assertGreaterEqual(data["beds"], 1)
		self.assertGreaterEqual(data["available"], 1)

	def test_get_available_beds_lists_free_bed(self):
		beds = self._as_manager(boarding_api.get_available_beds)
		self.assertIn(self.bed.name, [b["name"] for b in beds])

	def test_assign_bed_occupies_it(self):
		before = self._as_manager(boarding_api.get_dashboard)["active_assignments"]

		self._as_manager(boarding_api.assign_bed, student=self.fx.students[0].name, bed=self.bed.name)
		self.assertEqual(frappe.db.get_value("Boarding Bed", self.bed.name, "status"), "Occupé")

		beds = self._as_manager(boarding_api.get_available_beds)
		self.assertNotIn(self.bed.name, [b["name"] for b in beds])

		after = self._as_manager(boarding_api.get_dashboard)["active_assignments"]
		self.assertEqual(after, before + 1)

	def test_assign_bed_rejects_occupied_bed(self):
		self._as_manager(boarding_api.assign_bed, student=self.fx.students[0].name, bed=self.bed.name)
		other_student = self.fx.students[1] if len(self.fx.students) > 1 else self.fx.students[0]
		self.assertRaises(
			frappe.ValidationError,
			self._as_manager,
			boarding_api.assign_bed,
			student=other_student.name,
			bed=self.bed.name,
		)
