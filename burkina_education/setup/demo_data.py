# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Demo fixtures: "École Pilote Burkina" (master prompt section 66).

Fictional data only - no real students, guardians or staff. Safe to run
repeatedly (``bench execute burkina_education.setup.demo_data.run``); every
step checks for an existing record before creating one.

Phase 1: school, academic structure, subjects, students/guardians.
Admissions (§13, docs/architecture.md section O): three Student Applicants at
different pipeline stages - one walked all the way through to a real
enrolled Student (exercising submit/review/decide/fee/enroll for real), one
left mid-review, one decided Waitlisted - so the Registrar's dashboard/portal
has a real spread instead of an empty funnel.
Phase 2: a Grading Scheme, Assessment Types, one Student Group per demo
grade, a first-term Assessment Plan/Result per student, Student Attendance,
and a computed+ranked+submitted Student Term Report per student - so the
whole Phase 2 chain (marks -> lock -> compute -> rank -> bulletin) has real,
inspectable demo data instead of only being covered by unit tests.
Phase 3: a Company (XOF), Fee Category/Structure/Schedule per demo grade, a
Scholarship, one Sales Invoice per demo student (Education's own
``create_sales_invoice`` - exercising the scholarship/sibling discount hook
for real), one paid in cash (Payment Entry), one paid via a simulated Mobile
Money round-trip (initiate -> webhook -> Payment Entry), one left
outstanding so "outstanding fees" reporting has something to show.
Phase 4 (Communication): a sandbox SMS/WhatsApp Messaging Provider each,
French Notification Templates for every event_key, one Guardian and one
Student promoted to real portal Users (communication.portal.invite_*), and
a published "École Pilote Burkina" Announcement - so the notification
fan-out triggered automatically by the Phase 3 payments/Phase 2 term
reports above (Payment Entry.on_submit / Student Term Report.on_submit,
hooks.py) has real templates/providers to actually send through, not just
silently skip for lack of configuration.
Phase 5 (Operations): one Disciplinary Case and one Clinic Visit (each
scoped to a different demo student, since Clinic access is more restricted
than Discipline's - docs/architecture.md section K), a small Library
catalog with copies plus one open loan, a Transport Route with a student
assigned to a stop, the four school-relevant Asset Categories (needs the
Phase 3 Company's chart of accounts, so this runs last), one Canteen
Subscription with a logged meal, and one Boarding building/room/bed with a
student checked in.
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

COMPANY_NAME = "École Pilote Burkina"

# (category_name, amount in XOF)
FEE_CATEGORIES = [
	("Frais d'inscription", 15000),
	("Frais de scolarité", 85000),
]

MODES_OF_PAYMENT = [
	# (name, type)
	("Espèces", "Cash"),
	("Virement Bancaire", "Bank"),
	("Orange Money", "General"),
	("Moov Money", "General"),
]

MOBILE_MONEY_PROVIDER_NAME = "Orange Money Demo"

# Student full name that receives a demo Scholarship (exercises the discount
# hook in real demo data, not only in tests).
SCHOLARSHIP_STUDENT = "Fatoumata Traoré"

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

# Admissions (§13, docs/architecture.md section O): three applications at
# different pipeline stages, so the Registrar's dashboard/portal has a real
# spread to show rather than an empty funnel. (first, last, sex, grade,
# email, guardian(name, relation, phone), final_stage)
# final_stage: "enroll" walks all the way to a real Student; "review" stops
# mid-pipeline; "waitlist" is decided but not yet enrolled.
ADMISSIONS_APPLICANTS = [
	(
		"Boureima",
		"Sawadogo",
		"Male",
		"CP1",
		"boureima.sawadogo@epb-demo.bf",
		("Aminata Kaboré", "Mother", "+22670000003"),
		"enroll",
	),
	(
		"Aïssata",
		"Zongo",
		"Female",
		"6ème",
		"aissata.zongo@epb-demo.bf",
		("Boukary Zongo", "Father", "+22670000004"),
		"review",
	),
	(
		"Karim",
		"Diallo",
		"Male",
		"5ème",
		"karim.diallo@epb-demo.bf",
		("Mariam Diallo", "Mother", "+22670000005"),
		"waitlist",
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
	admissions_demo = create_admissions_demo(academic_year, grades_by_name)

	# Phase 4 setup runs before anything that can trigger a notification
	# (Student Term Report/Payment Entry submission below) so those hooks
	# have a real template + provider to send through instead of silently
	# skipping for lack of configuration.
	create_messaging_providers()
	create_notification_templates()

	create_grading_scheme()
	create_assessment_types()
	groups_by_grade = create_student_groups(academic_year, term_1, grades_by_name)
	seed_term_1_results(groups_by_grade)
	seed_term_1_attendance(groups_by_grade)
	report_names = generate_and_rank_term_reports(groups_by_grade, term_1)

	company = create_company()
	create_modes_of_payment()
	create_scholarship(academic_year)
	schedules_by_grade = create_fee_structures_and_schedules(company, academic_year, groups_by_grade, grades_by_name)
	invoice_names = seed_invoices(schedules_by_grade, groups_by_grade)
	provider = create_mobile_money_provider()
	payments = seed_payments(invoice_names, provider)

	portal_users = create_portal_users()
	announcement = create_demo_announcement()

	# Phase 5 (Operations) - runs last since Library/Transport/Canteen/
	# Boarding fees reuse the Finance fee engine (company) and Assets needs
	# the Company's chart of accounts (docs/architecture.md section K).
	disciplinary_case = create_disciplinary_case_demo()
	clinic_visit = create_clinic_visit_demo()
	library_membership = create_library_demo()
	transport_route = create_transport_demo()
	asset_categories = create_asset_categories_demo(company)
	canteen_subscription = create_canteen_demo()
	boarding_assignment = create_boarding_demo()

	frappe.db.commit()
	return {
		"school": school,
		"academic_year": academic_year,
		"student_term_reports": report_names,
		"company": company,
		"sales_invoices": invoice_names,
		"payments": payments,
		"portal_users": portal_users,
		"announcement": announcement,
		"disciplinary_case": disciplinary_case,
		"clinic_visit": clinic_visit,
		"library_membership": library_membership,
		"transport_route": transport_route,
		"asset_categories": asset_categories,
		"canteen_subscription": canteen_subscription,
		"boarding_assignment": boarding_assignment,
		"admissions_demo": admissions_demo,
	}


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


def create_admissions_demo(academic_year, grades_by_name):
	"""Application -> Review -> Acceptance -> Admission -> Enrollment
	(master.md §13, docs/architecture.md section O), exercised on real demo
	data at three different stages - not only in tests. Runs after
	create_students() (same Education Settings user-creation-skip guard
	applies to the Student the "enroll" applicant produces)."""
	education_settings = frappe.get_single("Education Settings")
	previous_skip_value = education_settings.user_creation_skip
	frappe.db.set_single_value("Education Settings", "user_creation_skip", 1)

	created = {}
	try:
		for first, last, sex, grade_name, email, guardian, final_stage in ADMISSIONS_APPLICANTS:
			full_name = f"{first} {last}"
			applicant_name = frappe.db.get_value("Student Applicant", {"title": full_name}, "name")
			if applicant_name:
				created[full_name] = applicant_name
				continue

			grade = grades_by_name.get(grade_name)
			guardian_name, relation, phone = guardian
			guardian_docname = frappe.db.get_value("Guardian", {"guardian_name": guardian_name}, "name")
			if not guardian_docname:
				guardian_docname = (
					frappe.get_doc(
						{
							"doctype": "Guardian",
							"guardian_name": guardian_name,
							"mobile_number": phone,
							"preferred_channel": "SMS",
							"sms_consent": 1,
							"portal_access": 1,
							"payment_responsibility": 1,
						}
					)
					.insert(ignore_permissions=True)
					.name
				)

			applicant = frappe.get_doc(
				{
					"doctype": "Student Applicant",
					"first_name": first,
					"last_name": last,
					"gender": sex,
					"student_email_id": email,
					"academic_year": academic_year,
					"requested_grade": grade,
					"guardians": [{"guardian": guardian_docname, "relation": relation}],
				}
			).insert(ignore_permissions=True)

			applicant.submit_application()
			applicant.start_review()

			if final_stage == "review":
				created[full_name] = applicant.name
				continue

			if final_stage == "waitlist":
				applicant.record_decision(
					"Liste d'attente",
					notes="Dossier favorable, en attente d'une place disponible dans la classe.",
				)
				created[full_name] = applicant.name
				continue

			# "enroll": accept, collect the admission fee, then enroll -
			# creates a real Student + Program Enrollment. Same amount as the
			# "Frais d'inscription" Fee Category below - collect_admission_fee()
			# requires a non-zero admission_fee_amount, which has no default.
			applicant.record_decision("Acceptée", notes="Entretien favorable, dossier complet.")
			applicant.admission_fee_amount = 15000
			applicant.save()
			applicant.collect_admission_fee(mode_of_payment="Espèces")
			result = applicant.enroll()
			created[full_name] = applicant.name
			created[f"{full_name} (élève)"] = result["student"]
	finally:
		frappe.db.set_single_value("Education Settings", "user_creation_skip", previous_skip_value)

	return created


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

	# dict.fromkeys (not a set) so iteration order is deterministic across
	# runs - a plain set's order depends on the process's hash seed, which
	# would otherwise make seed_payments() (cash/mobile-money/outstanding
	# assigned by invoice position) allocate differently on every re-run.
	demo_grade_names = dict.fromkeys(grade_name for *_, grade_name, _email, _guardians in STUDENTS)
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


# ---------------------------------------------------------------------------
# Phase 3 - Finance
# ---------------------------------------------------------------------------


def create_company():
	"""The demo school's own Company - normally created by the Setup Wizard,
	which this headless dev environment skips (see docs/installation.md)."""
	if not frappe.db.get_value("Currency", "XOF", "enabled"):
		frappe.db.set_value("Currency", "XOF", "enabled", 1)

	if not frappe.db.exists("Company", COMPANY_NAME):
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": COMPANY_NAME,
				"abbr": "EPB",
				"default_currency": "XOF",
				"country": "Burkina Faso",
				"create_chart_of_accounts_based_on": "Standard Template",
				"chart_of_accounts": "Standard",
			}
		).insert(ignore_permissions=True)

	# Mirrors what the Setup Wizard's own install_fixtures.set_global_defaults
	# does for the school's chosen company/currency - without this, Sales
	# Invoice falls back to the system's INR default instead of XOF.
	global_defaults = frappe.get_single("Global Defaults")
	if global_defaults.default_company != COMPANY_NAME or global_defaults.default_currency != "XOF":
		global_defaults.default_company = COMPANY_NAME
		global_defaults.default_currency = "XOF"
		global_defaults.country = "Burkina Faso"
		global_defaults.save(ignore_permissions=True)

	ensure_default_holiday_list()

	return COMPANY_NAME


def ensure_default_holiday_list():
	"""Once ``École Pilote Burkina`` becomes the *global* default company
	(above), Education's ``Student Attendance.validate_is_holiday()`` starts
	resolving it for every attendance record system-wide and requires it to
	have a ``default_holiday_list`` - normally set by the Setup Wizard.
	Sunday is the standard school weekly off in Burkina Faso.
	"""
	list_name = f"{COMPANY_NAME} {ACADEMIC_YEAR}"
	if not frappe.db.exists("Holiday List", list_name):
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": list_name,
				"from_date": "2026-10-01",
				"to_date": "2027-06-30",
				"weekly_off": "Sunday",
			}
		)
		holiday_list.get_weekly_off_dates()
		holiday_list.insert(ignore_permissions=True)

	if frappe.db.get_value("Company", COMPANY_NAME, "default_holiday_list") != list_name:
		frappe.db.set_value("Company", COMPANY_NAME, "default_holiday_list", list_name)


