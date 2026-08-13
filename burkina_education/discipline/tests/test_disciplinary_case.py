# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from burkina_education.school.tests.fixtures import MinimalSchoolFixture


class TestDisciplinaryCase(IntegrationTestCase):
	def setUp(self):
		self.fixture = MinimalSchoolFixture()

	def test_reported_by_defaults_to_current_user(self):
		case = frappe.get_doc(
			{
				"doctype": "Disciplinary Case",
				"student": self.fixture.student.name,
				"incident_type": "Retard",
				"severity": "Mineure",
				"description": "Arrivé 20 minutes en retard.",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(case.reported_by, frappe.session.user)
		self.assertEqual(case.status, "Ouvert")

	def test_resolved_on_tracks_status(self):
		case = frappe.get_doc(
			{
				"doctype": "Disciplinary Case",
				"student": self.fixture.student.name,
				"incident_type": "Comportement",
				"severity": "Modérée",
				"description": "Perturbation en classe.",
			}
		).insert(ignore_permissions=True)
		self.assertIsNone(case.resolved_on)

		case.status = "Résolu"
		case.resolution = "Entretien avec le censeur, avertissement."
		case.save()
		self.assertIsNotNone(case.resolved_on)

		case.status = "En cours"
		case.save()
		self.assertIsNone(case.resolved_on)

	def test_parent_contacted_on_defaults_when_checked(self):
		case = frappe.get_doc(
			{
				"doctype": "Disciplinary Case",
				"student": self.fixture.student.name,
				"incident_type": "Vol",
				"severity": "Grave",
				"description": "Vol signalé au réfectoire.",
				"parent_contacted": 1,
			}
		).insert(ignore_permissions=True)
		self.assertIsNotNone(case.parent_contacted_on)

	def test_instructor_cannot_access_disciplinary_case(self):
		# master.md §37: "Access must be restricted" - Instructor (teaching
		# staff generally) is deliberately not among the granted roles, only
		# School Director/Academic Director/Class Teacher (docs/architecture.md
		# section K).
		self.assertNotIn(
			"Instructor",
			[p.role for p in frappe.get_meta("Disciplinary Case").permissions],
		)
