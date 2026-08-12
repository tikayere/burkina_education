# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.messaging.notify import notify_event
from burkina_education.messaging.tests.fixtures import CommunicationFixture


class TestNotify(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()

	def test_sms_sent_via_sandbox_provider(self):
		summary = notify_event(
			"Absence Notification",
			guardians=[self.fx.guardian.name],
			context={"student_name": "Test Élève", "from_date": "2026-10-01", "to_date": "2026-10-05",
					 "attendance_percentage": 40, "threshold": 80},
		)
		self.assertEqual(summary["sent"], 1)
		self.assertEqual(summary["failed"], 0)

		log = frappe.get_last_doc("Message Log", filters={"recipient": self.fx.guardian.name})
		self.assertEqual(log.status, "Sent")
		self.assertEqual(log.channel, "SMS")
		self.assertIn("Test Élève", log.message)
		self.assertEqual(log.provider, self.fx.provider_sms.name)

	def test_guardian_without_sms_consent_is_skipped(self):
		self.fx.guardian.db_set("sms_consent", 0)

		summary = notify_event(
			"Absence Notification",
			guardians=[self.fx.guardian.name],
			context={"student_name": "X", "from_date": "2026-10-01", "to_date": "2026-10-05",
					 "attendance_percentage": 40, "threshold": 80},
		)
		self.assertEqual(summary["sent"], 0)
		self.assertEqual(summary["skipped"], 1)

	def test_missing_template_skips_without_error(self):
		summary = notify_event(
			# "Other" - unlike every other event_key, demo data never seeds a
			# template for it, so this stays a genuine "none configured" case
			# even against a database that already has real demo data in it.
			"Other",
			guardians=[self.fx.guardian.name],
			context={"student_name": "X", "amount": "1000 FCFA", "due_date": "2026-10-01", "invoice": "SINV-1"},
		)
		self.assertEqual(summary["skipped"], 1)
		self.assertEqual(summary["sent"], 0)

	def test_missing_provider_marks_failed_not_raised(self):
		self.fx.provider_sms.db_set("is_active", 0)
		# FrappeTestCase only rolls back once per *class*, not per test
		# method - disabling this shared/reused provider (see
		# CommunicationFixture._create_provider) must not leak into whichever
		# test method runs next in this class.
		self.addCleanup(lambda: frappe.db.set_value("Messaging Provider", self.fx.provider_sms.name, "is_active", 1))

		summary = notify_event(
			"Absence Notification",
			guardians=[self.fx.guardian.name],
			context={"student_name": "X", "from_date": "2026-10-01", "to_date": "2026-10-05",
					 "attendance_percentage": 40, "threshold": 80},
		)
		self.assertEqual(summary["failed"], 1)

		log = frappe.get_last_doc("Message Log", filters={"recipient": self.fx.guardian.name})
		self.assertEqual(log.status, "Failed")
		self.assertTrue(log.error)

	def test_whatsapp_requires_its_own_consent(self):
		self.fx.guardian.db_set("whatsapp_consent", 0)
		self.fx._create_template("Absence Notification", "WhatsApp")

		summary = notify_event(
			"Absence Notification",
			guardians=[self.fx.guardian.name],
			channels=["WhatsApp"],
			context={"student_name": "X", "from_date": "2026-10-01", "to_date": "2026-10-05",
					 "attendance_percentage": 40, "threshold": 80},
		)
		self.assertEqual(summary["skipped"], 1)
		self.assertEqual(summary["sent"], 0)

	def test_student_only_notified_when_linked_to_a_user(self):
		student = self.fx.students[0]
		summary = notify_event(
			"Result Available",
			students=[student.name],
			context={"academic_term": "T1", "term_average": 15},
		)
		# No Student.user set by the base fixture - nothing to send to, but
		# must not error.
		self.assertEqual(summary["skipped"], 1)

		user = self.fx.link_student_to_user(student)
		self.fx._create_template("Result Available", "In-App")
		summary = notify_event(
			"Result Available",
			students=[student.name],
			context={"academic_term": "T1", "term_average": 15},
		)
		self.assertEqual(summary["sent"], 1)
		log = frappe.get_last_doc("Message Log", filters={"recipient": user.name})
		self.assertEqual(log.channel, "In-App")
