# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Server-side scoping for the Guardian/Student Portals (master.md §29/§30/
§54/§77: "never rely exclusively on frontend permissions" / "a guardian
only sees students they are authorized to access" / "student cannot access
another student's information").

The Desk-facing Custom DocPerm rows (install.py::create_portal_permissions)
grant the ``Guardian``/``Student`` roles a plain **read** permission on a
short list of doctypes so ``/printview`` and the portal's own whitelisted
API calls are allowed through the standard permission system at all. This
module's ``has_permission`` hook (registered per-doctype in hooks.py) then
narrows that down from "any record" to "only records tied to *this*
Guardian's own children / this Student's own record" - Frappe's
``has_permission`` hook can only ever *deny*, never grant (see
``frappe.permissions.has_controller_permissions``), which is exactly the
shape needed here: staff roles keep whatever broader access their own
Custom DocPerm already grants, completely unaffected by this module.
"""

import frappe

#: doctype -> fieldname holding the Student this record belongs to.
STUDENT_LINKED_DOCTYPES = {
	"Student Term Report": "student",
	"Student Annual Report": "student",
	"Student Attendance": "student",
	"Sales Invoice": "student",
}

#: Roles that already have their own, broader access to the doctypes above -
#: this module never restricts them, regardless of the record.
PORTAL_ONLY_ROLES = {"Guardian", "Student"}

#: Roles Frappe assigns to essentially every enabled account regardless of
#: type ("All", "Guest") or that a *System User* account picks up alongside
#: Guardian/Student in this dev environment's test fixtures ("Desk User") -
#: none of these indicate real staff access, so they must not by themselves
#: cause this hook to defer. A real production Guardian/Student is a
#: "Website User" and wouldn't carry "Desk User" at all, but the check is
#: written to be correct either way rather than relying on that.
BASELINE_ROLES = PORTAL_ONLY_ROLES | {"All", "Guest", "Desk User"}


def get_student_for_user(user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Student", {"user": user}, "name")


def get_students_for_guardian_user(user=None):
	user = user or frappe.session.user
	guardian = frappe.db.get_value("Guardian", {"user": user}, "name")
	if not guardian:
		return []
	return frappe.get_all("Student Guardian", filters={"guardian": guardian}, pluck="parent")


def student_scoped_has_permission(doc, ptype="read", user=None, debug=False):
	"""``has_permission`` hook for ``STUDENT_LINKED_DOCTYPES``. Only ever
	narrows access for a user whose *only* relevant roles are Guardian/
	Student (a pure portal user) - anyone with any other role (System
	Manager, Academic Director, Class Teacher, Accountant, ...) is left
	completely alone since they rely on their own Custom DocPerm instead.
	"""
	user = user or frappe.session.user
	if user == "Administrator":
		return True

	roles = set(frappe.get_roles(user))
	if not (roles & PORTAL_ONLY_ROLES) or (roles - BASELINE_ROLES):
		return True

	student_field = STUDENT_LINKED_DOCTYPES.get(doc.doctype)
	student = doc.get(student_field) if student_field else None
	if not student:
		return False

	if "Student" in roles and student == get_student_for_user(user):
		return True
	if "Guardian" in roles and student in get_students_for_guardian_user(user):
		return True
	return False
