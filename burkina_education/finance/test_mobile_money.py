# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.finance.mobile_money import api
from burkina_education.finance.tests.fixtures import FinanceFixture


class TestMobileMoney(FrappeTestCase):
	def setUp(self):
		self.fixture = FinanceFixture()
		self.student = self.fixture.students[0]
		self.invoice = self.fixture.create_invoice(self.student, amount=50000)

		self.provider = frappe.get_doc(
			{
				"doctype": "Mobile Money Provider",
				"provider_name": f"Orange Money {self.fixture.tag}",
				"provider_code": "Orange Money",
				"is_active": 1,
				"sandbox_mode": 1,
				"mode_of_payment": "Cash",
				"currency": "XOF",
				"webhook_secret": "s3cr3t-key",
			}
		).insert(ignore_permissions=True)

	def _initiate(self):
		return api.initiate_payment(
			reference_doctype="Sales Invoice",
			reference_name=self.invoice.name,
			provider=self.provider.name,
			phone_number="+22670000000",
		)

	def test_initiate_creates_pending_transaction(self):
		result = self._initiate()
		txn = frappe.get_doc("Mobile Money Transaction", result["transaction"])
		self.assertEqual(txn.status, "Pending")
		self.assertTrue(txn.gateway_transaction_id)

	def test_webhook_with_valid_signature_confirms_payment(self):
		result = self._initiate()
		txn = frappe.get_doc("Mobile Money Transaction", result["transaction"])

		outcome = api.webhook(
			provider=self.provider.name,
			gateway_transaction_id=txn.gateway_transaction_id,
			status="SUCCESS",
			signature="s3cr3t-key",
		)

		self.assertEqual(outcome["status"], "success")
		txn.reload()
		self.assertEqual(txn.status, "Success")
		self.assertTrue(txn.payment_entry)

		payment_entry = frappe.get_doc("Payment Entry", txn.payment_entry)
		self.assertEqual(payment_entry.docstatus, 1)
		self.assertAlmostEqual(payment_entry.paid_amount, 50000, places=2)

		self.invoice.reload()
		self.assertAlmostEqual(self.invoice.outstanding_amount, 0, places=2)

	def test_duplicate_webhook_does_not_create_a_second_payment(self):
		result = self._initiate()
		txn_name = result["transaction"]
		gateway_id = frappe.db.get_value("Mobile Money Transaction", txn_name, "gateway_transaction_id")

		first = api.webhook(
			provider=self.provider.name, gateway_transaction_id=gateway_id, status="SUCCESS", signature="s3cr3t-key"
		)
		second = api.webhook(
			provider=self.provider.name, gateway_transaction_id=gateway_id, status="SUCCESS", signature="s3cr3t-key"
		)

		self.assertEqual(first["status"], "success")
		self.assertEqual(second["status"], "already_processed")
		self.assertEqual(
			frappe.db.count("Payment Entry", {"reference_no": gateway_id}), 1
		)

	def test_webhook_with_wrong_signature_is_rejected(self):
		result = self._initiate()
		gateway_id = frappe.db.get_value(
			"Mobile Money Transaction", result["transaction"], "gateway_transaction_id"
		)

		with self.assertRaises(frappe.ValidationError):
			api.webhook(
				provider=self.provider.name,
				gateway_transaction_id=gateway_id,
				status="SUCCESS",
				signature="wrong-secret",
			)

		txn = frappe.get_doc("Mobile Money Transaction", result["transaction"])
		self.assertEqual(txn.status, "Pending")

	def test_webhook_for_unknown_transaction_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			api.webhook(
				provider=self.provider.name,
				gateway_transaction_id="does-not-exist",
				status="SUCCESS",
				signature="s3cr3t-key",
			)

	def test_initiate_rejects_amount_above_outstanding(self):
		with self.assertRaises(frappe.ValidationError):
			api.initiate_payment(
				reference_doctype="Sales Invoice",
				reference_name=self.invoice.name,
				provider=self.provider.name,
				phone_number="+22670000000",
				amount=999999,
			)
