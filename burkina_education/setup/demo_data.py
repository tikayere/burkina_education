# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Demo fixtures: "École Pilote Burkina" (master prompt section 66).

Fictional data only - no real students, guardians or staff. Safe to run
repeatedly (``bench execute burkina_education.setup.demo_data.run``); every
step checks for an existing record before creating one.

This seeds the Phase 1 slice only: school, academic structure, subjects,
a handful of students/guardians. Attendance, assessments, fees and report
cards are seeded once those modules are built (Phase 2/3).
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
	create_academic_terms(academic_year)
	grades_by_name = create_academic_structure(school)
	create_subjects()
	create_students(school, grades_by_name)
	frappe.db.commit()
	return {"school": school, "academic_year": academic_year}


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


def create_academic_terms(academic_year):
	terms = [
		("Trimestre 1", "2026-10-01", "2026-12-19", 1),
		("Trimestre 2", "2027-01-05", "2027-03-27", 2),
		("Trimestre 3", "2027-04-05", "2027-06-30", 3),
	]
	for title, start, end, sequence in terms:
		if frappe.db.exists("Academic Term", title):
			continue
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
