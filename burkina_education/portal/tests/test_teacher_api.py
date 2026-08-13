# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Teacher Portal API tests (portal/teacher_api.py) - docs/architecture.md
section L. Covers instructor identity resolution (Employee.user_id, not
Instructor - a real bug found while building this, see
messaging/doctype/announcement/announcement.py::_teacher_users()), the
"do you actually teach this group" ownership boundary, and the Class
Teacher-only Discipline gate (master.md §37)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal import permissions, teacher_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestTeacherApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.link_instructor_to_user()

	def _as_teacher(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_instructor_resolved_via_employee_user_id(self):
		self.assertEqual(permissions.get_instructor_for_user(self.user.name), self.fx.instructor.name)

	def test_dashboard_counts_own_group(self):
		data = self._as_teacher(teacher_api.get_dashboard)
		self.assertEqual(data["groups_count"], 1)
		self.assertEqual(data["students_count"], len(self.fx.students))
		self.assertFalse(data["is_class_teacher"])

	def test_get_groups_lists_only_taught_groups(self):
		other_group = self.fx.other_student_group()
		groups = self._as_teacher(teacher_api.get_groups)
		names = {g["name"] for g in groups}
		self.assertIn(self.fx.student_group.name, names)
		self.assertNotIn(other_group.name, names)

	def test_group_students_rejects_untaught_group(self):
		other_group = self.fx.other_student_group()
		frappe.set_user(self.user.name)
		try:
			self.assertRaises(
				frappe.PermissionError, teacher_api.get_group_students, other_group.name
			)
		finally:
			frappe.set_user("Administrator")

	def test_mark_attendance_creates_and_submits_records(self):
		student = self.fx.students[0]
		result = self._as_teacher(
			teacher_api.mark_attendance,
			student_group=self.fx.student_group.name,
			date=frappe.utils.nowdate(),
			records=[{"student": student.name, "status": "Present"}],
		)
		self.assertEqual(result["created"], 1)

		att = frappe.db.get_value(
			"Student Attendance",
			{"student": student.name, "student_group": self.fx.student_group.name, "docstatus": 1},
			["status", "docstatus"],
			as_dict=True,
		)
		self.assertEqual(att.status, "Present")
		self.assertEqual(att.docstatus, 1)

	def test_mark_attendance_rejects_student_outside_roster(self):
		outsider = frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": "Hors",
				"last_name": self.fx.tag,
				"gender": "Male",
				"student_email_id": f"hors.{self.fx.tag}@test-fixture.bf".lower(),
			}
		).insert(ignore_permissions=True)

		result = self._as_teacher(
			teacher_api.mark_attendance,
			student_group=self.fx.student_group.name,
			date=frappe.utils.nowdate(),
			records=[{"student": outsider.name, "status": "Present"}],
		)
		self.assertEqual(result["created"], 0)
		self.assertEqual(result["skipped"], 1)

	def test_gradebook_save_then_submit(self):
		plan = frappe.get_doc(
			{
				"doctype": "Assessment Plan",
				"student_group": self.fx.student_group.name,
				"assessment_group": "All Assessment Groups",
				"grading_scale": self.fx.grading_scale,
				"course": self.fx.course.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
				"schedule_date": frappe.utils.nowdate(),
				"from_time": "08:00:00",
				"to_time": "08:45:00",
				"maximum_assessment_score": 20,
				"assessment_criteria": [{"assessment_criteria": self.fx._new_assessment_criteria(), "maximum_score": 20}],
			}
		).insert(ignore_permissions=True)
		plan.submit()

		student = self.fx.students[0]
		criteria_name = plan.assessment_criteria[0].assessment_criteria

		save_result = self._as_teacher(
			teacher_api.save_assessment_results,
			assessment_plan=plan.name,
			results=[
				{
					"student": student.name,
					"comment": "Bon travail",
					"details": [{"assessment_criteria": criteria_name, "maximum_score": 20, "score": 15}],
				}
			],
		)
		self.assertIn(student.name, save_result["saved"])

		result_name = frappe.db.get_value(
			"Assessment Result", {"assessment_plan": plan.name, "student": student.name}, "name"
		)
		self.assertEqual(frappe.db.get_value("Assessment Result", result_name, "total_score"), 15)

		submitted_name = self._as_teacher(teacher_api.submit_assessment_result, result_name)
		self.assertEqual(frappe.db.get_value("Assessment Result", submitted_name, "docstatus"), 1)

	def test_discipline_requires_class_teacher_role(self):
		frappe.set_user(self.user.name)
		try:
			self.assertRaises(frappe.PermissionError, teacher_api.get_discipline_cases)
			self.assertRaises(
				frappe.PermissionError,
				teacher_api.create_discipline_case,
				student=self.fx.students[0].name,
				incident_type="Comportement",
				severity="Mineure",
				description="Test",
			)
		finally:
			frappe.set_user("Administrator")

	def test_discipline_available_once_class_teacher_role_granted(self):
		self.fx.link_instructor_to_user(extra_roles=["Class Teacher"])
		case_name = self._as_teacher(
			teacher_api.create_discipline_case,
			student=self.fx.students[0].name,
			incident_type="Comportement",
			severity="Mineure",
			description="Bavardage.",
		)
		self.assertTrue(frappe.db.exists("Disciplinary Case", case_name))

		cases = self._as_teacher(teacher_api.get_discipline_cases)
		self.assertIn(case_name, {c["name"] for c in cases})

	def test_send_message_to_guardian_requires_taught_student(self):
		outsider = frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": "Hors",
				"last_name": self.fx.tag,
				"gender": "Male",
				"student_email_id": f"hors2.{self.fx.tag}@test-fixture.bf".lower(),
			}
		).insert(ignore_permissions=True)

		frappe.set_user(self.user.name)
		try:
			self.assertRaises(
				frappe.PermissionError,
				teacher_api.send_message_to_guardian,
				student=outsider.name,
				message="Test",
			)
		finally:
			frappe.set_user("Administrator")

	def test_send_message_to_guardian_delivers_in_app(self):
		self.fx.link_guardian_to_user()
		student = self.fx.students[0]
		summary = self._as_teacher(
			teacher_api.send_message_to_guardian, student=student.name, message="Merci de venir signer le bulletin."
		)
		self.assertGreaterEqual(summary["sent"], 1)
		log_exists = frappe.db.exists(
			"Message Log", {"recipient": self.fx.guardian.user, "channel": "In-App", "event_key": "Other"}
		)
		self.assertTrue(log_exists)


class TestAnnouncementTeacherUsersFix(FrappeTestCase):
	"""Regression test for the Instructor -> Employee -> User chain bug this
	Teacher Portal work found in ``_teacher_users()`` (it used to pluck a
	non-existent ``user_id`` field directly off Instructor)."""

	def test_teacher_users_resolves_through_employee(self):
		from burkina_education.messaging.doctype.announcement.announcement import _teacher_users

		fx = PortalFixture()
		user = fx.link_instructor_to_user()
		self.assertIn(user.name, _teacher_users())
