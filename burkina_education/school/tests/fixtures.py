# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Minimal School -> Education Level -> Cycle -> Grade -> Student chain,
shared by every Phase 5 (Operations) test suite - Discipline/Clinic/Library/
Transport/Canteen/Boarding all need exactly this and nothing phase-specific
(unlike Phase 2's AcademicFixture or Phase 3's FinanceFixture, which each add
real phase-specific plumbing - Course/Term, Company/CoA - on top of the same
base chain). Kept here once instead of duplicated six times (master.md §73:
"no unnecessary duplication"); each Phase 5 fixture subclasses this and adds
only what it actually needs.
"""

import frappe


class MinimalSchoolFixture:
	"""Everything is tagged with a random suffix so tests can run in
	parallel/repeatedly without name clashes."""

	def __init__(self, student_count=1):
		frappe.db.set_single_value("Education Settings", "user_creation_skip", 1)
		self.tag = frappe.generate_hash(length=6).upper()

		self.school = frappe.get_doc(
			{"doctype": "School", "school_name": f"Test School {self.tag}", "school_code": self.tag}
		).insert(ignore_permissions=True)

		self.education_level = frappe.get_doc(
			{
				"doctype": "Education Level",
				"education_level_name": f"Niveau {self.tag}",
				"school": self.school.name,
			}
		).insert(ignore_permissions=True)

		self.cycle = frappe.get_doc(
			{
				"doctype": "Cycle",
				"cycle_name": f"Cycle {self.tag}",
				"education_level": self.education_level.name,
				"school": self.school.name,
			}
		).insert(ignore_permissions=True)

		self.grade = frappe.get_doc(
			{"doctype": "Grade", "grade_name": f"Classe {self.tag}", "cycle": self.cycle.name}
		).insert(ignore_permissions=True)

		self.students = [self._create_student(i) for i in range(1, student_count + 1)]
		self.student = self.students[0]

	def _create_student(self, index):
		self._ensure_gender("Female")
		return frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": f"Eleve{index}",
				"last_name": self.tag,
				"gender": "Female",
				"student_email_id": f"eleve{index}.{self.tag}@test-fixture.bf".lower(),
				"grade": self.grade.name,
			}
		).insert(ignore_permissions=True)

	@staticmethod
	def _ensure_gender(gender):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)
		return gender
