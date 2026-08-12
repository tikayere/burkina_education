# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestGrade(FrappeTestCase):
	def setUp(self):
		self.school = make_school("test_school_grade")
		self.level = frappe.get_doc(
			{
				"doctype": "Education Level",
				"education_level_name": "Primaire",
				"school": self.school,
			}
		).insert(ignore_permissions=True)
		self.cycle = frappe.get_doc(
			{
				"doctype": "Cycle",
				"cycle_name": "Primaire",
				"education_level": self.level.name,
			}
		).insert(ignore_permissions=True)

	def test_grade_auto_creates_program(self):
		grade = frappe.get_doc(
			{
				"doctype": "Grade",
				"grade_name": "CP1",
				"cycle": self.cycle.name,
			}
		).insert(ignore_permissions=True)

		self.assertTrue(grade.program)
		self.assertTrue(frappe.db.exists("Program", grade.program))
		self.assertEqual(grade.school, self.school)

	def test_duplicate_grade_in_same_cycle_is_rejected(self):
		frappe.get_doc(
			{"doctype": "Grade", "grade_name": "CE1", "cycle": self.cycle.name}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{"doctype": "Grade", "grade_name": "CE1", "cycle": self.cycle.name}
			).insert(ignore_permissions=True)

	def test_deleting_grade_removes_unused_program(self):
		grade = frappe.get_doc(
			{"doctype": "Grade", "grade_name": "CE2", "cycle": self.cycle.name}
		).insert(ignore_permissions=True)
		program_name = grade.program

		grade.delete()

		self.assertFalse(frappe.db.exists("Program", program_name))


def make_school(code_prefix):
	code = frappe.generate_hash(length=6).upper()
	school = frappe.get_doc(
		{
			"doctype": "School",
			"school_name": f"Test School {code}",
			"school_code": code,
		}
	).insert(ignore_permissions=True)
	return school.name
