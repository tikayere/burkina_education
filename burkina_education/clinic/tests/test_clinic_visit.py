# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from burkina_education.school.tests.fixtures import MinimalSchoolFixture


class TestClinicVisit(IntegrationTestCase):
	def setUp(self):
		self.fixture = MinimalSchoolFixture()

	def test_attended_by_defaults_to_current_user(self):
		visit = frappe.get_doc(
			{
				"doctype": "Clinic Visit",
				"student": self.fixture.student.name,
				"complaint": "Maux de tête",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(visit.attended_by, frappe.session.user)
		self.assertEqual(visit.status, "Ouvert")

	def test_referral_requires_details(self):
		visit = frappe.get_doc(
			{
				"doctype": "Clinic Visit",
				"student": self.fixture.student.name,
				"complaint": "Fièvre",
				"referral": "Hôpital",
			}
		)
		self.assertRaises(frappe.ValidationError, visit.insert, ignore_permissions=True)

		visit.referral_details = "Orienté vers le CHU pour examens complémentaires."
		visit.insert(ignore_permissions=True)
		self.assertEqual(visit.referral, "Hôpital")

	def test_parent_notified_on_defaults_when_checked(self):
		visit = frappe.get_doc(
			{
				"doctype": "Clinic Visit",
				"student": self.fixture.student.name,
				"complaint": "Chute dans la cour",
				"parent_notified": 1,
			}
		).insert(ignore_permissions=True)
		self.assertIsNotNone(visit.parent_notified_on)

	def test_health_data_not_exposed_to_teaching_roles(self):
		# master.md §38: "Do not expose medical information to teachers unless
		# explicitly authorized" - only System Manager/School Director/Clinic
		# Staff are granted, deliberately excluding Instructor/Class Teacher
		# (unlike Disciplinary Case, which does grant Class Teacher).
		granted_roles = {p.role for p in frappe.get_meta("Clinic Visit").permissions}
		self.assertEqual(granted_roles, {"System Manager", "School Director", "Clinic Staff"})
