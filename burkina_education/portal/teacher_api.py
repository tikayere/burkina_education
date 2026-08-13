# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Teacher Portal (``frontend/``, route
``/portal``). docs/architecture.md section J originally chose a Desk
Workspace ("Espace Enseignant") over a website portal for teachers, since
Desk already covers attendance/marks entry; this module builds the
requested Vue equivalent on top of the *same* underlying doctypes
(Student Group, Student Attendance, Assessment Plan/Result, Disciplinary
Case), not a parallel data model — see docs/architecture.md section L.

Every function re-derives the caller's own Instructor identity
(``portal/permissions.py::require_instructor``) and, for anything scoped to
one Student Group, re-checks that this Instructor actually teaches it
(``require_group_taught_by_instructor``) before reading or writing.
"""

import frappe
from frappe.utils import flt, nowdate

from burkina_education.messaging.doctype.announcement.announcement import get_visible_announcements
from burkina_education.messaging.notify import notify_event
from burkina_education.portal import permissions

SUBMITTABLE_ATTENDANCE_STATUSES = ("Present", "Absent", "Late", "Excused", "Leave")


# ---------------------------------------------------------------------------
# Identity / dashboard
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_dashboard():
	instructor = permissions.require_instructor()
	groups = permissions.get_groups_for_instructor(instructor)
	students = permissions.get_students_in_groups(groups)

	today_schedule = frappe.get_all(
		"Course Schedule",
		filters={"instructor": instructor, "schedule_date": nowdate()},
		fields=["name", "student_group", "course", "room", "from_time", "to_time"],
		order_by="from_time asc",
		ignore_permissions=True,
	)

	open_cases = 0
	if permissions.is_class_teacher():
		student_names = [s.student for s in students]
		if student_names:
			open_cases = frappe.db.count(
				"Disciplinary Case", {"student": ["in", student_names], "status": ["!=", "Résolu"]}
			)

	return {
		"instructor": frappe.db.get_value(
			"Instructor", instructor, ["instructor_name", "image", "department"], as_dict=True
		),
		"is_class_teacher": permissions.is_class_teacher(),
		"groups_count": len(groups),
		"students_count": len(students),
		"today_schedule": today_schedule,
		"open_discipline_cases": open_cases,
		"announcements": _filter_announcements_for_instructor(get_visible_announcements(limit=20), groups)[:5],
	}


@frappe.whitelist()
def get_groups():
	instructor = permissions.require_instructor()
	groups = permissions.get_groups_for_instructor(instructor)
	if not groups:
		return []
	rows = frappe.get_all(
		"Student Group",
		filters={"name": ["in", groups]},
		fields=["name", "student_group_name", "program", "academic_year", "academic_term", "max_strength", "disabled"],
		ignore_permissions=True,
	)
	for row in rows:
		row["student_count"] = frappe.db.count("Student Group Student", {"parent": row.name, "active": 1})
		row["grade"] = frappe.db.get_value("Grade", {"program": row.program}, "name") if row.program else None
		row["grade_name"] = frappe.db.get_value("Grade", row.grade, "grade_name") if row.get("grade") else None
	return rows


@frappe.whitelist()
def get_group_students(student_group):
	instructor = permissions.require_instructor()
	permissions.require_group_taught_by_instructor(student_group, instructor)
	return frappe.get_all(
		"Student Group Student",
		filters={"parent": student_group, "active": 1},
		fields=["student", "student_name", "group_roll_number"],
		order_by="group_roll_number asc, student_name asc",
		ignore_permissions=True,
	)


@frappe.whitelist()
def get_schedule(from_date=None, to_date=None):
	instructor = permissions.require_instructor()
	from_date = from_date or nowdate()
	to_date = to_date or frappe.utils.add_days(from_date, 14)
	return frappe.get_all(
		"Course Schedule",
		filters={"instructor": instructor, "schedule_date": ["between", (from_date, to_date)]},
		fields=["name", "student_group", "course", "room", "schedule_date", "from_time", "to_time"],
		order_by="schedule_date asc, from_time asc",
		ignore_permissions=True,
	)


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_attendance_sheet(student_group, date):
	instructor = permissions.require_instructor()
	permissions.require_group_taught_by_instructor(student_group, instructor)
	roster = get_group_students(student_group)
	existing = {
		r.student: r
		for r in frappe.get_all(
			"Student Attendance",
			filters={"student_group": student_group, "date": date, "docstatus": 1},
			fields=["name", "student", "status", "remarks"],
			ignore_permissions=True,
		)
	}
	for row in roster:
		record = existing.get(row.student)
		row["attendance_name"] = record.name if record else None
		row["status"] = record.status if record else None
		row["remarks"] = record.remarks if record else None
	return roster


@frappe.whitelist()
def mark_attendance(student_group, date, records):
	"""``records``: list of ``{student, status, remarks}``. Idempotent per
	student/date - an unchanged status is a no-op, a changed one cancels the
	previous submitted record and inserts+submits a fresh one (Student
	Attendance is a submittable doctype, so a plain update isn't allowed
	once locked)."""
	instructor = permissions.require_instructor()
	permissions.require_group_taught_by_instructor(student_group, instructor)

	if isinstance(records, str):
		records = frappe.parse_json(records)

	roster = {r.student for r in permissions.get_students_in_groups([student_group])}
	result = {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0}

	with permissions.elevated():
		for record in records:
			student = record.get("student")
			status = record.get("status")
			if student not in roster or status not in SUBMITTABLE_ATTENDANCE_STATUSES:
				result["skipped"] += 1
				continue

			existing = frappe.db.get_value(
				"Student Attendance",
				{"student": student, "student_group": student_group, "date": date, "docstatus": 1},
				["name", "status"],
				as_dict=True,
			)
			if existing and existing.status == status:
				result["unchanged"] += 1
				continue
			if existing:
				old = frappe.get_doc("Student Attendance", existing.name)
				old.cancel()
				result["updated"] += 1
			else:
				result["created"] += 1

			doc = frappe.get_doc(
				{
					"doctype": "Student Attendance",
					"student": student,
					"student_group": student_group,
					"date": date,
					"status": status,
					"remarks": record.get("remarks"),
				}
			)
			doc.insert()
			doc.submit()

	return result


# ---------------------------------------------------------------------------
# Gradebook
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_assessment_plans(student_group=None):
	instructor = permissions.require_instructor()
	groups = permissions.get_groups_for_instructor(instructor)
	if student_group:
		permissions.require_group_taught_by_instructor(student_group, instructor)
		groups = [student_group]
	if not groups:
		return []
	return frappe.get_all(
		"Assessment Plan",
		filters={"student_group": ["in", groups]},
		fields=["name", "assessment_name", "student_group", "course", "schedule_date", "maximum_assessment_score"],
		order_by="schedule_date desc",
		ignore_permissions=True,
	)


@frappe.whitelist()
def get_assessment_result_sheet(assessment_plan):
	instructor = permissions.require_instructor()
	plan = frappe.get_doc("Assessment Plan", assessment_plan)
	permissions.require_group_taught_by_instructor(plan.student_group, instructor)

	criteria = [
		{"assessment_criteria": c.assessment_criteria, "maximum_score": c.maximum_score}
		for c in plan.assessment_criteria
	]
	roster = get_group_students(plan.student_group)
	existing = {
		r.student: r
		for r in frappe.get_all(
			"Assessment Result",
			filters={"assessment_plan": assessment_plan},
			fields=["name", "student", "total_score", "grade", "comment", "docstatus"],
			ignore_permissions=True,
		)
	}
	for row in roster:
		result = existing.get(row.student)
		if result:
			row.update(
				{
					"result_name": result.name,
					"total_score": result.total_score,
					"grade": result.grade,
					"comment": result.comment,
					"submitted": result.docstatus == 1,
					"details": frappe.get_all(
						"Assessment Result Detail",
						filters={"parent": result.name},
						fields=["assessment_criteria", "maximum_score", "score"],
						ignore_permissions=True,
					),
				}
			)
		else:
			row.update({"result_name": None, "total_score": None, "submitted": False, "details": []})

	return {
		"plan": {
			"name": plan.name,
			"assessment_name": plan.assessment_name,
			"course": plan.course,
			"maximum_assessment_score": plan.maximum_assessment_score,
			"criteria": criteria,
		},
		"roster": roster,
	}


@frappe.whitelist()
def save_assessment_results(assessment_plan, results):
	"""``results``: list of ``{student, details: [{assessment_criteria, score}], comment}``.
	Only ever touches draft (unsubmitted) Assessment Result rows - a
	submitted one is locked per docs/architecture.md section G and must be
	amended by an authorized role via ``guard_assessment_result_cancel``,
	not silently rewritten here."""
	instructor = permissions.require_instructor()
	plan = frappe.get_doc("Assessment Plan", assessment_plan)
	permissions.require_group_taught_by_instructor(plan.student_group, instructor)

	if isinstance(results, str):
		results = frappe.parse_json(results)

	roster = {r.student for r in permissions.get_students_in_groups([plan.student_group])}
	saved, locked, skipped = [], [], []

	with permissions.elevated():
		for entry in results:
			student = entry.get("student")
			if student not in roster:
				skipped.append(student)
				continue

			details = entry.get("details") or []
			total_score = sum(flt(d.get("score")) for d in details)

			existing_name = frappe.db.get_value(
				"Assessment Result", {"assessment_plan": assessment_plan, "student": student}, "name"
			)
			if existing_name:
				doc = frappe.get_doc("Assessment Result", existing_name)
				if doc.docstatus == 1:
					locked.append(student)
					continue
				doc.set("details", [])
			else:
				doc = frappe.get_doc(
					{
						"doctype": "Assessment Result",
						"assessment_plan": assessment_plan,
						"student": student,
						"program": plan.program,
						"course": plan.course,
						"academic_year": plan.academic_year,
						"academic_term": plan.academic_term,
						"student_group": plan.student_group,
						"assessment_group": plan.assessment_group,
						"grading_scale": plan.grading_scale,
						"maximum_score": plan.maximum_assessment_score,
					}
				)

			for detail in details:
				doc.append(
					"details",
					{
						"assessment_criteria": detail.get("assessment_criteria"),
						"maximum_score": detail.get("maximum_score"),
						"score": flt(detail.get("score")),
					},
				)
			doc.total_score = total_score
			doc.comment = entry.get("comment")
			doc.save()
			saved.append(student)

	return {"saved": saved, "locked": locked, "skipped": skipped}


@frappe.whitelist()
def submit_assessment_result(name):
	instructor = permissions.require_instructor()
	doc = frappe.get_doc("Assessment Result", name)
	permissions.require_group_taught_by_instructor(doc.student_group, instructor)
	with permissions.elevated():
		doc.submit()
	return doc.name


# ---------------------------------------------------------------------------
# Discipline (Class Teacher role only - master.md §37, docs/architecture.md
# section K: Instructor alone, without the Class Teacher role, has no access)
# ---------------------------------------------------------------------------


def _require_class_teacher():
	if not permissions.is_class_teacher():
		frappe.throw(
			frappe._("Cette fonctionnalité est réservée aux professeurs principaux (Class Teacher)."),
			frappe.PermissionError,
		)


@frappe.whitelist()
def get_discipline_cases(student_group=None):
	_require_class_teacher()
	instructor = permissions.require_instructor()
	filters = {}
	if student_group:
		permissions.require_group_taught_by_instructor(student_group, instructor)
		students = [s.student for s in permissions.get_students_in_groups([student_group])]
		filters["student"] = ["in", students or [""]]
	return frappe.get_all(
		"Disciplinary Case",
		filters=filters,
		fields=["name", "student", "student_name", "date", "incident_type", "severity", "status"],
		order_by="date desc",
		limit=100,
	)


@frappe.whitelist()
def create_discipline_case(student, incident_type, severity, description, action_taken=None, date=None):
	_require_class_teacher()
	doc = frappe.get_doc(
		{
			"doctype": "Disciplinary Case",
			"student": student,
			"date": date or nowdate(),
			"incident_type": incident_type,
			"severity": severity,
			"description": description,
			"action_taken": action_taken,
			"status": "Ouvert",
		}
	)
	doc.insert()  # real Class Teacher Custom DocPerm grant - no ignore_permissions needed
	return doc.name


# ---------------------------------------------------------------------------
# Announcements / messaging
# ---------------------------------------------------------------------------


def _filter_announcements_for_instructor(announcements, groups):
	grades = {
		frappe.db.get_value("Grade", {"program": g.program}, "name")
		for g in frappe.get_all("Student Group", filters={"name": ["in", groups]}, fields=["program"])
		if g.program
	}
	out = []
	for a in announcements:
		if a.audience_type in ("All", "All Teachers"):
			out.append(a)
		elif a.audience_type == "Student Group" and a.audience_reference in groups:
			out.append(a)
		elif a.audience_type == "Grade" and a.audience_reference in grades:
			out.append(a)
	return out


@frappe.whitelist()
def get_announcements(limit=20):
	instructor = permissions.require_instructor()
	groups = permissions.get_groups_for_instructor(instructor)
	all_visible = get_visible_announcements(limit=100)
	return _filter_announcements_for_instructor(all_visible, groups)[: int(limit)]


@frappe.whitelist()
def send_message_to_guardian(student, message, title=None):
	"""Freeform note from a teacher to a student's guardian(s) - reuses the
	existing notification engine (``messaging/notify.py``) rather than a new
	chat/messaging doctype; delivered In-App only (never SMS/WhatsApp
	credits for a teacher's freeform note) to whichever of the student's
	guardians has portal access. Ownership-checked: the student must be in
	one of this Instructor's own Student Groups."""
	instructor = permissions.require_instructor()
	groups = permissions.get_groups_for_instructor(instructor)
	taught_students = {s.student for s in permissions.get_students_in_groups(groups)}
	if student not in taught_students:
		frappe.throw(frappe._("Cet élève n'est dans aucune de vos classes."), frappe.PermissionError)

	guardians = frappe.get_all("Student Guardian", filters={"parent": student}, pluck="guardian")
	if not guardians:
		frappe.throw(frappe._("Aucun tuteur n'est associé à cet élève."))

	instructor_name = frappe.db.get_value("Instructor", instructor, "instructor_name")
	student_name = frappe.db.get_value("Student", student, "student_name")
	summary = notify_event(
		"Other",
		guardians=guardians,
		context={
			"title": title or frappe._("Message de {0}").format(instructor_name),
			"content": message,
			"student_name": student_name,
		},
		channels=["In-App"],
		reference_doctype="Student",
		reference_name=student,
	)
	return summary


@frappe.whitelist()
def get_inbox(limit=50):
	permissions.require_instructor()
	from burkina_education.portal import common

	return common.inbox(frappe.session.user, limit=int(limit))
