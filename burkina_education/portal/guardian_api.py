# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Guardian Portal (``frontend/``, route
``/portal``). Every function re-derives the caller's own Guardian identity
from ``frappe.session.user`` and, for any function taking a ``student``
argument, re-checks that student is actually one of this guardian's own
linked children (``portal/permissions.py::require_own_student``) before
touching ``portal/common.py``'s aggregation - the same student can never be
fetched via someone else's guardian login.
"""

import frappe
from frappe.utils import flt

from burkina_education.finance.mobile_money.api import initiate_payment as _initiate_mobile_money_payment
from burkina_education.portal import common, permissions


@frappe.whitelist()
def get_children():
	students = permissions.require_guardian_students()
	rows = frappe.get_all(
		"Student",
		filters={"name": ["in", students]},
		fields=["name", "student_name", "grade", "school", "image", "status"],
	)
	for row in rows:
		row["grade_name"] = frappe.db.get_value("Grade", row.grade, "grade_name") if row.grade else None
	return rows


@frappe.whitelist()
def get_dashboard():
	students = permissions.require_guardian_students()
	children = []
	for student in students:
		summary = common.student_summary(student)
		invoice_info = common.invoices(student)
		reports = common.reports(student)
		children.append(
			{
				"name": student,
				"student_name": summary.student_name,
				"grade_name": summary.get("grade_name"),
				"image": summary.image,
				"status": summary.status,
				"attendance_percentage": common.attendance_overview(student)["last_30_days"]["percentage"],
				"outstanding_balance": invoice_info["outstanding_balance"],
				"latest_term_report": reports["term_reports"][0] if reports["term_reports"] else None,
			}
		)

	seen = {}
	for student in students:
		for a in common.announcements(student, limit=10):
			seen[a.name] = a
	announcements = sorted(seen.values(), key=lambda a: a.published_on or "", reverse=True)[:10]

	return {"children": children, "announcements": announcements}


@frappe.whitelist()
def get_child(student):
	student = permissions.require_own_student(student)
	summary = common.student_summary(student)
	invoice_info = common.invoices(student)
	reports = common.reports(student)
	library = common.library(student)
	return {
		"student": summary,
		"attendance": common.attendance_overview(student),
		"outstanding_balance": invoice_info["outstanding_balance"],
		"latest_term_report": reports["term_reports"][0] if reports["term_reports"] else None,
		"open_library_loans": len(library["open_loans"]),
		"upcoming_schedule": common.upcoming_schedule(student, limit=5),
		"announcements": common.announcements(student, limit=5),
		"discipline_open": len([d for d in common.discipline(student) if d.status != "Résolu"]),
	}


@frappe.whitelist()
def get_child_profile(student):
	student = permissions.require_own_student(student)
	info = common.student_summary(student)
	info["guardians"] = common.guardians_of(student)
	return info


@frappe.whitelist()
def get_child_attendance(student, from_date=None, to_date=None):
	student = permissions.require_own_student(student)
	from_date = from_date or frappe.utils.add_days(frappe.utils.nowdate(), -90)
	to_date = to_date or frappe.utils.nowdate()
	return {
		"summary": common.attendance_overview(student),
		"records": common.attendance_records(student, from_date, to_date),
	}


@frappe.whitelist()
def get_child_grades(student):
	student = permissions.require_own_student(student)
	return common.reports(student)


@frappe.whitelist()
def get_child_term_report(student, name):
	student = permissions.require_own_student(student)
	return common.term_report_detail(student, name)


@frappe.whitelist()
def get_child_annual_report(student, name):
	student = permissions.require_own_student(student)
	return common.annual_report_detail(student, name)


@frappe.whitelist()
def get_child_fees(student):
	student = permissions.require_own_student(student)
	return common.invoices(student)


@frappe.whitelist()
def get_child_invoice(student, name):
	student = permissions.require_own_student(student)
	return common.invoice_detail(student, name)


@frappe.whitelist()
def get_mobile_money_providers():
	permissions.require_guardian_students()
	return common.active_mobile_money_providers()


@frappe.whitelist()
def pay_child_invoice(student, invoice, provider, phone_number, amount=None):
	"""Thin, ownership-checked wrapper around the existing mobile money
	``initiate_payment`` API (docs/architecture.md section H) - that
	function already re-checks ``frappe.has_permission`` on the invoice
	itself (covered by ``student_scoped_has_permission``), this adds the
	explicit "is this even one of my own children's invoices" check the
	portal UI needs before it ever gets there."""
	student = permissions.require_own_student(student)
	invoice_doc = frappe.db.get_value("Sales Invoice", invoice, "student")
	if invoice_doc != student:
		frappe.throw(frappe._("Cette facture n'appartient pas à cet élève."), frappe.PermissionError)
	return _initiate_mobile_money_payment(
		reference_doctype="Sales Invoice",
		reference_name=invoice,
		provider=provider,
		phone_number=phone_number,
		amount=flt(amount) if amount else None,
	)


@frappe.whitelist()
def get_child_library(student):
	student = permissions.require_own_student(student)
	return common.library(student)


@frappe.whitelist()
def get_child_transport(student):
	student = permissions.require_own_student(student)
	return common.transport(student)


@frappe.whitelist()
def get_child_canteen(student):
	student = permissions.require_own_student(student)
	return common.canteen(student)


@frappe.whitelist()
def get_child_boarding(student):
	student = permissions.require_own_student(student)
	return common.boarding(student)


@frappe.whitelist()
def get_child_discipline(student):
	student = permissions.require_own_student(student)
	return common.discipline(student)


@frappe.whitelist()
def get_child_clinic(student):
	"""Health data - Guardian-only across the whole app (never exposed to
	the Student Portal itself), see ``portal/common.py::clinic``."""
	student = permissions.require_own_student(student)
	return common.clinic(student)


@frappe.whitelist()
def get_child_schedule(student, limit=30):
	student = permissions.require_own_student(student)
	return common.upcoming_schedule(student, limit=int(limit))


@frappe.whitelist()
def get_inbox(limit=50):
	permissions.require_guardian_students()
	return common.inbox(frappe.session.user, limit=int(limit))
