# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Shared test fixtures for the Phase 4 messaging/portal test suites -
building on AcademicFixture (Phase 2) the same way finance/tests/fixtures.py
does, adding a Guardian (linked to the fixture's first Student, with a real
User for portal-permission tests), a sandbox Messaging Provider, and one
active Notification Template per channel used by the test suites.
"""

import frappe

from burkina_education.academic.tests.fixtures import AcademicFixture, get_or_create_user


class CommunicationFixture(AcademicFixture):
	def __init__(self):
		super().__init__()

		self.guardian = frappe.get_doc(
			{
				"doctype": "Guardian",
				"guardian_name": f"Tuteur {self.tag}",
				"mobile_number": "+22670000010",
				"whatsapp_number": "+22670000010",
				"email_address": f"tuteur.{self.tag}@test-fixture.bf".lower(),
				"preferred_channel": "SMS",
				"sms_consent": 1,
				"whatsapp_consent": 1,
				"portal_access": 1,
				"payment_responsibility": 1,
			}
		).insert(ignore_permissions=True)

		student = self.students[0]
		student_doc = frappe.get_doc("Student", student.name)
		student_doc.append("guardians", {"guardian": self.guardian.name, "relation": "Father"})
		student_doc.save(ignore_permissions=True)

		self.provider_sms = self._create_provider("SMS")
		self.provider_whatsapp = self._create_provider("WhatsApp")

		self.template_sms = self._create_template("Absence Notification", "SMS")

	def _create_provider(self, channel):
		# FrappeTestCase only rolls back once per *class* (addClassCleanup),
		# not per test method - every test method's setUp() re-running this
		# would otherwise try to create a second "is_default" provider for
		# the same channel within the same still-open transaction and hit
		# MessagingProvider.validate()'s own uniqueness guard. Reuse whatever
		# the first setUp() in this class already created instead.
		existing = frappe.db.get_value("Messaging Provider", {"channel": channel, "is_default": 1})
		if existing:
			return frappe.get_doc("Messaging Provider", existing)

		name = f"Provider {channel} {self.tag}"
		return frappe.get_doc(
			{
				"doctype": "Messaging Provider",
				"provider_name": name,
				"channel": channel,
				"provider_code": "Generic HTTP",
				"is_active": 1,
				"sandbox_mode": 1,
				"is_default": 1,
			}
		).insert(ignore_permissions=True)

	def _create_template(self, event_key, channel, body=None):
		name = f"{event_key} {channel} {self.tag}"
		existing = frappe.db.exists("Notification Template", name)
		if existing:
			doc = frappe.get_doc("Notification Template", existing)
			if body and doc.body != body:
				doc.db_set("body", body)
			return doc

		return frappe.get_doc(
			{
				"doctype": "Notification Template",
				"template_name": name,
				"event_key": event_key,
				"channel": channel,
				"language": "fr",
				"is_active": 1,
				"body": body or "Bonjour {{ guardian_name }}, message pour {{ student_name }}.",
			}
		).insert(ignore_permissions=True)

	def link_guardian_to_user(self):
		"""Create (or reuse) a User for self.guardian, with the Guardian role,
		and link Guardian.user - used by portal/permission tests."""
		user = get_or_create_user(f"guardian.user.{self.tag}@test-fixture.bf", ["Guardian"])
		self.guardian.db_set("user", user.name)
		return user

	def link_student_to_user(self, student=None):
		student = student or self.students[0]
		user = get_or_create_user(f"student.user.{self.tag}@test-fixture.bf", ["Student"])
		frappe.db.set_value("Student", student.name, "user", user.name)
		return user