def create_modes_of_payment():
	for name, mop_type in MODES_OF_PAYMENT:
		if frappe.db.exists("Mode of Payment", name):
			continue
		frappe.get_doc(
			{"doctype": "Mode of Payment", "mode_of_payment": name, "type": mop_type, "enabled": 1}
		).insert(ignore_permissions=True)


def create_scholarship(academic_year):
	student = frappe.db.get_value("Student", {"student_name": SCHOLARSHIP_STUDENT}, "name")
	if not student:
		return None
	if frappe.db.exists("Scholarship", {"student": student, "academic_year": academic_year}):
		return frappe.db.get_value("Scholarship", {"student": student, "academic_year": academic_year}, "name")

	scholarship = frappe.get_doc(
		{
			"doctype": "Scholarship",
			"student": student,
			"academic_year": academic_year,
			"scholarship_type": "Bourse Partielle",
			"discount_percent": 30,
			"status": "Approuvée",
			"reason": "Bourse au mérite - démonstration",
		}
	).insert(ignore_permissions=True)
	return scholarship.name


def create_fee_structures_and_schedules(company, academic_year, groups_by_grade, grades_by_name):
	"""One Fee Structure + one Fee Schedule per demo grade (same components/
	amounts for every grade - this is demo data, not a real fee policy),
	targeting that grade's Student Group.
	"""
	for category_name, _amount in FEE_CATEGORIES:
		if not frappe.db.exists("Fee Category", category_name):
			frappe.get_doc({"doctype": "Fee Category", "category_name": category_name}).insert(
				ignore_permissions=True
			)

	schedules_by_grade = {}

	for grade_name, group_name in groups_by_grade.items():
		grade = grades_by_name.get(grade_name)
		program = frappe.db.get_value("Grade", grade, "program")
		if not program:
			continue

		structure_name = frappe.db.get_value(
			"Fee Structure", {"program": program, "academic_year": academic_year}, "name"
		)
		if not structure_name:
			structure = frappe.get_doc(
				{
					"doctype": "Fee Structure",
					"program": program,
					"academic_year": academic_year,
					"company": company,
					"components": [
						{"fees_category": cat, "amount": amount} for cat, amount in FEE_CATEGORIES
					],
				}
			).insert(ignore_permissions=True)
			structure.submit()
			structure_name = structure.name

		schedule_name = frappe.db.get_value("Fee Schedule", {"fee_structure": structure_name}, "name")
		if not schedule_name:
			structure = frappe.get_doc("Fee Structure", structure_name)
			schedule = frappe.get_doc(
				{
					"doctype": "Fee Schedule",
					"fee_structure": structure_name,
					"academic_year": academic_year,
					"company": company,
					"due_date": "2026-11-30",
					"components": [
						{"fees_category": c.fees_category, "amount": c.amount, "total": c.total}
						for c in structure.components
					],
					"student_groups": [{"student_group": group_name}],
				}
			).insert(ignore_permissions=True)
			schedule.submit()
			schedule_name = schedule.name

		schedules_by_grade[grade_name] = schedule_name

	return schedules_by_grade


