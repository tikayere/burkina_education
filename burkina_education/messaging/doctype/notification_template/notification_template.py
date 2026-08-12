# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

#: Documented per event_key purely for the Desk UI ("Variables disponibles"
#: read-only helper field) - messaging/notify.py is the single source of
#: truth for what context is actually passed at each call site; this is not
#: read back by any code path, only shown to the person editing a template.
PLACEHOLDER_HINTS = {
	"Absence Notification": "student_name, guardian_name, from_date, to_date, attendance_percentage, threshold",
	"Payment Confirmation": "student_name, guardian_name, amount, currency, reference, balance",
	"Fee Reminder": "student_name, guardian_name, amount, currency, due_date, invoice",
	"Result Available": "student_name, guardian_name, academic_term, term_average, passing_score",
	"School Announcement": "title, content, school_name",
	"Emergency Message": "title, content, school_name",
	"Parent Meeting": "student_name, guardian_name, date, location",
	"Timetable Change": "student_name, guardian_name, description",
	"Other": "(dépend de l'appel manuel - voir la documentation de l'Annonce/l'événement concerné)",
}


class NotificationTemplate(Document):
	def validate(self):
		self.available_placeholders = PLACEHOLDER_HINTS.get(self.event_key, "")
		if self.channel == "Email" and not self.subject:
			frappe.throw(frappe._("Un modèle de canal E-mail doit avoir un objet."))
