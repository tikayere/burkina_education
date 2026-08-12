# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from burkina_education.academic.tests.fixtures import AcademicFixture
from burkina_education.attendance.alerts import run_attendance_alerts


class TestAttendanceAlerts(FrappeTestCase):
	def setUp(self):
		self.fx = AcademicFixture()

	def _mark(self, student, day_offset, status):
		doc = frappe.get_doc(
			{
				"doctype": "Student Attendance",
				"student": student.name,
				"student_group": self.fx.student_group.name,
				"date": add_days(nowdate(), day_offset),
				"status": status,
			}
		).insert(ignore_permissions=True)
		doc.submit()

	def test_low_attendance_creates_alert(self):
		student = self.fx.students[0]
		# 1 present, 4 absent over the last 5 days -> 20%, below the 80% default threshold.
		self._mark(student, -1, "Present")
		self._mark(student, -2, "Absent")
		self._mark(student, -3, "Absent")
		self._mark(student, -4, "Absent")
		self._mark(student, -5, "Absent")

		created = run_attendance_alerts()

		self.assertIn(student.name, created)
		alert = frappe.get_all(
			"Attendance Alert",
			filters={"student": student.name, "status": "New"},
			fields=["attendance_percentage", "threshold"],
		)[0]
		self.assertEqual(alert.attendance_percentage, 20.0)
		self.assertEqual(alert.threshold, 80)

	def test_good_attendance_creates_no_alert(self):
		student = self.fx.students[1]
		self._mark(student, -1, "Present")
		self._mark(student, -2, "Present")

		created = run_attendance_alerts()

		self.assertNotIn(student.name, created)
		self.assertFalse(frappe.db.exists("Attendance Alert", {"student": student.name}))

	def test_second_run_does_not_duplicate_an_open_alert(self):
		student = self.fx.students[0]
		self._mark(student, -1, "Absent")

		first_run = run_attendance_alerts()
		second_run = run_attendance_alerts()

		self.assertIn(student.name, first_run)
		self.assertNotIn(student.name, second_run)
		self.assertEqual(frappe.db.count("Attendance Alert", {"student": student.name}), 1)

	def test_late_status_is_extended_via_property_setter(self):
		student = self.fx.students[0]
		# "Late" is not one of Education's stock statuses (Present/Absent/Leave) -
		# this only succeeds because of the Phase 2 Property Setter.
		self._mark(student, -1, "Late")
		self.assertEqual(
			frappe.db.get_value(
				"Student Attendance", {"student": student.name, "status": "Late"}, "status"
			),
			"Late",
		)
