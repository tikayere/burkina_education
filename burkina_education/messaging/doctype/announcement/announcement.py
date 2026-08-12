# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""School announcements (master.md §35) - authoring/audience-targeting lives
here; actual delivery (in-app Notification Log + SMS/WhatsApp/Email via
Message Log) is delegated to communication.notify so this module doesn't
duplicate the fan-out/rendering logic every other notification event uses.
See docs/architecture.md section J.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class Announcement(Document):
	def validate(self):
		if self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(_("La date de fin ne peut pas être antérieure à la date de début."))

	@frappe.whitelist()
	def publish(self):
		"""Resolve the audience, fan the announcement out through
		communication.notify (in-app + whichever of SMS/WhatsApp/Email were
		checked), and lock the announcement into Published state."""
		if self.publication_status == "Published":
			frappe.throw(_("Cette annonce est déjà publiée."))
		frappe.has_permission(self.doctype, "write", self, throw=True)

		from burkina_education.messaging.notify import notify_event

		guardians, students, users = resolve_audience(self)

		channels = []
		if self.notify_sms:
			channels.append("SMS")
		if self.notify_whatsapp:
			channels.append("WhatsApp")
		if self.notify_email:
			channels.append("Email")
		if self.notify_in_app:
			channels.append("In-App")

		context = {"title": self.title, "content": frappe.utils.strip_html(self.content or "")}
		# An Announcement's audience can be the whole school - always fan out
		# through a background job rather than blocking the "Publier" button
		# (master.md §59: background jobs for anything that scales with
		# student count).
		result = notify_event(
			"School Announcement",
			guardians=guardians,
			students=students,
			users=users,
			context=context,
			channels=channels or None,
			reference_doctype=self.doctype,
			reference_name=self.name,
			background=True,
		)

		self.db_set("publication_status", "Published")
		self.db_set("published_on", frappe.utils.now_datetime())
		self.db_set("published_by", frappe.session.user)
		return result

	@frappe.whitelist()
	def archive(self):
		frappe.has_permission(self.doctype, "write", self, throw=True)
		self.db_set("publication_status", "Archived")

	@frappe.whitelist()
	def preview_audience(self):
		"""Counts only - lets the person publishing sanity-check the audience
		size before it fans out (large schools especially, master.md §59)."""
		guardians, students, users = resolve_audience(self)
		return {"guardians": len(guardians), "students": len(students), "users": len(users)}


def resolve_audience(doc):
	"""Return ``(guardian_names, student_names, user_names)`` for an
	Announcement's ``audience_type`` - deliberately three separate lists
	rather than one, since in-app/email notifications go to Users while
	SMS/WhatsApp go to Guardians (via their phone numbers)."""
	guardians, students, users = [], [], []

	if doc.audience_type == "All":
		students = frappe.get_all("Student", filters={"status": "Active"}, pluck="name")
		guardians = _guardians_of(students)
		users = _teacher_users()
	elif doc.audience_type == "All Guardians":
		# Deliberately does not also populate the returned `students` list -
		# unlike "Education Level"/"Grade"/"Student Group" below, "All
		# Guardians" means guardians only, by name.
		active_students = frappe.get_all("Student", filters={"status": "Active"}, pluck="name")
		guardians = _guardians_of(active_students)
	elif doc.audience_type == "All Students":
		students = frappe.get_all("Student", filters={"status": "Active"}, pluck="name")
	elif doc.audience_type == "All Teachers":
		users = _teacher_users()
	elif doc.audience_type == "Education Level":
		# Scoped population audiences (Education Level/Grade/Student Group),
		# unlike "All Guardians", notify both that population's students
		# (their own portal) and its guardians - a "this class" announcement
		# is reasonably for both, not guardians-only.
		grades = frappe.get_all("Grade", filters={"education_level": doc.audience_reference}, pluck="name")
		students = frappe.get_all(
			"Student", filters={"status": "Active", "grade": ["in", grades or [""]]}, pluck="name"
		)
		guardians = _guardians_of(students)
	elif doc.audience_type == "Grade":
		students = frappe.get_all(
			"Student", filters={"status": "Active", "grade": doc.audience_reference}, pluck="name"
		)
		guardians = _guardians_of(students)
	elif doc.audience_type == "Student Group":
		students = frappe.get_all(
			"Student Group Student", filters={"parent": doc.audience_reference, "active": 1}, pluck="student"
		)
		guardians = _guardians_of(students)

	return guardians, students, users


def _guardians_of(student_names):
	if not student_names:
		return []
	rows = frappe.get_all("Student Guardian", filters={"parent": ["in", student_names]}, pluck="guardian")
	return list(dict.fromkeys(rows))


def _teacher_users():
	rows = frappe.get_all(
		"Instructor", filters={"status": "Active"}, pluck="user_id"
	)
	return [u for u in dict.fromkeys(rows) if u]


def get_visible_announcements(audience_filters=None, limit=20):
	"""Published announcements currently within their visibility window -
	used by both the Guardian and Student Portals (messaging/portal.py)."""
	today = nowdate()
	filters = {
		"publication_status": "Published",
		"start_date": ["<=", today],
	}
	rows = frappe.get_all(
		"Announcement",
		filters=filters,
		or_filters=[{"end_date": [">=", today]}, {"end_date": ["is", "not set"]}],
		fields=["name", "title", "content", "priority", "published_on", "audience_type", "audience_reference"],
		order_by="priority desc, published_on desc",
		limit_page_length=limit,
	)
	return rows


def get_visible_announcements_for_student(student, limit=20):
	"""Same as ``get_visible_announcements`` but narrowed to announcements
	whose audience actually includes ``student`` - used by the Guardian/
	Student Portals so a "Grade"-scoped announcement for another class
	doesn't show up (master.md §35 audience examples)."""
	from burkina_education.academic import grading

	grade = frappe.db.get_value("Student", student, "grade")
	education_level = grading.get_education_level_for_grade(grade) if grade else None
	student_groups = set(
		frappe.get_all("Student Group Student", filters={"student": student, "active": 1}, pluck="parent")
	)

	broad = {"All", "All Guardians", "All Students"}
	visible = []
	for row in get_visible_announcements(limit=limit * 3):
		if row.audience_type in broad:
			visible.append(row)
		elif row.audience_type == "Grade" and row.audience_reference == grade:
			visible.append(row)
		elif row.audience_type == "Education Level" and row.audience_reference == education_level:
			visible.append(row)
		elif row.audience_type == "Student Group" and row.audience_reference in student_groups:
			visible.append(row)
		if len(visible) >= limit:
			break
	return visible
