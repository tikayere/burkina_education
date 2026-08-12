# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.messaging.tests.fixtures import CommunicationFixture


class TestResultAvailableNotification(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()
		self.fx._create_template("Result Available", "SMS")

	def test_submitting_term_report_notifies_guardian(self):
		report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": self.fx.students[0].name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
				"term_average": 14.5,
			}
		).insert(ignore_permissions=True)
		report.submit()

		log = frappe.get_last_doc(
			"Message Log",
			filters={"event_key": "Result Available", "reference_name": report.name},
		)
		self.assertEqual(log.status, "Sent")
		self.assertEqual(log.recipient, self.fx.guardian.name)

	def test_annual_report_submit_also_notifies(self):
		self.fx._create_template("Result Available", "SMS", body="Moyenne annuelle: {{ term_average }}")
		annual = frappe.get_doc(
			{
				"doctype": "Student Annual Report",
				"student": self.fx.students[0].name,
				"academic_year": self.fx.academic_year.name,
				"annual_average": 13.2,
			}
		).insert(ignore_permissions=True)
		annual.submit()

		log = frappe.get_last_doc(
			"Message Log",
			filters={"event_key": "Result Available", "reference_name": annual.name},
		)
		self.assertEqual(log.status, "Sent")
