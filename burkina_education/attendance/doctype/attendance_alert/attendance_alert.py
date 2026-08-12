# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendanceAlert(Document):
	"""A logged low-attendance detection for one student over one period
	(master.md §24). Detection/audit is attendance/alerts.py::run_attendance_alerts();
	notifying the guardian (Phase 4/Communication) is this doc's own
	``notify_guardians()``, triggered explicitly from the Desk "Marquer comme
	notifié" button rather than automatically at creation - a low-attendance
	alert may be worth a phone call or in-person conversation before an SMS
	goes out, see docs/architecture.md section J.
	"""

	@frappe.whitelist()
	def notify_guardians(self):
		frappe.has_permission(self.doctype, "write", self, throw=True)

		from burkina_education.messaging.notify import notify_event

		guardians = frappe.get_all("Student Guardian", filters={"parent": self.student}, pluck="guardian")
		result = notify_event(
			"Absence Notification",
			guardians=guardians,
			context={
				"student_name": self.student_name,
				"from_date": frappe.utils.formatdate(self.from_date),
				"to_date": frappe.utils.formatdate(self.to_date),
				"attendance_percentage": self.attendance_percentage,
				"threshold": self.threshold,
			},
			reference_doctype=self.doctype,
			reference_name=self.name,
		)
		self.db_set("status", "Notified")
		return result
