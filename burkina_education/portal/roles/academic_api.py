# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Academic Portal, shared by four roles whose
real permissions nest inside one another (docs/architecture.md section M):

- Registrar: Campus / Cycle / Education Level / Grade only (academic
  reference-data setup).
- Examination Coordinator: Examination / Examination Schedule only.
- Department Head: Competency / Learning Unit / Lesson / Learning Objective
  (read-write) plus Curriculum / Course (read-only) - the same authoring
  rights Instructor already has, not Academic Director's full set (see
  docs/architecture.md section N).
- Academic Director: all of the above, plus write access to Curriculum,
  Grading Scheme, Assessment Type, Disciplinary Case, Scholarship, School,
  Announcement, Student Term/Annual Report, and Burkina Education Settings.

Every doctype above is plain, non-ownership-scoped CRUD the frontend does
directly via generic list/document resources; ``get_dashboard`` is the only
custom endpoint, and shapes its response to whichever of the four roles the
caller actually holds rather than assuming Academic Director's full set.
"""

import frappe

from burkina_education.portal.permissions import require_any_role

ACADEMIC_ROLES = ("Registrar", "Academic Director", "Examination Coordinator", "Department Head")


@frappe.whitelist()
def get_dashboard():
	require_any_role(*ACADEMIC_ROLES)
	roles = set(frappe.get_roles())
	is_director = "Academic Director" in roles
	has_structure = is_director or "Registrar" in roles
	has_exams = is_director or "Examination Coordinator" in roles
	has_pedagogy = is_director or "Department Head" in roles

	out = {
		"is_director": is_director,
		"has_structure": has_structure,
		"has_exams": has_exams,
		"has_pedagogy": has_pedagogy,
	}

	if has_pedagogy:
		out["pedagogy"] = {
			"curriculum_count": frappe.db.count("Curriculum"),
			"competency_count": frappe.db.count("Competency"),
			"lesson_count": frappe.db.count("Lesson"),
		}

	if has_structure:
		out["structure"] = {
			"campuses": frappe.db.count("Campus"),
			"cycles": frappe.db.count("Cycle"),
			"education_levels": frappe.db.count("Education Level"),
			"grades": frappe.db.count("Grade"),
		}

	if has_exams:
		out["exams"] = {
			"upcoming": frappe.get_all(
				"Examination",
				filters={"status": ["in", ("Scheduled", "Ongoing")]},
				fields=["name", "examination_name", "exam_type", "from_date", "to_date", "status"],
				order_by="from_date asc",
				limit=8,
			),
			"schedules_this_week": frappe.db.count(
				"Examination Schedule",
				{"exam_date": ["between", (frappe.utils.nowdate(), frappe.utils.add_days(frappe.utils.nowdate(), 7))]},
			),
		}

	if is_director:
		out["director"] = {
			"open_discipline_cases": frappe.db.count("Disciplinary Case", {"status": ["!=", "Résolu"]}),
			"pending_scholarships": frappe.db.count("Scholarship", {"status": "Brouillon"}),
			"published_announcements": frappe.db.count("Announcement", {"publication_status": "Published"}),
			"draft_announcements": frappe.db.count("Announcement", {"publication_status": "Draft"}),
			"term_reports_this_year": frappe.db.count("Student Term Report", {"docstatus": 1}),
			"curriculum_count": frappe.db.count("Curriculum"),
			"lesson_count": frappe.db.count("Lesson"),
		}

	return out
