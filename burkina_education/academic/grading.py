# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Grading engine glue: the cancel guard on Education's ``Assessment Result``,
and the weighted-average helpers used by ``Student Term Report``/``Student
Annual Report`` (see docs/architecture.md section G).

No formula here is hard-coded per school - everything reads its parameters
from ``Grading Scheme``.
"""

import frappe
from frappe import _

#: Roles allowed to cancel (and therefore amend) a locked Assessment Result.
#: Kept as a hook rather than rewriting the DocType's permissions - see
#: docs/architecture.md section G for why.
ASSESSMENT_RESULT_CANCEL_ROLES = {"Academic Director", "Examination Coordinator", "System Manager"}


def guard_assessment_result_cancel(doc, method=None):
	if frappe.session.user == "Administrator":
		return

	user_roles = set(frappe.get_roles(frappe.session.user))
	if user_roles & ASSESSMENT_RESULT_CANCEL_ROLES:
		return

	frappe.throw(
		_(
			"Marks have already been submitted (locked). Only an Academic Director or "
			"Examination Coordinator can cancel/amend a submitted Assessment Result."
		),
		frappe.PermissionError,
	)


# ---------------------------------------------------------------------------
# Grading Scheme resolution
# ---------------------------------------------------------------------------


def get_education_level_for_grade(grade):
	if not grade:
		return None
	cycle = frappe.db.get_value("Grade", grade, "cycle")
	if not cycle:
		return None
	return frappe.db.get_value("Cycle", cycle, "education_level")


def resolve_grading_scheme(grade=None):
	"""Pick the Grading Scheme to use for a Grade: an Education-Level-scoped
	default if one exists, else the global default (``education_level`` blank).
	Returns None if no scheme has been configured at all - callers must
	handle that (master.md §19: schools configure this, nothing is assumed).
	"""
	education_level = get_education_level_for_grade(grade)
	if education_level:
		scoped = frappe.db.get_value(
			"Grading Scheme", {"education_level": education_level, "is_default": 1, "is_active": 1}
		)
		if scoped:
			return scoped
	# Link fields left unset are stored as NULL (not ""), so "blank" has to be
	# checked with the "is not set" operator rather than an equality filter.
	return frappe.db.get_value(
		"Grading Scheme", {"education_level": ["is", "not set"], "is_default": 1, "is_active": 1}
	)


# ---------------------------------------------------------------------------
# Weighted-average computation
# ---------------------------------------------------------------------------


def compute_subject_results(student, academic_term, use_coefficients=True, score_max=20, rounding=2):
	"""One row per Course with submitted Assessment Results for this student
	in this term: a coefficient-weighted average of all its assessments,
	rescaled to ``score_max``.
	"""
	results = frappe.get_all(
		"Assessment Result",
		filters={"student": student, "academic_term": academic_term, "docstatus": 1},
		fields=["name", "course", "assessment_plan", "total_score", "maximum_score"],
	)
	if not results:
		return []

	plan_names = list({r.assessment_plan for r in results if r.assessment_plan})
	plan_coefficient = {}
	if plan_names:
		for p in frappe.get_all(
			"Assessment Plan", filters={"name": ["in", plan_names]}, fields=["name", "coefficient"]
		):
			plan_coefficient[p.name] = p.coefficient or 1

	course_names = list({r.course for r in results if r.course})
	course_coefficient = {}
	if course_names:
		for c in frappe.get_all("Course", filters={"name": ["in", course_names]}, fields=["name", "coefficient"]):
			course_coefficient[c.name] = c.coefficient or 1

	by_course = {}
	for r in results:
		by_course.setdefault(r.course, []).append(r)

	subject_rows = []
	for course, rows in by_course.items():
		weighted_sum, weight_total = 0.0, 0.0
		for r in rows:
			if not r.maximum_score:
				continue
			scaled = (r.total_score or 0) / r.maximum_score * score_max
			coefficient = plan_coefficient.get(r.assessment_plan, 1) if use_coefficients else 1
			weighted_sum += scaled * coefficient
			weight_total += coefficient

		subject_rows.append(
			{
				"course": course,
				"coefficient": course_coefficient.get(course, 1),
				"subject_average": round(weighted_sum / weight_total, rounding) if weight_total else 0.0,
				"max_score": score_max,
				"assessment_count": len(rows),
			}
		)

	return subject_rows


def compute_term_average(subject_rows, use_coefficients=True, method="Weighted by Coefficient", rounding=2):
	if not subject_rows:
		return 0.0

	if use_coefficients and method == "Weighted by Coefficient":
		weighted_sum = sum(row["subject_average"] * (row["coefficient"] or 1) for row in subject_rows)
		weight_total = sum((row["coefficient"] or 1) for row in subject_rows)
		return round(weighted_sum / weight_total, rounding) if weight_total else 0.0

	return round(sum(row["subject_average"] for row in subject_rows) / len(subject_rows), rounding)


def compute_annual_average(term_rows, method="Weighted by Term Weight", rounding=2):
	if not term_rows:
		return 0.0

	if method == "Weighted by Term Weight":
		weighted_sum = sum(row["term_average"] * (row["weight"] or 1) for row in term_rows)
		weight_total = sum((row["weight"] or 1) for row in term_rows)
		return round(weighted_sum / weight_total, rounding) if weight_total else 0.0

	return round(sum(row["term_average"] for row in term_rows) / len(term_rows), rounding)


# ---------------------------------------------------------------------------
# Attendance summary (used inside a Student Term Report)
# ---------------------------------------------------------------------------


def get_attendance_summary(student, from_date, to_date):
	rows = frappe.get_all(
		"Student Attendance",
		filters={"student": student, "docstatus": 1, "date": ["between", (from_date, to_date)]},
		fields=["status", {"COUNT": "name", "as": "count"}],
		group_by="status",
	)

	summary = {"present": 0, "absent": 0, "late": 0, "excused": 0, "leave": 0, "total": 0}
	for row in rows:
		key = (row.status or "").lower()
		if key in summary:
			summary[key] = row.count
		summary["total"] += row.count

	attended = summary["present"] + summary["late"]
	summary["percentage"] = round(attended / summary["total"] * 100, 2) if summary["total"] else 0.0
	return summary


# ---------------------------------------------------------------------------
# Bulk helper for the report-card workflow / demo data
# ---------------------------------------------------------------------------


@frappe.whitelist()
def generate_term_reports(student_group, academic_term):
	"""Create (if missing) and (re)compute a Student Term Report for every
	active student of ``student_group`` for ``academic_term``. Submitted
	reports are left untouched (they are locked; amend them explicitly).
	"""
	frappe.has_permission("Student Term Report", "create", throw=True)

	academic_year = frappe.db.get_value("Academic Term", academic_term, "academic_year")
	if not academic_year:
		frappe.throw(_("Academic Term {0} has no Academic Year set.").format(academic_term))

	student_rows = frappe.get_all(
		"Student Group Student", filters={"parent": student_group, "active": 1}, fields=["student"]
	)

	report_names = []
	for row in student_rows:
		existing = frappe.db.get_value(
			"Student Term Report", {"student": row.student, "academic_term": academic_term}
		)
		if existing:
			doc = frappe.get_doc("Student Term Report", existing)
			if doc.docstatus != 0:
				report_names.append(doc.name)
				continue
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Student Term Report",
					"student": row.student,
					"student_group": student_group,
					"academic_year": academic_year,
					"academic_term": academic_term,
				}
			).insert(ignore_permissions=True)

		doc.compute()
		report_names.append(doc.name)

	return report_names
