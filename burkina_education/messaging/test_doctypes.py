# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.messaging.tests.fixtures import CommunicationFixture


class TestMessagingProvider(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()

	def test_second_default_provider_for_same_channel_is_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "Messaging Provider",
				"provider_name": f"Second SMS {self.fx.tag}",
				"channel": "SMS",
				"provider_code": "Generic HTTP",
				"is_active": 1,
				"is_default": 1,
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_default_providers_for_different_channels_coexist(self):
		# self.fx already created a default SMS provider and a default
		# WhatsApp provider - both must be allowed to stand.
		self.assertTrue(frappe.db.get_value("Messaging Provider", self.fx.provider_sms.name, "is_default"))
		self.assertTrue(frappe.db.get_value("Messaging Provider", self.fx.provider_whatsapp.name, "is_default"))


class TestNotificationTemplate(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()

	def test_email_template_requires_subject(self):
		doc = frappe.get_doc(
			{
				"doctype": "Notification Template",
				"template_name": f"Sans objet {self.fx.tag}",
				"event_key": "Payment Confirmation",
				"channel": "Email",
				"body": "Bonjour",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_placeholder_hints_are_populated(self):
		doc = frappe.get_doc(
			{
				"doctype": "Notification Template",
				"template_name": f"Avec objet {self.fx.tag}",
				"event_key": "Payment Confirmation",
				"channel": "Email",
				"subject": "Paiement reçu",
				"body": "Bonjour",
			}
		).insert(ignore_permissions=True)
		self.assertIn("amount", doc.available_placeholders)
