# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Guardian/Student Portals (master.md §29/§30) and
portal-user provisioning. Every function here re-derives the caller's own
Guardian/Student identity from ``frappe.session.user`` server-side rather
than trusting a client-supplied id for *whose* data to return - only
``guardian_student_detail``/``get_student_dashboard`` additionally take a
``student`` argument, and that argument is always checked against the
caller's own linked students before anything is returned (master.md §54:
"never rely exclusively on frontend permissions").

See messaging/permissions.py for the matching ``has_permission`` hook
that backs the same guarantee for direct doctype reads (``/printview``).
"""

import frappe
from frappe import _
from frappe.utils import nowdate

from burkina_education.academic import grading
from burkina_education.messaging.doctype.announcement.announcement import get_visible_announcements_for_student
from burkina_education.messaging.permissions import get_student_for_user, get_students_for_guardian_user


# ---------------------------------------------------------------------------
# Portal-user provisioning (Desk side - Guardian/Student form buttons)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def invite_guardian(guardian):
	"""Create (or link) a Website User for a Guardian and grant the
	``Guardian`` portal role. Unlike Education's own ``guardian.invite_guardian``
	(which creates the User but never links it back), this always sets
	``Guardian.user`` - the field the whole portal/permission layer keys off.
	"""
	frappe.has_permission("Guardian", "write", throw=True)
	guardian_doc = frappe.get_doc("Guardian", guardian)
	if not guardian_doc.email_address:
		frappe.throw(_("Veuillez d'abord renseigner l'adresse e-mail du tuteur."))

	user_name = guardian_doc.user or frappe.db.get_value("User", {"email": guardian_doc.email_address})
	if not user_name:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"first_name": guardian_doc.guardian_name,
				"email": guardian_doc.email_address,
				"user_type": "Website User",
				"send_welcome_email": 1,
			}
		)
		user.append("roles", {"role": "Guardian"})
		user.insert(ignore_permissions=True)
		user_name = user.name
	else:
		user = frappe.get_doc("User", user_name)
		if not any(r.role == "Guardian" for r in user.roles):
			user.append("roles", {"role": "Guardian"})
			user.save(ignore_permissions=True)

	if guardian_doc.user != user_name:
		guardian_doc.db_set("user", user_name)

	return user_name


@frappe.whitelist()
def invite_student(student):
	"""Same as ``invite_guardian`` but for a Student - explicit and
	independent of ``Education Settings.user_creation_skip`` (which the demo
	seed/tests flip off, and a real school may too, without that meaning
	nobody should ever get portal access)."""
	frappe.has_permission("Student", "write", throw=True)
	student_doc = frappe.get_doc("Student", student)
	if not student_doc.student_email_id:
		frappe.throw(_("Veuillez d'abord renseigner l'adresse e-mail de l'élève."))

	user_name = student_doc.user or frappe.db.get_value("User", {"email": student_doc.student_email_id})
	if not user_name:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"first_name": student_doc.first_name,
				"last_name": student_doc.last_name,
				"email": student_doc.student_email_id,
				"user_type": "Website User",
				"send_welcome_email": 1,
			}
		)
		user.append("roles", {"role": "Student"})
		user.insert(ignore_permissions=True)
		user_name = user.name
	else:
		user = frappe.get_doc("User", user_name)
		if not any(r.role == "Student" for r in user.roles):
			user.append("roles", {"role": "Student"})
			user.save(ignore_permissions=True)

	if student_doc.user != user_name:
		student_doc.db_set("user", user_name)

	return user_name


# ---------------------------------------------------------------------------
# Guardian Portal
# ---------------------------------------------------------------------------


def _require_guardian():
	students = get_students_for_guardian_user()
	if not students:
		frappe.throw(_("Aucun compte tuteur n'est associé à cet utilisateur."), frappe.PermissionError)
	return students


@frappe.whitelist()
def guardian_dashboard():
	"""One card per child: identity, attendance (last 30 days), outstanding
	balance, latest submitted term report if any."""
	students = _require_guardian()
	rows = frappe.get_all(
		"Student",
		filters={"name": ["in", students]},
		fields=["name", "student_name", "grade", "school", "image", "status"],
	)
	for row in rows:
		row["grade_name"] = frappe.db.get_value("Grade", row.grade, "grade_name") if row.grade else None
		summary = grading.get_attendance_summary(row.name, _thirty_days_ago(), nowdate())
		row["attendance_percentage"] = summary["percentage"]
		row["outstanding_balance"] = _outstanding_balance(row.name)
		row["latest_report"] = frappe.db.get_value(
			"Student Term Report", {"student": row.name, "docstatus": 1}, "name", order_by="creation desc"
		)
	announcements = {}
	for name in students:
		for a in get_visible_announcements_for_student(name, limit=10):
			announcements[a.name] = a
	announcements = sorted(announcements.values(), key=lambda a: a.published_on or "", reverse=True)[:10]

	return {"children": rows, "announcements": announcements}


@frappe.whitelist()
def guardian_student_detail(student):
	students = _require_guardian()
	if student not in students:
		frappe.throw(_("Vous n'avez pas accès à cet élève."), frappe.PermissionError)
	return _student_detail(student)


# ---------------------------------------------------------------------------
# Student Portal
# ---------------------------------------------------------------------------


@frappe.whitelist()
def student_dashboard():
	student = get_student_for_user()
	if not student:
		frappe.throw(_("Aucun compte élève n'est associé à cet utilisateur."), frappe.PermissionError)
	return _student_detail(student)


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


def _student_detail(student):
	info = frappe.db.get_value(
		"Student", student, ["student_name", "grade", "school", "image", "status"], as_dict=True
	)
	if info.grade:
		info["grade_name"] = frappe.db.get_value("Grade", info.grade, "grade_name")

	term_reports = frappe.get_all(
		"Student Term Report",
		filters={"student": student, "docstatus": 1},
		fields=["name", "academic_term", "term_average", "class_rank", "class_size"],
		order_by="creation desc",
	)
	annual_reports = frappe.get_all(
		"Student Annual Report",
		filters={"student": student, "docstatus": 1},
		fields=["name", "academic_year", "annual_average", "annual_rank", "decision"],
		order_by="creation desc",
	)
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"student": student, "docstatus": 1},
		fields=["name", "grand_total", "outstanding_amount", "due_date", "currency", "status"],
		order_by="posting_date desc",
	)

	return {
		"student": info,
		"attendance": grading.get_attendance_summary(student, _thirty_days_ago(), nowdate()),
		"term_reports": term_reports,
		"annual_reports": annual_reports,
		"invoices": invoices,
		"outstanding_balance": sum(i.outstanding_amount or 0 for i in invoices),
		"announcements": get_visible_announcements_for_student(student, limit=10),
	}


def _outstanding_balance(student):
	rows = frappe.get_all(
		"Sales Invoice", filters={"student": student, "docstatus": 1}, fields=["outstanding_amount"]
	)
	return sum(r.outstanding_amount or 0 for r in rows)


def _thirty_days_ago():
	return frappe.utils.add_days(nowdate(), -30)
