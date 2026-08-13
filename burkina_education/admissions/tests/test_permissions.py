# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Permission-boundary regression tests for Admissions
(docs/architecture.md section O): Registrar owns the pipeline day-to-day,
Academic Director/School Director get the same rights for oversight,
Secretary deliberately does not (section M's own permission audit found
Secretary's real scope is communications-only)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic.tests.fixtures import get_or_create_user
from burkina_education.admissions.tests.fixtures import AdmissionsFixture


class TestAdmissionsPermissions(FrappeTestCase):
	def setUp(self):
		self.fixture = AdmissionsFixture()
		self.registrar = get_or_create_user(f"registrar.{self.fixture.tag}@test-fixture.bf", ["Registrar"])
		self.secretary = get_or_create_user(f"secretary.{self.fixture.tag}@test-fixture.bf", ["Secretary"])
		self.instructor = get_or_create_user(f"instructor.{self.fixture.tag}@test-fixture.bf", ["Instructor"])

	def test_registrar_can_write_student_applicant(self):
		self.assertTrue(frappe.has_permission("Student Applicant", "write", user=self.registrar.name))
		self.assertTrue(frappe.has_permission("Student Applicant", "create", user=self.registrar.name))

	def test_secretary_cannot_access_student_applicant(self):
		self.assertFalse(frappe.has_permission("Student Applicant", "read", user=self.secretary.name))
		self.assertFalse(frappe.has_permission("Student Applicant", "write", user=self.secretary.name))

	def test_instructor_cannot_access_student_applicant(self):
		self.assertFalse(frappe.has_permission("Student Applicant", "read", user=self.instructor.name))

	def test_pipeline_transition_checks_write_permission(self):
		applicant = self.fixture.create_applicant()
		applicant.submit_application()

		applicant_as_secretary = frappe.get_doc("Student Applicant", applicant.name)
		with self.set_user(self.secretary.name):
			with self.assertRaises(frappe.PermissionError):
				applicant_as_secretary.start_review()