def seed_invoices(schedules_by_grade, groups_by_grade):
	"""One Sales Invoice per demo student, built with Education's own
	``create_sales_invoice`` (the exact function ``Fee Schedule.create_fees()``
	uses in production) - so the scholarship/sibling discount hook
	(``finance.discounts``) runs on real demo data, not only in tests.
	"""
	from education.education.doctype.fee_schedule.fee_schedule import create_sales_invoice

	invoice_names = []
	for grade_name, schedule_name in schedules_by_grade.items():
		group_name = groups_by_grade[grade_name]
		students = frappe.get_all(
			"Student Group Student", filters={"parent": group_name, "active": 1}, fields=["student"]
		)
		for row in students:
			existing = frappe.db.get_value(
				"Sales Invoice", {"student": row.student, "fee_schedule": schedule_name}, "name"
			)
			if existing:
				invoice_names.append(existing)
				continue

			name = create_sales_invoice(schedule_name, row.student)
			invoice = frappe.get_doc("Sales Invoice", name)
			if invoice.docstatus == 0:
				invoice.submit()
			invoice_names.append(name)

	return invoice_names


def create_mobile_money_provider():
	if frappe.db.exists("Mobile Money Provider", MOBILE_MONEY_PROVIDER_NAME):
		return MOBILE_MONEY_PROVIDER_NAME

	frappe.get_doc(
		{
			"doctype": "Mobile Money Provider",
			"provider_name": MOBILE_MONEY_PROVIDER_NAME,
			"provider_code": "Orange Money",
			"is_active": 1,
			"sandbox_mode": 1,
			"mode_of_payment": "Orange Money",
			"currency": "XOF",
			"webhook_secret": "demo-webhook-secret-do-not-use-in-production",
		}
	).insert(ignore_permissions=True)
	return MOBILE_MONEY_PROVIDER_NAME


