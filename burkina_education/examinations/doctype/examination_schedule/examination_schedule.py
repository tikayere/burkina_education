# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time

from burkina_education.academic import grading


class ExaminationSchedule(Document):
	"""One Grade/Course sitting of an Examination: date, time, room, invigilator.

	Mirrors the app's Grade -> Program pattern: on insert this transparently
	creates and owns an Education ``Assessment Plan``, so marks entry, the
	submit-to-lock workflow, and the audit trail (docs/architecture.md
	section G) are the exact same engine used for ordinary coursework - no
	separate "exam marks" pipeline to maintain.
	"""

	def validate(self):
		self.validate_time_range()
		self.validate_room_conflict()
		self.validate_invigilator_conflict()

	def validate_time_range(self):
		if self.from_time and self.to_time and self.from_time >= self.to_time:
			frappe.throw(_("From Time must be before To Time."))

	def validate_room_conflict(self):
		conflict = self._find_overlap("room", self.room)
		if conflict:
			frappe.throw(
				_("Room {0} is already booked for {1} at this time ({2}).").format(
					frappe.bold(self.room), conflict.course, conflict.name
				)
			)

	def validate_invigilator_conflict(self):
		conflict = self._find_overlap("invigilator", self.invigilator)
		if conflict:
			frappe.throw(
				_("Invigilator {0} is already assigned to {1} at this time ({2}).").format(
					frappe.bold(self.invigilator), conflict.course, conflict.name
				)
			)

	def _find_overlap(self, fieldname, value):
		if not value or not self.exam_date or not self.from_time or not self.to_time:
			return None

		rows = frappe.get_all(
			"Examination Schedule",
			filters={
				fieldname: value,
				"exam_date": self.exam_date,
				"status": ["!=", "Cancelled"],
				"name": ["!=", self.name or ""],
			},
			fields=["name", "course", "from_time", "to_time"],
		)
		self_from, self_to = get_time(self.from_time), get_time(self.to_time)
		for row in rows:
			if self_from < get_time(row.to_time) and self_to > get_time(row.from_time):
				return row
		return None

	def after_insert(self):
		self.create_linked_assessment_plan()

	def create_linked_assessment_plan(self):
		if self.assessment_plan:
			return

		grading_scale = self._resolve_grading_scale()
		criteria_name = self._get_or_create_criteria()

		plan = frappe.get_doc(
			{
				"doctype": "Assessment Plan",
				"student_group": self.student_group,
				"assessment_group": "All Assessment Groups",
				"grading_scale": grading_scale,
				"course": self.course,
				"academic_year": frappe.db.get_value("Examination", self.examination, "academic_year"),
				"schedule_date": self.exam_date,
				"from_time": self.from_time,
				"to_time": self.to_time,
				"room": self.room,
				"examiner": self.invigilator,
				"maximum_assessment_score": self.max_score,
				"assessment_type": self.assessment_type,
				"coefficient": self.coefficient,
				"assessment_criteria": [{"assessment_criteria": criteria_name, "maximum_score": self.max_score}],
			}
		).insert(ignore_permissions=True)

		self.db_set("assessment_plan", plan.name, update_modified=False)

	def _resolve_grading_scale(self):
		scheme_name = grading.resolve_grading_scheme(self.grade)
		if scheme_name:
			scale = frappe.db.get_value("Grading Scheme", scheme_name, "grading_scale")
			if scale:
				return scale

		fallback = frappe.db.get_value("Grading Scale", {}, "name")
		if not fallback:
			frappe.throw(
				_(
					"No Grading Scale is configured anywhere on this site. Create one (or set one on "
					"a Grading Scheme) before scheduling examinations."
				)
			)
		return fallback

	def _get_or_create_criteria(self):
		# Education forbids reusing an Assessment Criteria for the same
		# (course, student_group, assessment_group) across submitted plans -
		# each Examination Schedule needs its own.
		name = f"{self.examination} - {self.course} - {self.name}"
		if not frappe.db.exists("Assessment Criteria", name):
			frappe.get_doc({"doctype": "Assessment Criteria", "assessment_criteria": name}).insert(
				ignore_permissions=True
			)
		return name

	def on_trash(self):
		if not self.assessment_plan:
			return

		submitted_results = frappe.db.exists(
			"Assessment Result", {"assessment_plan": self.assessment_plan, "docstatus": 1}
		)
		if submitted_results:
			frappe.throw(
				_("Cannot delete this Examination Schedule: marks have already been submitted for it.")
			)

		# force=1: this Examination Schedule row still exists at this point in
		# on_trash, so the link-exists check would otherwise block deleting
		# the very Assessment Plan we are cleaning up (same pattern as
		# Grade.on_trash - see docs/architecture.md).
		frappe.delete_doc(
			"Assessment Plan", self.assessment_plan, ignore_permissions=True, ignore_missing=True, force=1
		)
