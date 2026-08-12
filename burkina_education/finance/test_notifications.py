# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from burkina_education.finance.notifications import run_fee_reminders
from burkina_education.finance.tests.fixtures import FinanceFixture


def _make_notifiable(guardian_doc, phone="+22670000020"):
	"""FinanceFixture's shared Guardian only sets name/email - fill in what
	the notification engine actually needs to reach them by SMS."""
	guardian_doc.db_set("mobile_number", phone)
	guardian_doc.db_set("sms_consent", 1)
	guardian_doc.db_set("preferred_channel", "SMS")

	# FrappeTestCase only rolls back once per *class* (addClassCleanup), not
	# per test method - every test method's setUp() re-running this would
	# otherwise try to create a second "is_default" SMS provider within the
	# same still-open transaction and hit MessagingProvider.validate()'s own
	# uniqueness guard. Reuse whatever the first setUp() already created.
	if frappe.db.exists("Messaging Provider", {"channel": "SMS", "is_default": 1}):
		return

	frappe.get_doc(
		{
			"doctype": "Messaging Provider",
			"provider_name": f"SMS {frappe.generate_hash(length=6)}",
			"channel": "SMS",
			"provider_code": "Generic HTTP",
			"is_active": 1,
			"sandbox_mode": 1,
			"is_default": 1,
		}
	).insert(ignore_permissions=True)


class TestPaymentConfirmationNotification(FrappeTestCase):
	def setUp(self):
		self.fx = FinanceFixture()
		_make_notifiable(self.fx.guardian)
		frappe.get_doc(
			{
				"doctype": "Notification Template",
				"template_name": f"Paiement {self.fx.tag}",
				"event_key": "Payment Confirmation",
				"channel": "SMS",
				"is_active": 1,
				"body": "Merci {{ guardian_name }}, {{ amount }} reçu pour {{ student_name }}.",
			}
		).insert(ignore_permissions=True)

	def test_cash_payment_entry_submit_notifies_guardian(self):
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		invoice = self.fx.create_invoice(self.fx.students[0], submit=True)
		pe = get_payment_entry("Sales Invoice", invoice.name, party_amount=invoice.outstanding_amount)
		pe.reference_no = "TEST-CASH"
		pe.reference_date = nowdate()
		pe.insert(ignore_permissions=True)
		pe.submit()

		log = frappe.get_last_doc(
			"Message Log", filters={"event_key": "Payment Confirmation", "reference_name": pe.name}
		)
		self.assertEqual(log.status, "Sent")
		self.assertEqual(log.recipient, self.fx.guardian.name)

	def test_non_fee_payment_entry_is_ignored(self):
		"""A Payment Entry against an invoice with no ``student`` set (an
		ordinary ERPNext sale, if this Company ever has one) must not crash
		or notify anyone."""
		from burkina_education.finance.notifications import notify_payment_confirmation

		pe = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Receive", "party_type": "Customer"})
		# Calling the hook directly with no references is the relevant edge
		# case - it must simply no-op.
		notify_payment_confirmation(pe)  # should not raise


class TestFeeReminders(FrappeTestCase):
	def setUp(self):
		self.fx = FinanceFixture()
		_make_notifiable(self.fx.guardian, phone="+22670000021")
		frappe.get_doc(
			{
				"doctype": "Notification Template",
				"template_name": f"Rappel {self.fx.tag}",
				"event_key": "Fee Reminder",
				"channel": "SMS",
				"is_active": 1,
				"body": "Relance {{ student_name }}: {{ amount }} en retard depuis le {{ due_date }}.",
			}
		).insert(ignore_permissions=True)

	def _overdue_invoice(self, days_overdue):
		invoice = self.fx.create_invoice(self.fx.students[0], submit=False)
		new_due_date = add_days(nowdate(), -days_overdue) if days_overdue else add_days(nowdate(), 10)
		if days_overdue:
			# ERPNext rejects a due_date before posting_date - back-date
			# posting_date too so an "overdue" invoice is actually valid.
			invoice.posting_date = add_days(new_due_date, -1)
			invoice.set_posting_time = 1
		invoice.due_date = new_due_date
		# Sales Invoice.set_due_date() (ERPNext core) recomputes due_date from
		# the auto-generated payment_schedule row's own due_date on every
		# save/validate - setting only the parent field gets silently
		# overwritten back to the original unless the schedule row agrees.
		for row in invoice.payment_schedule:
			row.due_date = new_due_date
		invoice.save(ignore_permissions=True)
		invoice.submit()
		return invoice

	def test_overdue_invoice_triggers_reminder(self):
		invoice = self._overdue_invoice(10)

		notified = run_fee_reminders()

		self.assertIn(invoice.name, notified)
		log = frappe.get_last_doc(
			"Message Log", filters={"event_key": "Fee Reminder", "reference_name": invoice.name}
		)
		self.assertEqual(log.status, "Sent")

	def test_reminder_is_not_repeated_within_interval(self):
		invoice = self._overdue_invoice(10)

		first = run_fee_reminders(interval_days=7)
		second = run_fee_reminders(interval_days=7)

		self.assertIn(invoice.name, first)
		self.assertNotIn(invoice.name, second)

	def test_invoice_not_yet_due_is_not_reminded(self):
		self._overdue_invoice(0)

		notified = run_fee_reminders()

		self.assertEqual(notified, [])