def seed_payments(invoice_names, provider):
	"""Demonstrate every payment channel the demo is meant to show off: the
	first invoice paid in cash (Payment Entry), the second paid through a
	simulated Mobile Money round-trip (initiate -> webhook -> Payment Entry,
	the exact flow a real Orange Money/Moov Money integration would drive),
	and any remaining invoice left outstanding on purpose so "outstanding
	fees" reporting has something real to show.
	"""
	summary = {"cash": None, "mobile_money": None, "outstanding": []}
	if not invoice_names:
		return summary

	cash_invoice = frappe.get_doc("Sales Invoice", invoice_names[0])
	if cash_invoice.docstatus == 1 and cash_invoice.outstanding_amount:
		summary["cash"] = _pay_in_cash(cash_invoice)
	elif cash_invoice.docstatus == 1:
		summary["cash"] = "already paid"

	if len(invoice_names) > 1:
		mm_invoice_name = invoice_names[1]
		summary["mobile_money"] = _pay_by_mobile_money(mm_invoice_name, provider)

	for name in invoice_names[2:]:
		outstanding = frappe.db.get_value("Sales Invoice", name, "outstanding_amount")
		if outstanding:
			summary["outstanding"].append(name)

	return summary


def _pay_in_cash(invoice):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	pe = get_payment_entry("Sales Invoice", invoice.name, party_amount=invoice.outstanding_amount)
	pe.mode_of_payment = "Espèces"
	pe.reference_no = f"CASH-{invoice.name}"
	pe.reference_date = frappe.utils.nowdate()
	pe.insert(ignore_permissions=True)
	pe.submit()
	return pe.name


