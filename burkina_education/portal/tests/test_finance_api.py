# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Finance (Accountant) Portal API tests (portal/roles/finance_api.py) -
docs/architecture.md section M. Uses ``finance.tests.fixtures.FinanceFixture``
(Phase 3's own fixture, complete with Fee Category/Structure/Schedule and a
``create_invoice`` helper) rather than ``PortalFixture``, since building a
submittable Sales Invoice needs that whole chain and PortalFixture doesn't
carry it.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic.tests.fixtures import get_or_create_user
from burkina_education.finance.tests.fixtures import FinanceFixture
from burkina_education.portal.roles import finance_api


class TestFinanceApi(FrappeTestCase):
	def setUp(self):
		self.fx = FinanceFixture()
		self.user = get_or_create_user(f"accountant.{self.fx.tag}@test-fixture.bf", ["Accountant"])
		if not frappe.db.exists("Mode of Payment", "Espèces"):
			frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Espèces", "enabled": 1}).insert(
				ignore_permissions=True
			)
		self.invoice = self.fx.create_invoice(self.fx.students[0], amount=50000)

	def _as_accountant(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_requires_accountant_role(self):
		frappe.set_user("Guest")
		try:
			self.assertRaises(frappe.PermissionError, finance_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_reports_outstanding(self):
		data = self._as_accountant(finance_api.get_dashboard)
		self.assertGreaterEqual(data["outstanding_count"], 1)
		self.assertGreaterEqual(data["outstanding_total"], 50000)

	def test_record_payment_settles_invoice(self):
		result = self._as_accountant(finance_api.record_payment, invoice=self.invoice.name, amount=50000)
		self.assertEqual(result["outstanding_amount"], 0)
		pe = frappe.get_doc("Payment Entry", result["payment_entry"])
		self.assertEqual(pe.docstatus, 1)
		self.assertEqual(pe.mode_of_payment, "Espèces")

	def test_record_payment_rejects_amount_above_outstanding(self):
		frappe.set_user(self.user.name)
		try:
			self.assertRaises(
				frappe.ValidationError, finance_api.record_payment, invoice=self.invoice.name, amount=999999
			)
		finally:
			frappe.set_user("Administrator")

	def test_record_payment_partial_leaves_remaining_outstanding(self):
		result = self._as_accountant(finance_api.record_payment, invoice=self.invoice.name, amount=20000)
		self.assertEqual(result["outstanding_amount"], 30000)
