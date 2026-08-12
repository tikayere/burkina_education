# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic.tests.fixtures import AcademicFixture, get_or_create_user


class TestGradingEngine(FrappeTestCase):
	def setUp(self):
		self.fx = AcademicFixture()

	def test_weighted_subject_and_term_average(self):
		student = self.fx.students[0]

		# Devoir (coefficient 1): 12/20 ; Composition (coefficient 3): 16/20
		# Weighted subject average = (12*1 + 16*3) / (1+3) = 15
		self.fx.create_result(student, self.fx.term_1.name, self.fx.assessment_type_devoir, score=12)
		self.fx.create_result(student, self.fx.term_1.name, self.fx.assessment_type_composition, score=16)

		report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)
		report.compute()

		self.assertEqual(len(report.subjects), 1)
		self.assertEqual(report.subjects[0].course, self.fx.course.name)
		self.assertEqual(report.subjects[0].subject_average, 15.0)
		# Only one subject, so term average == subject average regardless of
		# course coefficient.
		self.assertEqual(report.term_average, 15.0)
		self.assertEqual(report.grading_scheme, self.fx.grading_scheme.name)

	def test_compute_is_blocked_after_submit(self):
		student = self.fx.students[0]
		self.fx.create_result(student, self.fx.term_1.name, self.fx.assessment_type_devoir, score=10)

		report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)
		report.compute()
		report.submit()

		with self.assertRaises(frappe.ValidationError):
			report.compute()

	def test_annual_average_weighted_by_term_weight(self):
		student = self.fx.students[0]

		self.fx.create_result(student, self.fx.term_1.name, self.fx.assessment_type_devoir, score=10)
		report_1 = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)
		report_1.compute()
		report_1.submit()

		self.fx.create_result(student, self.fx.term_2.name, self.fx.assessment_type_devoir, score=16)
		report_2 = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": student.name,
				"student_group": self.fx.group_for_term(self.fx.term_2.name).name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_2.name,
			}
		).insert(ignore_permissions=True)
		report_2.compute()
		report_2.submit()

		# term_1 weight=1 (avg 10), term_2 weight=2 (avg 16)
		# annual = (10*1 + 16*2) / 3 = 14
		annual = frappe.get_doc(
			{
				"doctype": "Student Annual Report",
				"student": student.name,
				"academic_year": self.fx.academic_year.name,
			}
		).insert(ignore_permissions=True)
		annual.compute()

		self.assertEqual(len(annual.terms), 2)
		self.assertEqual(annual.annual_average, 14.0)

	def test_only_authorized_roles_can_cancel_submitted_assessment_result(self):
		student = self.fx.students[0]
		result = self.fx.create_result(
			student, self.fx.term_1.name, self.fx.assessment_type_devoir, score=10
		)

		instructor = get_or_create_user(
			f"instructor_cancel_{self.fx.tag}@example.com".lower(), ["Instructor", "Academics User"]
		)
		with self.set_user(instructor.name):
			doc = frappe.get_doc("Assessment Result", result.name)
			with self.assertRaises(frappe.PermissionError):
				doc.cancel()

		director = get_or_create_user(
			f"director_cancel_{self.fx.tag}@example.com".lower(), ["Academic Director", "Academics User"]
		)
		with self.set_user(director.name):
			doc = frappe.get_doc("Assessment Result", result.name)
			doc.cancel()

		self.assertEqual(frappe.db.get_value("Assessment Result", result.name, "docstatus"), 2)
