# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Overdue-loan detection/notification (master.md §39 "notifications"),
mirroring finance.notifications.run_fee_reminders and
attendance.alerts.run_attendance_alerts (docs/architecture.md section K).
"""

import frappe
from frappe.utils import formatdate, nowdate


def run_overdue_notices():
	"""Daily scheduled job: flips any still-'Emprunté' Library Transaction
	past its due date to 'En retard' and notifies the student's guardians.
	Notification fires exactly once per transaction - the filter below only
	ever matches a transaction the first time it goes overdue, since the
	status flip removes it from 'Emprunté' afterwards (no separate rate-limit
	field needed, unlike Finance's recurring fee reminders)."""
	from burkina_education.messaging.notify import notify_event

	overdue = frappe.get_all(
		"Library Transaction",
		filters={"status": "Emprunté", "due_date": ["<", nowdate()]},
		fields=["name", "membership", "book_title", "due_date"],
	)
	for row in overdue:
		frappe.db.set_value("Library Transaction", row.name, "status", "En retard")

		student = frappe.db.get_value("Library Membership", row.membership, "student")
		if not student:
			continue
		guardians = frappe.get_all("Student Guardian", filters={"parent": student}, pluck="guardian")
		if not guardians:
			continue

		notify_event(
			"Library Book Overdue",
			guardians=guardians,
			context={"book_title": row.book_title, "due_date": formatdate(row.due_date)},
			reference_doctype="Library Transaction",
			reference_name=row.name,
		)