def _pay_by_mobile_money(invoice_name, provider):
	from burkina_education.finance.mobile_money import api

	existing = frappe.db.get_value(
		"Mobile Money Transaction", {"reference_name": invoice_name, "status": "Success"}, "name"
	)
	if existing:
		return existing

	invoice = frappe.get_doc("Sales Invoice", invoice_name)
	if invoice.docstatus != 1 or not invoice.outstanding_amount:
		return None

	result = api.initiate_payment(
		reference_doctype="Sales Invoice",
		reference_name=invoice_name,
		provider=provider,
		phone_number="+22670000099",
	)
	gateway_id = frappe.db.get_value(
		"Mobile Money Transaction", result["transaction"], "gateway_transaction_id"
	)
	provider_doc = frappe.get_doc("Mobile Money Provider", provider)
	secret = provider_doc.get_password("webhook_secret")
	outcome = api.webhook(
		provider=provider, gateway_transaction_id=gateway_id, status="SUCCESS", signature=secret
	)
	return outcome.get("transaction")


# ---------------------------------------------------------------------------
# Phase 4 - Communication
# ---------------------------------------------------------------------------

MESSAGING_PROVIDERS = [
	# (provider_name, channel, sender_id)
	("SMS Bac à Sable", "SMS", "EPB"),
	("WhatsApp Bac à Sable", "WhatsApp", "+22670000000"),
]

