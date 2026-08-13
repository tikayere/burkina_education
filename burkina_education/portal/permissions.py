# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Server-side identity/ownership helpers shared by the three Vue portals
(``portal/student_api.py``, ``portal/guardian_api.py``, ``portal/teacher_api.py``).

Same philosophy as ``messaging/permissions.py`` (master.md §54/§77: "never
rely exclusively on frontend permissions") — every whitelisted portal
function re-derives the caller's own Guardian/Student/Instructor identity
from ``frappe.session.user`` and re-checks ownership of whatever record it's
about to return, rather than trusting a client-supplied id for *whose* data
to fetch. Read-heavy aggregate views here (Discipline/Clinic/Library/
Transport/Canteen/Boarding for a specific student) are served with
``ignore_permissions=True`` *after* that explicit ownership check — a single
well-tested checkpoint per function — rather than adding six more Custom
DocPerm + ``has_permission`` hook pairs (the layered approach
``messaging/permissions.py`` uses for the doctypes Desk list views also read
directly). See docs/architecture.md section L for the rationale.
"""

from contextlib import contextmanager

import frappe

from burkina_education.messaging.permissions import get_student_for_user, get_students_for_guardian_user

__all__ = [
	"elevated",
	"get_student_for_user",
	"get_students_for_guardian_user",
	"require_student",
	"require_guardian_students",
	"require_own_student",
	"get_instructor_for_user",
	"require_instructor",
	"get_groups_for_instructor",
	"require_group_taught_by_instructor",
	"is_class_teacher",
	"get_students_in_groups",
]


def require_student(user=None):
	student = get_student_for_user(user)
	if not student:
		frappe.throw(frappe._("Aucun compte élève n'est associé à cet utilisateur."), frappe.PermissionError)
	return student


def require_guardian_students(user=None):
	students = get_students_for_guardian_user(user)
	if not students:
		frappe.throw(frappe._("Aucun compte tuteur n'est associé à cet utilisateur."), frappe.PermissionError)
	return students


def require_own_student(student, user=None):
	"""Guardian variant of ``require_student``: throws unless ``student`` is
	one of the caller's own linked children."""
	students = require_guardian_students(user)
	if student not in students:
		frappe.throw(frappe._("Vous n'avez pas accès à cet élève."), frappe.PermissionError)
	return student


def get_instructor_for_user(user=None):
	"""Instructor has no ``user`` link of its own - only ``employee``, and
	Employee is the doctype that actually carries ``user_id`` (standard
	ERPNext field). Walking User -> Employee -> Instructor is the only
	reliable chain; see the fix to ``messaging/doctype/announcement/
	announcement.py::_teacher_users()`` (docs/architecture.md section L) for
	a real bug this same wrong assumption caused elsewhere in the app.
	"""
	user = user or frappe.session.user
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		return None
	return frappe.db.get_value("Instructor", {"employee": employee}, "name")


def require_instructor(user=None):
	instructor = get_instructor_for_user(user)
	if not instructor:
		frappe.throw(frappe._("Aucun compte enseignant n'est associé à cet utilisateur."), frappe.PermissionError)
	return instructor


def get_groups_for_instructor(instructor):
	"""Every active Student Group this Instructor appears in (subject
	teacher or class teacher alike - Education doesn't distinguish the two
	at the group level, only via the separate "Class Teacher" Role, see
	``is_class_teacher``)."""
	return frappe.get_all(
		"Student Group Instructor",
		filters={"instructor": instructor, "parenttype": "Student Group"},
		pluck="parent",
	)


def require_group_taught_by_instructor(student_group, instructor):
	if student_group not in get_groups_for_instructor(instructor):
		frappe.throw(frappe._("Vous n'enseignez pas dans cette classe/section."), frappe.PermissionError)
	return student_group


def is_class_teacher(user=None):
	""""Class Teacher" is a plain Role (master.md), not a per-group flag -
	whoever holds it can see Discipline records for any student, same as
	Academic Director/School Director (docs/architecture.md section K)."""
	user = user or frappe.session.user
	return "Class Teacher" in frappe.get_roles(user)


def get_students_in_groups(groups, active_only=True):
	if not groups:
		return []
	filters = {"parent": ["in", groups]}
	if active_only:
		filters["active"] = 1
	rows = frappe.get_all(
		"Student Group Student", filters=filters, fields=["student", "student_name", "parent", "group_roll_number"]
	)
	# De-duplicate a student who appears in >1 group taught by the same
	# instructor (e.g. two subjects in the same section) while keeping the
	# first group_roll_number/parent seen.
	seen = {}
	for row in rows:
		seen.setdefault(row.student, row)
	return list(seen.values())


@contextmanager
def elevated():
	"""Temporarily run as Administrator - for the *write* half of a
	teacher_api.py mutation, after its own ownership check
	(``require_group_taught_by_instructor`` etc.) has already passed.

	``doc.flags.ignore_permissions`` (used throughout portal/common.py's
	*reads*) only covers Frappe's own insert/save/submit permission checks
	on that one document - it does nothing for ad hoc permission-checked
	queries a doctype's own controller runs internally (Education's
	``Assessment Result.validate()`` does exactly this, calling
	``frappe.db.get_value`` - which re-checks ``frappe.has_permission``
	against the *real* session user regardless of any flag - to guard
	against a duplicate result). Becoming Administrator for the duration is
	the only mechanism ``frappe.has_permission`` itself unconditionally
	honours (see ``frappe/permissions.py::has_permission``'s very first
	check), so it's what covers those nested calls too - a normal Instructor
	Desk user hits the same internal query, just under a role/User
	Permission grant this portal's own ownership check already substitutes
	for.
	"""
	user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		yield
	finally:
		frappe.set_user(user)
