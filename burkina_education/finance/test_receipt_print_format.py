# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.www.printview import get_html_and_style

from burkina_education.finance.tests.fixtures import FinanceFixture


class TestReceiptPrintFormat(FrappeTestCase):
	def setUp(self):
		self.fixture = FinanceFixture()

	def test_receipt_renders_payment_details(self):
		student = self.fixture.students[0]
		invoice = self.fixture.create_invoice(student, amount=75000)

		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry("Sales Invoice", invoice.name, party_amount=75000)
		pe.mode_of_payment = "Cash"
		pe.reference_no = "TEST-REF-1"
		pe.reference_date = frappe.utils.nowdate()
		pe.insert(ignore_permissions=True)
		pe.submit()

		result = get_html_and_style(doc="Payment Entry", name=pe.name, print_format="Recu de Paiement")
		html = result["html"]

		self.assertIn(pe.name, html)
		self.assertIn("75000.00", html)