# (template_name, event_key, channel, body). All sandbox/demo copy - a real
# school edits these (Notification Template list) to its own wording,
# nothing here is read by any code path other than communication.notify.
NOTIFICATION_TEMPLATES = [
	(
		"Absence - SMS",
		"Absence Notification",
		"SMS",
		"Bonjour {{ guardian_name }}, {{ student_name }} a un taux de présence de "
		"{{ attendance_percentage }}% (seuil {{ threshold }}%) entre le {{ from_date }} "
		"et le {{ to_date }}. École Pilote Burkina.",
	),
	(
		"Paiement confirmé - SMS",
		"Payment Confirmation",
		"SMS",
		"Bonjour {{ guardian_name }}, nous confirmons la réception de {{ amount }} pour "
		"{{ student_name }} (réf {{ reference }}). Solde restant : {{ balance }}. Merci.",
	),
	(
		"Rappel de frais - SMS",
		"Fee Reminder",
		"SMS",
		"Bonjour {{ guardian_name }}, la facture {{ invoice }} de {{ student_name }} "
		"({{ amount }}) est en retard depuis le {{ due_date }}. Merci de régulariser.",
	),
	(
		"Résultat disponible - SMS",
		"Result Available",
		"SMS",
		"Bonjour {{ guardian_name }}, le bulletin de {{ student_name }} pour "
		"{{ academic_term }} est disponible (moyenne : {{ term_average }}). "
		"Consultez l'espace parent.",
	),
	(
		"Réunion parents - SMS",
		"Parent Meeting",
		"SMS",
		"Bonjour {{ guardian_name }}, une réunion concernant {{ student_name }} est "
		"prévue le {{ date }} à {{ location }}.",
	),
	(
		"Changement d'emploi du temps - SMS",
		"Timetable Change",
		"SMS",
		"Bonjour {{ guardian_name }}, changement d'emploi du temps pour "
		"{{ student_name }} : {{ description }}.",
	),
	(
		"Annonce - SMS",
		"School Announcement",
		"SMS",
		"École Pilote Burkina : {{ title }}",
	),
	(
		"Message urgent - SMS",
		"Emergency Message",
		"SMS",
		"URGENT - École Pilote Burkina : {{ title }} - {{ content }}",
	),
	(
		"Livre en retard - SMS",
		"Library Book Overdue",
		"SMS",
		"Bonjour {{ guardian_name }}, le livre « {{ book_title }} » emprunté par "
		"{{ student_name }} devait être rendu le {{ due_date }}. Merci de le "
		"retourner à la bibliothèque. École Pilote Burkina.",
	),
]

PORTAL_GUARDIAN = "Issa Ouédraogo"
PORTAL_STUDENT = "Amadou Ouédraogo"

ANNOUNCEMENT_TITLE = "Réunion de rentrée - Trimestre 1"


def create_messaging_providers():
	for provider_name, channel, sender_id in MESSAGING_PROVIDERS:
		if frappe.db.exists("Messaging Provider", provider_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Messaging Provider",
				"provider_name": provider_name,
				"channel": channel,
				"provider_code": "Generic HTTP",
				"is_active": 1,
				"sandbox_mode": 1,
				"is_default": 1,
				"sender_id": sender_id,
			}
		).insert(ignore_permissions=True)


def create_notification_templates():
	for template_name, event_key, channel, body in NOTIFICATION_TEMPLATES:
		if frappe.db.exists("Notification Template", template_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Notification Template",
				"template_name": template_name,
				"event_key": event_key,
				"channel": channel,
				"language": "fr",
				"is_active": 1,
				"body": body,
			}
		).insert(ignore_permissions=True)


def create_portal_users():
	"""Promote one demo Guardian and one demo Student to real portal Users
	(communication.portal.invite_*) so the Guardian/Student Portals have
	something real to log into - without this, every Guardian/Student
	created above is Desk-invisible data only (Education Settings.
	user_creation_skip is on for the whole demo seed, see create_students())."""
	from burkina_education.messaging.portal import invite_guardian, invite_student

	result = {}

	guardian_name = frappe.db.get_value("Guardian", {"guardian_name": PORTAL_GUARDIAN}, "name")
	if guardian_name:
		guardian = frappe.get_doc("Guardian", guardian_name)
		if not guardian.email_address:
			guardian.db_set("email_address", "issa.ouedraogo@epb-demo.bf")
		result["guardian_user"] = invite_guardian(guardian_name)

	student_name = frappe.db.get_value("Student", {"student_name": PORTAL_STUDENT}, "name")
	if student_name:
		result["student_user"] = invite_student(student_name)

	return result


def create_demo_announcement():
	if frappe.db.exists("Announcement", {"title": ANNOUNCEMENT_TITLE}):
		return frappe.db.get_value("Announcement", {"title": ANNOUNCEMENT_TITLE}, "name")

	doc = frappe.get_doc(
		{
			"doctype": "Announcement",
			"title": ANNOUNCEMENT_TITLE,
			"content": (
				"<p>Chers parents,</p><p>La réunion de rentrée du Trimestre 1 se tiendra "
				"la semaine prochaine. Merci de consulter l'espace parent pour les détails "
				"de votre classe.</p>"
			),
			"priority": "Normal",
			"audience_type": "All Guardians",
			"start_date": frappe.utils.nowdate(),
			"notify_in_app": 1,
			"notify_sms": 1,
		}
	).insert(ignore_permissions=True)
	doc.publish()
	return doc.name


