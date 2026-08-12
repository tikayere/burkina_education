# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Shared test fixtures for the Phase 2 grading/ranking/examination test
suites - building the full Assessment Plan/Result chain by hand in every
test file would be repetitive and easy to get subtly wrong, so it lives here
once instead (master.md §73: "no unnecessary duplication").
"""

import frappe


def get_or_create_user(email, roles):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Test",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)

	existing_roles = {r.role for r in user.roles}
	for role in roles:
		if role not in existing_roles:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)
	return user


class AcademicFixture:
	"""Builds one School -> Education Level -> Cycle -> Grade -> Student Group,
	one Course, one Academic Year with two weighted Academic Terms, two
	Students, and the Assessment Group/Criteria/Grading Scale plumbing
	Education needs. Everything is tagged with a random suffix so tests can
	run in parallel/repeatedly without name clashes.
	"""

	def __init__(self):
		# Assessment Result -> User creation on Student would otherwise crash
		# on a blank email (docs/installation.md "Known environment quirks" /
		# the Phase 1 demo-data fix); tests run inside a rolled-back
		# transaction so this never leaks into real data.
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

		self.course = frappe.get_doc(
			{"doctype": "Course", "course_name": f"Matiere {self.tag}", "coefficient": 2}
		).insert(ignore_permissions=True)

		self.academic_year = frappe.get_doc(
			{
				"doctype": "Academic Year",
				"academic_year_name": f"AY {self.tag}",
				"year_start_date": "2025-09-01",
				"year_end_date": "2026-06-30",
			}
		).insert(ignore_permissions=True)

		self.term_1 = frappe.get_doc(
			{
				"doctype": "Academic Term",
				"academic_year": self.academic_year.name,
				"term_name": f"Trimestre 1 {self.tag}",
				"term_start_date": "2025-09-01",
				"term_end_date": "2025-12-15",
				"weight": 1,
			}
		).insert(ignore_permissions=True)

		self.term_2 = frappe.get_doc(
			{
				"doctype": "Academic Term",
				"academic_year": self.academic_year.name,
				"term_name": f"Trimestre 2 {self.tag}",
				"term_start_date": "2026-01-05",
				"term_end_date": "2026-03-30",
				"weight": 2,
			}
		).insert(ignore_permissions=True)

		self.students = [self._create_student(1), self._create_student(2)]

		# Assessment Plan.academic_term is `fetch_from: student_group.academic_term`
		# in Education (not independently settable), so a Student Group is
		# scoped to exactly one term - one Student Group per term is created
		# lazily by group_for_term(), each carrying the same student roster.
		self._groups = {}
		self.student_group = self.group_for_term(self.term_1.name)

		self.grading_scale = self._get_or_create_grading_scale()

		self.assessment_type_devoir = frappe.get_doc(
			{
				"doctype": "Assessment Type",
				"type_name": f"Devoir {self.tag}",
				"category": "Devoir",
				"default_coefficient": 1,
			}
		).insert(ignore_permissions=True)

		self.assessment_type_composition = frappe.get_doc(
			{
				"doctype": "Assessment Type",
				"type_name": f"Composition {self.tag}",
				"category": "Composition",
				"default_coefficient": 3,
			}
		).insert(ignore_permissions=True)

		self.grading_scheme = frappe.get_doc(
			{
				"doctype": "Grading Scheme",
				"scheme_name": f"Bareme {self.tag}",
				"education_level": self.education_level.name,
				"score_max": 20,
				"passing_score": 10,
				"is_default": 1,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

	def _create_student(self, index):
		self._ensure_gender("Male")
		return frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": f"Eleve{index}",
				"last_name": self.tag,
				"gender": "Male",
				"student_email_id": f"eleve{index}.{self.tag}@test-fixture.bf".lower(),
				# Custom field from Phase 1 - the grading engine resolves the
				# Grading Scheme via student -> grade -> cycle -> education level.
				"grade": self.grade.name,
			}
		).insert(ignore_permissions=True)

	@staticmethod
	def _ensure_gender(gender):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)
		return gender

	def _new_assessment_criteria(self):
		# Education rejects a second submitted Assessment Plan reusing the same
		# (course, student_group, assessment_group, assessment_criteria) tuple
		# regardless of term - see assessment_plan.py validate_assessment_criteria.
		# Each Assessment Plan created by create_result() therefore needs its
		# own criteria.
		self._criteria_seq = getattr(self, "_criteria_seq", 0) + 1
		name = f"Note {self.tag}-{self._criteria_seq}"
		frappe.get_doc({"doctype": "Assessment Criteria", "assessment_criteria": name}).insert(
			ignore_permissions=True
		)
		return name

	def group_for_term(self, academic_term):
		if academic_term in self._groups:
			return self._groups[academic_term]

		group = frappe.get_doc(
			{
				"doctype": "Student Group",
				"student_group_name": f"Groupe {self.tag} - {academic_term}",
				"academic_year": self.academic_year.name,
				"academic_term": academic_term,
				"group_based_on": "Batch",
				"program": self.grade.program,
				"max_strength": 0,
				"students": [
					{"student": s.name, "student_name": s.student_name, "active": 1} for s in self.students
				],
			}
		).insert(ignore_permissions=True)
		self._groups[academic_term] = group
		return group

	def _get_or_create_grading_scale(self):
		name = f"Test Grading Scale {self.tag}"
		doc = frappe.get_doc(
			{
				"doctype": "Grading Scale",
				"grading_scale_name": name,
				"intervals": [
					{"grade_code": "A", "threshold": 80},
					{"grade_code": "B", "threshold": 50},
					{"grade_code": "C", "threshold": 0},
				],
			}
		).insert(ignore_permissions=True)
		return doc.name

	def create_result(self, student, academic_term, assessment_type, score, max_score=20, coefficient=None):
		"""Create + submit an Assessment Plan/Result pair for one student, one
		course, one term: exactly the shape the grading engine reads."""
		# Education's Assessment Plan rejects overlapping date/time within the
		# same Student Group, so every call in a test needs its own slot - and
		# a fresh criteria (see _new_assessment_criteria).
		criteria = self._new_assessment_criteria()
		hour = 5 + self._criteria_seq
		student_group = self.group_for_term(academic_term)

		plan = frappe.get_doc(
			{
				"doctype": "Assessment Plan",
				"student_group": student_group.name,
				"assessment_group": "All Assessment Groups",
				"grading_scale": self.grading_scale,
				"course": self.course.name,
				"academic_year": self.academic_year.name,
				"schedule_date": frappe.utils.nowdate(),
				"from_time": f"{hour:02d}:00:00",
				"to_time": f"{hour:02d}:45:00",
				"maximum_assessment_score": max_score,
				"assessment_type": assessment_type.name,
				"coefficient": coefficient if coefficient is not None else assessment_type.default_coefficient,
				"assessment_criteria": [{"assessment_criteria": criteria, "maximum_score": max_score}],
			}
		).insert(ignore_permissions=True)
		plan.submit()

		result = frappe.get_doc(
			{
				"doctype": "Assessment Result",
				"assessment_plan": plan.name,
				"student": student.name,
				"academic_term": academic_term,
				"details": [{"assessment_criteria": criteria, "maximum_score": max_score, "score": score}],
			}
		).insert(ignore_permissions=True)
		result.submit()
		return result
