# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCurriculum(FrappeTestCase):
	def setUp(self):
		code = frappe.generate_hash(length=6).upper()
		self.school = frappe.get_doc(
			{"doctype": "School", "school_name": f"Test School {code}", "school_code": code}
		).insert(ignore_permissions=True)
		self.education_level = frappe.get_doc(
			{"doctype": "Education Level", "education_level_name": f"Niveau {code}", "school": self.school.name}
		).insert(ignore_permissions=True)
		self.cycle = frappe.get_doc(
			{
				"doctype": "Cycle",
				"cycle_name": f"Cycle {code}",
				"education_level": self.education_level.name,
				"school": self.school.name,
			}
		).insert(ignore_permissions=True)
		self.grade = frappe.get_doc(
			{"doctype": "Grade", "grade_name": f"Classe {code}", "cycle": self.cycle.name}
		).insert(ignore_permissions=True)
		self.course = frappe.get_doc(
			{"doctype": "Course", "course_name": f"Matière {code}"}
		).insert(ignore_permissions=True)
		if not frappe.db.exists("Academic Year", f"AY {code}"):
			self.academic_year = frappe.get_doc(
				{
					"doctype": "Academic Year",
					"academic_year_name": f"AY {code}",
					"year_start_date": "2025-09-01",
					"year_end_date": "2026-06-30",
				}
			).insert(ignore_permissions=True)
		else:
			self.academic_year = frappe.get_doc("Academic Year", f"AY {code}")

	def test_curriculum_and_children_chain(self):
		curriculum = frappe.get_doc(
			{
				"doctype": "Curriculum",
				"grade": self.grade.name,
				"course": self.course.name,
				"academic_year": self.academic_year.name,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(curriculum.title, f"{self.grade.name} - {self.course.name} ({self.academic_year.name})")
		self.assertEqual(curriculum.school, self.school.name)

		competency = frappe.get_doc(
			{
				"doctype": "Competency",
				"curriculum": curriculum.name,
				"title": "Résoudre une équation du premier degré",
			}
		).insert(ignore_permissions=True)

		objective = frappe.get_doc(
			{
				"doctype": "Learning Objective",
				"competency": competency.name,
				"title": "Isoler l'inconnue dans une équation simple",
			}
		).insert(ignore_permissions=True)

		unit = frappe.get_doc(
			{"doctype": "Learning Unit", "curriculum": curriculum.name, "title": "Équations et inéquations"}
		).insert(ignore_permissions=True)

		lesson = frappe.get_doc(
			{
				"doctype": "Lesson",
				"learning_unit": unit.name,
				"title": "Introduction aux équations",
				"objectives": [{"learning_objective": objective.name}],
			}
		).insert(ignore_permissions=True)

		self.assertEqual(lesson.objectives[0].learning_objective, objective.name)

	def test_duplicate_curriculum_for_same_grade_course_year_rejected(self):
		frappe.get_doc(
			{
				"doctype": "Curriculum",
				"grade": self.grade.name,
				"course": self.course.name,
				"academic_year": self.academic_year.name,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Curriculum",
					"grade": self.grade.name,
					"course": self.course.name,
					"academic_year": self.academic_year.name,
				}
			).insert(ignore_permissions=True)