# ---------------------------------------------------------------------------
# Phase 5 (Operations): Discipline, Clinic, Library, Transport, Assets,
# Canteen, Boarding - see docs/architecture.md section K.
# ---------------------------------------------------------------------------

DEMO_STUDENT_DISCIPLINE = "Amadou Ouédraogo"
DEMO_STUDENT_CLINIC = "Aïcha Ouédraogo"

# (title, author, category, isbn, copy count)
LIBRARY_BOOKS = [
	("Une si longue lettre", "Mariama Bâ", "Littérature", "978-2-7087-0264-4", 2),
	("Les Bouts de bois de Dieu", "Ousmane Sembène", "Littérature", "978-2-253-00595-7", 1),
	("Mathématiques 6ème", "Ministère de l'Éducation", "Manuel scolaire", None, 3),
]

TRANSPORT_ROUTE_NAME = "Ligne Centre-Ville"


def create_disciplinary_case_demo():
	student = frappe.db.get_value("Student", {"student_name": DEMO_STUDENT_DISCIPLINE}, "name")
	if not student:
		return None
	existing = frappe.db.get_value("Disciplinary Case", {"student": student}, "name")
	if existing:
		return existing

	case = frappe.get_doc(
		{
			"doctype": "Disciplinary Case",
			"student": student,
			"incident_type": "Retard",
			"severity": "Mineure",
			"description": "Arrivée 20 minutes en retard, sans justificatif.",
			"action_taken": "Avertissement oral, information portée au carnet de correspondance.",
		}
	).insert(ignore_permissions=True)
	return case.name


def create_clinic_visit_demo():
	student = frappe.db.get_value("Student", {"student_name": DEMO_STUDENT_CLINIC}, "name")
	if not student:
		return None
	existing = frappe.db.get_value("Clinic Visit", {"student": student}, "name")
	if existing:
		return existing

	visit = frappe.get_doc(
		{
			"doctype": "Clinic Visit",
			"student": student,
			"complaint": "Maux de tête et légère fièvre.",
			"treatment": "Paracétamol, repos à l'infirmerie.",
			"parent_notified": 1,
		}
	).insert(ignore_permissions=True)
	return visit.name


def create_library_demo():
	"""Book catalog with copies, plus one active Library Membership + one
	open loan for the demo scholarship student (exercises the borrow flow on
	real demo data, not only in tests)."""
	for title, author_name, category_name, isbn, copies in LIBRARY_BOOKS:
		if not frappe.db.exists("Library Author", author_name):
			frappe.get_doc({"doctype": "Library Author", "author_name": author_name}).insert(
				ignore_permissions=True
			)
		if not frappe.db.exists("Library Category", category_name):
			frappe.get_doc({"doctype": "Library Category", "category_name": category_name}).insert(
				ignore_permissions=True
			)

		book_name = frappe.db.get_value("Library Book", {"title": title}, "name")
		if not book_name:
			book = frappe.get_doc(
				{
					"doctype": "Library Book",
					"title": title,
					"author": author_name,
					"category": category_name,
					"isbn": isbn,
				}
			).insert(ignore_permissions=True)
			book_name = book.name

		existing_copies = frappe.db.count("Library Book Copy", {"book": book_name})
		for _i in range(existing_copies, copies):
			frappe.get_doc({"doctype": "Library Book Copy", "book": book_name}).insert(
				ignore_permissions=True
			)

	student = frappe.db.get_value("Student", {"student_name": SCHOLARSHIP_STUDENT}, "name")
	if not student:
		return None

	membership_name = frappe.db.get_value("Library Membership", {"student": student}, "name")
	if not membership_name:
		membership = frappe.get_doc({"doctype": "Library Membership", "student": student}).insert(
			ignore_permissions=True
		)
		membership_name = membership.name

	has_open_loan = frappe.db.exists(
		"Library Transaction", {"membership": membership_name, "status": ["in", ("Emprunté", "En retard")]}
	)
	if not has_open_loan:
		book_name = frappe.db.get_value("Library Book", {"title": LIBRARY_BOOKS[0][0]}, "name")
		available_copy = frappe.db.get_value(
			"Library Book Copy", {"book": book_name, "status": "Disponible"}, "name"
		)
		if available_copy:
			frappe.get_doc(
				{
					"doctype": "Library Transaction",
					"membership": membership_name,
					"book_copy": available_copy,
				}
			).insert(ignore_permissions=True)

	return membership_name


