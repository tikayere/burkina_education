# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic.tests.fixtures import AcademicFixture


class TestExaminationSchedule(FrappeTestCase):
	def setUp(self):
		self.fx = AcademicFixture()
		self.examination = frappe.get_doc(
			{
				"doctype": "Examination",
				"examination_name": f"Composition {self.fx.tag}",
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)
		self.room = frappe.get_doc(
			{"doctype": "Room", "room_name": f"Salle {self.fx.tag}"}
		).insert(ignore_permissions=True)
		self.invigilator = frappe.get_doc(
			{
				"doctype": "Instructor",
				"instructor_name": f"Surveillant {self.fx.tag}",
			}
		).insert(ignore_permissions=True)

	def _schedule(self, course=None, room=None, invigilator=None, from_time="08:00:00", to_time="10:00:00"):
		return frappe.get_doc(
			{
				"doctype": "Examination Schedule",
				"examination": self.examination.name,
				"grade": self.fx.grade.name,
				"student_group": self.fx.student_group.name,
				"course": course or self.fx.course.name,
				"exam_date": "2025-12-01",
				"from_time": from_time,
				"to_time": to_time,
				"room": room or self.room.name,
				"invigilator": invigilator or self.invigilator.name,
				"max_score": 20,
			}
		).insert(ignore_permissions=True)

	def test_creates_and_owns_an_assessment_plan(self):
		schedule = self._schedule()

		self.assertTrue(schedule.assessment_plan)
		self.assertEqual(
			frappe.db.get_value("Assessment Plan", schedule.assessment_plan, "course"), self.fx.course.name
		)

		schedule.delete()
		self.assertFalse(frappe.db.exists("Assessment Plan", schedule.assessment_plan))

	def test_room_conflict_is_detected(self):
		self._schedule(from_time="08:00:00", to_time="10:00:00")

		other_course = frappe.get_doc(
			{"doctype": "Course", "course_name": f"Autre matiere {self.fx.tag}"}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			self._schedule(course=other_course.name, from_time="09:00:00", to_time="11:00:00")

	def test_invigilator_conflict_is_detected(self):
		self._schedule(from_time="08:00:00", to_time="10:00:00")

		other_course = frappe.get_doc(
			{"doctype": "Course", "course_name": f"Autre matiere 2 {self.fx.tag}"}
		).insert(ignore_permissions=True)
		other_room = frappe.get_doc(
			{"doctype": "Room", "room_name": f"Autre salle {self.fx.tag}"}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			self._schedule(
				course=other_course.name, room=other_room.name, from_time="09:30:00", to_time="11:00:00"
			)

	def test_non_overlapping_slots_are_allowed(self):
		self._schedule(from_time="08:00:00", to_time="10:00:00")

		other_course = frappe.get_doc(
			{"doctype": "Course", "course_name": f"Autre matiere 3 {self.fx.tag}"}
		).insert(ignore_permissions=True)

		# Same room, same invigilator, but a later non-overlapping slot.
		second = self._schedule(course=other_course.name, from_time="10:00:00", to_time="12:00:00")
		self.assertTrue(second.assessment_plan)
