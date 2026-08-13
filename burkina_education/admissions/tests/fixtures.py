# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Shared test fixture for the Admissions pipeline test suite - see
school/tests/fixtures.py (Phase 5's MinimalSchoolFixture) and
finance/tests/fixtures.py for the equivalent pattern this mirrors. Needs its
own Academic Year on top of the minimal School->Grade chain (Student
Applicant requires one), so it isn't a thin subclass of either.
"""

import frappe


class AdmissionsFixture:
	"""One School -> Education Level -> Cycle -> Grade (owning a Program) ->
	Academic Year -> Guardian. Everything is tagged with a random suffix so
	tests can run in parallel/repeatedly without name clashes."""

	def __init__(self):
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

		self.academic_year = frappe.get_doc(
			{
				"doctype": "Academic Year",
				"academic_year_name": f"AY {self.tag}",
				"year_start_date": "2025-09-01",
				"year_end_date": "2026-06-30",
			}
		).insert(ignore_permissions=True)

		self._ensure_gender("Female")
		self.guardian = frappe.get_doc(
			{
				"doctype": "Guardian",
				"guardian_name": f"Tuteur {self.tag}",
				"email_address": f"tuteur.{self.tag}@test-fixture.bf".lower(),
			}
		).insert(ignore_permissions=True)

	def create_applicant(self, **overrides):
		values = {
			"doctype": "Student Applicant",
			"first_name": f"Candidat{self.tag}",
			"last_name": self.tag,
			"gender": "Female",
			"student_email_id": f"candidat.{self.tag}.{frappe.generate_hash(length=4)}@test-fixture.bf".lower(),
			"academic_year": self.academic_year.name,
			"requested_grade": self.grade.name,
			"guardians": [{"guardian": self.guardian.name, "relation": "Mother"}],
		}
		values.update(overrides)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	@staticmethod
	def _ensure_gender(gender):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)
		return gender
