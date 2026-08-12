# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Demo fixtures: "École Pilote Burkina" (master prompt section 66).

Fictional data only - no real students, guardians or staff. Safe to run
repeatedly (``bench execute burkina_education.setup.demo_data.run``); every
step checks for an existing record before creating one.

Phase 1: school, academic structure, subjects, students/guardians.
Phase 2 (this file, added alongside the grading engine): a Grading Scheme,
Assessment Types, one Student Group per demo grade, a first-term Assessment
Plan/Result per student, Student Attendance, and a computed+ranked+submitted
Student Term Report per student - so the whole Phase 2 chain (marks -> lock
-> compute -> rank -> bulletin) has real, inspectable demo data instead of
only being covered by unit tests. Fees/report cards for other terms and
Phase 3+ modules are seeded once those are built.
"""

import frappe

SCHOOL_CODE = "EPB"
ACADEMIC_YEAR = "2026-2027"

EDUCATION_LEVELS = [
	# (name, sequence, [(cycle_name, [grade_names])])
	("Préscolaire", 1, [("Préscolaire", ["Petite Section", "Moyenne Section", "Grande Section"])]),
	("Primaire", 2, [("Primaire", ["CP1", "CP2", "CE1", "CE2", "CM1", "CM2"])]),
	("Post-primaire", 3, [("Collège", ["6ème", "5ème", "4ème", "3ème"])]),
	("Secondaire", 4, [("Lycée", ["2nde", "1ère", "Terminale"])]),
]

SUBJECTS = [
	# (name, code, coefficient, hours_per_week)
	("Français", "FR", 4, 6),
	("Mathématiques", "MATH", 4, 5),
	("Sciences", "SCI", 2, 3),
	("Histoire-Géographie", "HG", 2, 3),
	("Anglais", "ANG", 2, 3),
	("Éducation Physique et Sportive", "EPS", 1, 2),
]

GRADING_SCHEME_NAME = "Barème Général"

# (type_name, category, default_coefficient)
ASSESSMENT_TYPES = [
	("Devoir", "Devoir", 1),
	("Composition", "Composition", 3),
]

# Subjects a first-term Assessment Plan/Result is seeded for, per student.
DEMO_RESULT_SUBJECTS = ["Français", "Mathématiques"]

# (first, last, sex, grade, email, guardian(s) as (name, relationship, phone))
STUDENTS = [
	(
		"Amadou",
		"Ouédraogo",
		"Male",
		"6ème",
		"amadou.ouedraogo@epb-demo.bf",
		[("Issa Ouédraogo", "Father", "+22670000001")],
	),
	(
		"Aïcha",
		"Ouédraogo",
		"Female",
		"CM2",
		"aicha.ouedraogo@epb-demo.bf",
		[("Issa Ouédraogo", "Father", "+22670000001")],  # sibling of Amadou
	),
	(
		"Fatoumata",
		"Traoré",
		"Female",
		"5ème",
		"fatoumata.traore@epb-demo.bf",
		[("Salimata Traoré", "Mother", "+22670000002")],
	),
]


def run():
	ensure_genders()
	school = create_school()
	academic_year = create_academic_year()
	terms_by_title = create_academic_terms(academic_year)
	term_1 = terms_by_title["Trimestre 1"]
	grades_by_name = create_academic_structure(school)
	create_subjects()
	create_students(school, grades_by_name)

	create_grading_scheme()
	create_assessment_types()
	groups_by_grade = create_student_groups(academic_year, term_1, grades_by_name)
	seed_term_1_results(groups_by_grade)
	seed_term_1_attendance(groups_by_grade)
	report_names = generate_and_rank_term_reports(groups_by_grade, term_1)

	frappe.db.commit()
	return {"school": school, "academic_year": academic_year, "student_term_reports": report_names}


def ensure_genders():
	# Frappe ships the Gender doctype but does not seed it outside the Setup
	# Wizard; Student.gender links to it, so make sure the basics exist.
	for gender in ("Male", "Female", "Other"):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)


def create_school():
	if frappe.db.exists("School", SCHOOL_CODE):
		return SCHOOL_CODE

	school = frappe.get_doc(
		{
			"doctype": "School",
			"school_name": "École Pilote Burkina",
			"school_code": SCHOOL_CODE,
			"official_name": "École Pilote Burkina",
			"school_type": "Privé",
			"ownership_type": "Privé",
			"city": "Ouagadougou",
			"province": "Kadiogo",
			"country": "Burkina Faso",
			"default_currency": "XOF",
			"default_language": "fr",
		}
	).insert(ignore_permissions=True)
	return school.name


def create_academic_year():
	if frappe.db.exists("Academic Year", ACADEMIC_YEAR):
		return ACADEMIC_YEAR

	year = frappe.get_doc(
		{
			"doctype": "Academic Year",
			"academic_year_name": ACADEMIC_YEAR,
			"year_start_date": "2026-10-01",
			"year_end_date": "2027-06-30",
		}
	).insert(ignore_permissions=True)
	return year.name


def academic_term_name(academic_year, title):
	# Academic Term overrides autoname() to "{academic_year} ({term_name})"
	# rather than using its declared `autoname: field:title` literally - see
	# education/education/doctype/academic_term/academic_term.py.
	return f"{academic_year} ({title})"


def create_academic_terms(academic_year):
	"""Returns {"Trimestre 1": <actual docname>, ...}."""
	terms = [
		("Trimestre 1", "2026-10-01", "2026-12-19", 1),
		("Trimestre 2", "2027-01-05", "2027-03-27", 2),
		("Trimestre 3", "2027-04-05", "2027-06-30", 3),
	]
	names = {}
	for title, start, end, sequence in terms:
		name = academic_term_name(academic_year, title)
		if not frappe.db.exists("Academic Term", name):
			frappe.get_doc(
				{
					"doctype": "Academic Term",
					"academic_year": academic_year,
					"term_name": title,
					"title": title,
					"term_start_date": start,
					"term_end_date": end,
					"sequence": sequence,
					"weight": 1,
				}
			).insert(ignore_permissions=True)
		names[title] = name
	return names


def create_academic_structure(school):
	"""Create Education Levels -> Cycles -> Grades. Returns {grade_name: Grade docname}."""
	grades_by_name = {}

	for level_name, sequence, cycles in EDUCATION_LEVELS:
		level = frappe.db.get_value(
			"Education Level", {"school": school, "education_level_name": level_name}, "name"
		)
		if not level:
			level = frappe.get_doc(
				{
					"doctype": "Education Level",
					"education_level_name": level_name,
					"school": school,
					"sequence": sequence,
				}
			).insert(ignore_permissions=True).name

		for cycle_seq, (cycle_name, grade_names) in enumerate(cycles, start=1):
			cycle = frappe.db.get_value(
				"Cycle", {"education_level": level, "cycle_name": cycle_name}, "name"
			)
			if not cycle:
				cycle = frappe.get_doc(
					{
						"doctype": "Cycle",
						"cycle_name": cycle_name,
						"education_level": level,
						"sequence": cycle_seq,
					}
				).insert(ignore_permissions=True).name

			for grade_seq, grade_name in enumerate(grade_names, start=1):
				grade = frappe.db.get_value("Grade", {"cycle": cycle, "grade_name": grade_name}, "name")
				if not grade:
					grade = frappe.get_doc(
						{
							"doctype": "Grade",
							"grade_name": grade_name,
							"cycle": cycle,
							"sequence": grade_seq,
						}
					).insert(ignore_permissions=True).name
				grades_by_name[grade_name] = grade

	return grades_by_name


def create_subjects():
	for name, code, coefficient, hours in SUBJECTS:
		if frappe.db.exists("Course", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Course",
				"course_name": name,
				"course_code": code,
				"coefficient": coefficient,
				"hours_per_week": hours,
				"grading_type": "Numeric",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)


def create_students(school, grades_by_name):
	guardians_by_name = {}

	# Education auto-creates a Website User + sends a welcome email for every
	# Student with an email address (student.py::validate_user). Demo emails
	# are fictional, so skip that side effect for this seed run only.
	education_settings = frappe.get_single("Education Settings")
	previous_skip_value = education_settings.user_creation_skip
	frappe.db.set_single_value("Education Settings", "user_creation_skip", 1)

	try:
		_create_students(school, grades_by_name, guardians_by_name)
	finally:
		frappe.db.set_single_value(
			"Education Settings", "user_creation_skip", previous_skip_value
		)


def _create_students(school, grades_by_name, guardians_by_name):
	for first, last, sex, grade_name, email, guardians in STUDENTS:
		full_name = f"{first} {last}"
		if frappe.db.exists("Student", {"student_name": full_name}):
			continue

		grade = grades_by_name.get(grade_name)
		student = frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": first,
				"last_name": last,
				"student_name": full_name,
				"student_email_id": email,
				"gender": sex,
				"school": school,
				"grade": grade,
				"enabled": 1,
				"status": "Active",
				"joining_date": "2026-10-01",
			}
		)

		for guardian_name, relationship, phone in guardians:
			if guardian_name not in guardians_by_name:
				guardian_docname = frappe.db.get_value("Guardian", {"guardian_name": guardian_name}, "name")
				if not guardian_docname:
					guardian_docname = frappe.get_doc(
						{
							"doctype": "Guardian",
							"guardian_name": guardian_name,
							"mobile_number": phone,
							"preferred_channel": "SMS",
							"sms_consent": 1,
							"portal_access": 1,
							"payment_responsibility": 1,
						}
					).insert(ignore_permissions=True).name
				guardians_by_name[guardian_name] = guardian_docname

			student.append(
				"guardians",
				{
					"guardian": guardians_by_name[guardian_name],
					"relation": relationship,
				},
			)

		student.insert(ignore_permissions=True)


def create_grading_scheme():
	if frappe.db.exists("Grading Scheme", GRADING_SCHEME_NAME):
		return GRADING_SCHEME_NAME

	frappe.get_doc(
		{
			"doctype": "Grading Scheme",
			"scheme_name": GRADING_SCHEME_NAME,
			"score_max": 20,
			"passing_score": 10,
			"use_coefficients": 1,
			"term_average_method": "Weighted by Coefficient",
			"annual_average_method": "Weighted by Term Weight",
			"is_default": 1,
			"is_active": 1,
		}
	).insert(ignore_permissions=True)
	return GRADING_SCHEME_NAME


def create_assessment_types():
	for type_name, category, coefficient in ASSESSMENT_TYPES:
		if frappe.db.exists("Assessment Type", type_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Assessment Type",
				"type_name": type_name,
				"category": category,
				"default_coefficient": coefficient,
			}
		).insert(ignore_permissions=True)


def create_student_groups(academic_year, term_1, grades_by_name):
	"""One Student Group ("A") per demo grade, scoped to Trimestre 1, with
	that grade's demo student(s) as active members. Education's Assessment
	Plan.academic_term is fetch_from student_group.academic_term (see
	docs/architecture.md section G), so a Student Group is term-scoped.
	"""
	groups_by_grade = {}

	demo_grade_names = {grade_name for *_, grade_name, _email, _guardians in STUDENTS}
	for grade_name in demo_grade_names:
		grade = grades_by_name.get(grade_name)
		if not grade:
			continue

		group_name = f"{grade_name} A"
		program = frappe.db.get_value("Grade", grade, "program")

		if frappe.db.exists("Student Group", group_name):
			groups_by_grade[grade_name] = group_name
			continue

		students_in_grade = frappe.get_all("Student", filters={"grade": grade}, fields=["name", "student_name"])

		frappe.get_doc(
			{
				"doctype": "Student Group",
				"student_group_name": group_name,
				"academic_year": academic_year,
				"academic_term": term_1,
				"group_based_on": "Batch",
				"program": program,
				"students": [
					{"student": s.name, "student_name": s.student_name, "active": 1} for s in students_in_grade
				],
			}
		).insert(ignore_permissions=True)
		groups_by_grade[grade_name] = group_name

	return groups_by_grade


def seed_term_1_results(groups_by_grade):
	"""One submitted Assessment Plan/Result per (student, subject, assessment
	type) for Trimestre 1, so the grading engine has real marks to compute
	from. Scores are plausible but arbitrary - this is demo data, not a real
	gradebook.
	"""
	import random

	random.seed(42)  # deterministic across re-runs

	assessment_types = {
		row.type_name: row.default_coefficient
		for row in frappe.get_all("Assessment Type", fields=["type_name", "default_coefficient"])
	}
	grading_scale = frappe.db.get_value("Grading Scale", {}, "name")

	for grade_name, group_name in groups_by_grade.items():
		students = frappe.get_all(
			"Student Group Student", filters={"parent": group_name, "active": 1}, fields=["student"]
		)
		for row in students:
			for slot, subject in enumerate(DEMO_RESULT_SUBJECTS):
				if not frappe.db.exists("Course", subject):
					continue
				for type_index, (type_name, coefficient) in enumerate(assessment_types.items()):
					_seed_one_result(
						student=row.student,
						group_name=group_name,
						course=subject,
						assessment_type=type_name,
						coefficient=coefficient,
						grading_scale=grading_scale,
						slot=slot * len(assessment_types) + type_index,
						score=round(random.uniform(9, 18), 1),
					)


def _seed_one_result(student, group_name, course, assessment_type, coefficient, grading_scale, slot, score):
	criteria_name = f"Note {course} {assessment_type} {student}"
	if frappe.db.exists("Assessment Result", {"student": student, "course": course}):
		# Cheap idempotency check: if this student already has *a* result for
		# this course, assume the whole demo seed already ran for them.
		existing = frappe.get_all(
			"Assessment Result",
			filters={"student": student, "course": course},
			fields=["assessment_plan"],
			limit=1,
		)
		if existing:
			plan_course = frappe.db.get_value("Assessment Plan", existing[0].assessment_plan, "course")
			if plan_course == course:
				return

	if not frappe.db.exists("Assessment Criteria", criteria_name):
		frappe.get_doc({"doctype": "Assessment Criteria", "assessment_criteria": criteria_name}).insert(
			ignore_permissions=True
		)

	hour = 6 + slot
	plan = frappe.get_doc(
		{
			"doctype": "Assessment Plan",
			"student_group": group_name,
			"assessment_group": "All Assessment Groups",
			"grading_scale": grading_scale,
			"course": course,
			"schedule_date": "2026-11-15",
			"from_time": f"{hour:02d}:00:00",
			"to_time": f"{hour:02d}:45:00",
			"maximum_assessment_score": 20,
			"assessment_type": assessment_type,
			"coefficient": coefficient,
			"assessment_criteria": [{"assessment_criteria": criteria_name, "maximum_score": 20}],
		}
	).insert(ignore_permissions=True)
	plan.submit()

	result = frappe.get_doc(
		{
			"doctype": "Assessment Result",
			"assessment_plan": plan.name,
			"student": student,
			"details": [{"assessment_criteria": criteria_name, "maximum_score": 20, "score": score}],
		}
	).insert(ignore_permissions=True)
	result.submit()


def seed_term_1_attendance(groups_by_grade):
	"""A handful of Present/Absent/Late records per demo student over
	Trimestre 1's first two weeks - enough for the bulletin's attendance
	summary and the attendance-alert job to have something to read.
	"""
	pattern = ["Present", "Present", "Present", "Absent", "Present", "Late", "Present"]

	for group_name in groups_by_grade.values():
		students = frappe.get_all(
			"Student Group Student", filters={"parent": group_name, "active": 1}, fields=["student"]
		)
		for row in students:
			for day_offset, status in enumerate(pattern):
				date = frappe.utils.add_days("2026-10-05", day_offset)
				if frappe.db.exists("Student Attendance", {"student": row.student, "date": date}):
					continue
				doc = frappe.get_doc(
					{
						"doctype": "Student Attendance",
						"student": row.student,
						"student_group": group_name,
						"date": date,
						"status": status,
					}
				).insert(ignore_permissions=True)
				doc.submit()


def generate_and_rank_term_reports(groups_by_grade, term_1):
	"""Compute, submit and rank a Student Term Report per demo student for
	Trimestre 1 - the end-to-end payoff of everything else seeded above,
	and what the "Bulletin Burkina" print format is designed to render.
	"""
	from burkina_education.academic import grading, ranking

	report_names = []
	for group_name in groups_by_grade.values():
		names = grading.generate_term_reports(group_name, term_1)
		for name in names:
			doc = frappe.get_doc("Student Term Report", name)
			if doc.docstatus == 0:
				doc.submit()
			report_names.append(name)

		ranking.rank_term_reports(group_name, term_1)

	return report_names
