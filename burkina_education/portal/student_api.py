# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Student Portal (``frontend/``, route
``/portal``). Every function re-derives the caller's own Student identity
from ``frappe.session.user`` (``portal/permissions.py::require_student``) -
never a client-supplied student id. See ``portal/common.py`` for the actual
per-student aggregation, shared with the Guardian Portal.
"""

import frappe

from burkina_education.portal import common, permissions


@frappe.whitelist()
def get_dashboard():
	student = permissions.require_student()
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
def get_profile():
	student = permissions.require_student()
	info = common.student_summary(student)
	info["guardians"] = common.guardians_of(student)
	return info


@frappe.whitelist()
def get_attendance(from_date=None, to_date=None):
	student = permissions.require_student()
	from_date = from_date or frappe.utils.add_days(frappe.utils.nowdate(), -90)
	to_date = to_date or frappe.utils.nowdate()
	return {
		"summary": common.attendance_overview(student),
		"records": common.attendance_records(student, from_date, to_date),
	}


@frappe.whitelist()
def get_grades():
	student = permissions.require_student()
	return common.reports(student)


@frappe.whitelist()
def get_term_report(name):
	student = permissions.require_student()
	return common.term_report_detail(student, name)


@frappe.whitelist()
def get_annual_report(name):
	student = permissions.require_student()
	return common.annual_report_detail(student, name)


@frappe.whitelist()
def get_fees():
	student = permissions.require_student()
	return common.invoices(student)


@frappe.whitelist()
def get_invoice(name):
	student = permissions.require_student()
	return common.invoice_detail(student, name)


@frappe.whitelist()
def get_mobile_money_providers():
	permissions.require_student()
	return common.active_mobile_money_providers()


@frappe.whitelist()
def get_library():
	student = permissions.require_student()
	return common.library(student)


@frappe.whitelist()
def get_transport():
	student = permissions.require_student()
	return common.transport(student)


@frappe.whitelist()
def get_canteen():
	student = permissions.require_student()
	return common.canteen(student)


@frappe.whitelist()
def get_boarding():
	student = permissions.require_student()
	return common.boarding(student)


@frappe.whitelist()
def get_discipline():
	student = permissions.require_student()
	return common.discipline(student)


@frappe.whitelist()
def get_schedule(limit=30):
	student = permissions.require_student()
	return common.upcoming_schedule(student, limit=int(limit))


@frappe.whitelist()
def get_announcements(limit=20):
	student = permissions.require_student()
	return common.announcements(student, limit=int(limit))


@frappe.whitelist()
def get_inbox(limit=50):
	permissions.require_student()
	return common.inbox(frappe.session.user, limit=int(limit))
