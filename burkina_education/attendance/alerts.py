# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Attendance threshold detection (master.md §24: "attendance < configured
threshold -> optionally notify"). This module only detects and logs; sending
an actual SMS/WhatsApp/portal notification is Phase 4 (Communication) -
see docs/architecture.md section G.
"""

import frappe
from frappe.utils import add_days, nowdate

from burkina_education.academic import grading

#: How far back to look when no explicit window is given (e.g. the daily
#: scheduled run) - a rolling window rather than "since the start of time"
#: keeps a single bad stretch from permanently flagging a student.
DEFAULT_WINDOW_DAYS = 30


@frappe.whitelist()
def run_attendance_alerts(from_date=None, to_date=None):
	"""For every active Student with at least one Student Attendance record
	in the window, create an Attendance Alert if their attendance percentage
	is below ``Burkina Education Settings.attendance_alert_threshold`` and no
	still-open ("New") alert already covers this window.
	"""
	threshold = frappe.db.get_single_value("Burkina Education Settings", "attendance_alert_threshold")
	if not threshold:
		return []

	to_date = to_date or nowdate()
	from_date = from_date or add_days(to_date, -DEFAULT_WINDOW_DAYS)

	students = frappe.get_all("Student", filters={"status": "Active"}, fields=["name"])

	created = []
	for student in students:
		summary = grading.get_attendance_summary(student.name, from_date, to_date)
		if not summary["total"] or summary["percentage"] >= threshold:
			continue

		already_open = frappe.db.exists(
			"Attendance Alert",
			{"student": student.name, "status": "New", "to_date": [">=", from_date]},
		)
		if already_open:
			continue

		frappe.get_doc(
			{
				"doctype": "Attendance Alert",
				"student": student.name,
				"from_date": from_date,
				"to_date": to_date,
				"total_days": summary["total"],
				"present_count": summary["present"],
				"absent_count": summary["absent"],
				"late_count": summary["late"],
				"attendance_percentage": summary["percentage"],
				"threshold": threshold,
			}
		).insert(ignore_permissions=True)
		created.append(student.name)

	return created