def create_transport_demo():
	if not frappe.db.exists("Transport Route", TRANSPORT_ROUTE_NAME):
		frappe.get_doc(
			{
				"doctype": "Transport Route",
				"route_name": TRANSPORT_ROUTE_NAME,
				"distance_km": 8.5,
				"stops": [
					{"stop_name": "Place de la Nation", "pickup_time": "06:30:00", "drop_time": "16:30:00"},
					{"stop_name": "Marché Sankaryaré", "pickup_time": "06:45:00", "drop_time": "16:15:00"},
				],
			}
		).insert(ignore_permissions=True)

	student = frappe.db.get_value("Student", {"student_name": DEMO_STUDENT_DISCIPLINE}, "name")
	if student and not frappe.db.exists("Student Transport Assignment", {"student": student}):
		frappe.get_doc(
			{
				"doctype": "Student Transport Assignment",
				"student": student,
				"route": TRANSPORT_ROUTE_NAME,
				"stop_name": "Place de la Nation",
			}
		).insert(ignore_permissions=True)

	return TRANSPORT_ROUTE_NAME


def create_asset_categories_demo(company):
	"""Seed data only (master.md §43) - ``Asset Category.accounts`` needs a
	real Company/chart of accounts, hence this runs after ``create_company()``
	rather than at install time (docs/architecture.md section K, and
	inventory/setup.py's own docstring)."""
	from burkina_education.inventory.setup import seed_asset_categories

	if not company:
		return []
	return seed_asset_categories(company)


def create_canteen_demo():
	plan_name = "Formule Complète"
	if not frappe.db.exists("Meal Plan", plan_name):
		frappe.get_doc(
			{
				"doctype": "Meal Plan",
				"plan_name": plan_name,
				"price_per_month": 20000,
				"description": "Petit-déjeuner, déjeuner et goûter, du lundi au vendredi.",
			}
		).insert(ignore_permissions=True)

	student = frappe.db.get_value("Student", {"student_name": SCHOLARSHIP_STUDENT}, "name")
	if not student:
		return None

	subscription_name = frappe.db.get_value("Canteen Subscription", {"student": student}, "name")
	if not subscription_name:
		subscription = frappe.get_doc(
			{"doctype": "Canteen Subscription", "student": student, "meal_plan": plan_name}
		).insert(ignore_permissions=True)
		subscription_name = subscription.name

	if not frappe.db.exists("Meal Consumption", {"subscription": subscription_name}):
		frappe.get_doc(
			{"doctype": "Meal Consumption", "subscription": subscription_name}
		).insert(ignore_permissions=True)

	return subscription_name


def create_boarding_demo():
	building_name = "Internat Filles"
	if not frappe.db.exists("Boarding Building", building_name):
		frappe.get_doc({"doctype": "Boarding Building", "building_name": building_name}).insert(
			ignore_permissions=True
		)

	room_name = f"{building_name}-101"
	if not frappe.db.exists("Boarding Room", room_name):
		frappe.get_doc(
			{
				"doctype": "Boarding Room",
				"building": building_name,
				"room_number": "101",
				"capacity": 4,
			}
		).insert(ignore_permissions=True)

	bed_name = f"{room_name}-A"
	if not frappe.db.exists("Boarding Bed", bed_name):
		frappe.get_doc({"doctype": "Boarding Bed", "room": room_name, "bed_number": "A"}).insert(
			ignore_permissions=True
		)

	student = frappe.db.get_value("Student", {"student_name": DEMO_STUDENT_CLINIC}, "name")
	if not student:
		return None
	existing = frappe.db.get_value("Student Boarding Assignment", {"student": student}, "name")
	if existing:
		return existing

	assignment = frappe.get_doc(
		{"doctype": "Student Boarding Assignment", "student": student, "bed": bed_name}
	).insert(ignore_permissions=True)
	return assignment.name
