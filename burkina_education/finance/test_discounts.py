# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.finance import discounts
from burkina_education.finance.tests.fixtures import FinanceFixture


class TestDiscounts(FrappeTestCase):
	def setUp(self):
		self.fixture = FinanceFixture()

	def test_sibling_rank_and_discount(self):
		settings = frappe.get_single("Burkina Education Settings")
		settings.set("sibling_discount_rules", [])
		settings.append("sibling_discount_rules", {"sibling_rank": 2, "discount_percent": 10})
		settings.append("sibling_discount_rules", {"sibling_rank": 3, "discount_percent": 20})
		settings.save(ignore_permissions=True)

		first, second, third = self.fixture.students
		self.assertEqual(discounts.sibling_rank(first.name, self.fixture.academic_year.name), 1)
		self.assertEqual(discounts.sibling_rank(second.name, self.fixture.academic_year.name), 2)
		self.assertEqual(discounts.sibling_rank(third.name, self.fixture.academic_year.name), 3)

		self.assertEqual(discounts.sibling_discount_percent(first.name, self.fixture.academic_year.name), 0)
		self.assertEqual(discounts.sibling_discount_percent(second.name, self.fixture.academic_year.name), 10)
		self.assertEqual(discounts.sibling_discount_percent(third.name, self.fixture.academic_year.name), 20)

	def test_scholarship_full_overrides_sibling(self):
		settings = frappe.get_single("Burkina Education Settings")
		settings.set("sibling_discount_rules", [])
		settings.append("sibling_discount_rules", {"sibling_rank": 2, "discount_percent": 10})
		settings.save(ignore_permissions=True)

		second = self.fixture.students[1]
		frappe.get_doc(
			{
				"doctype": "Scholarship",
				"student": second.name,
				"academic_year": self.fixture.academic_year.name,
				"scholarship_type": "Bourse Totale",
				"discount_percent": 100,
				"status": "Approuvée",
			}
		).insert(ignore_permissions=True)

		percent, notes = discounts.resolve_discount_percent(second.name, self.fixture.academic_year.name)
		self.assertEqual(percent, 100)
		self.assertIn("Bourse Totale", notes)

	def test_partial_scholarship_combines_with_sibling_discount_capped_at_100(self):
		settings = frappe.get_single("Burkina Education Settings")
		settings.set("sibling_discount_rules", [])
		settings.append("sibling_discount_rules", {"sibling_rank": 2, "discount_percent": 60})
		settings.save(ignore_permissions=True)

		second = self.fixture.students[1]
		frappe.get_doc(
			{
				"doctype": "Scholarship",
				"student": second.name,
				"academic_year": self.fixture.academic_year.name,
				"scholarship_type": "Bourse Partielle",
				"discount_percent": 60,
				"status": "Approuvée",
			}
		).insert(ignore_permissions=True)

		percent, notes = discounts.resolve_discount_percent(second.name, self.fixture.academic_year.name)
		self.assertEqual(percent, 100)  # 60 + 60 capped
		self.assertEqual(len(notes), 2)

	def test_draft_scholarship_is_not_applied(self):
		second = self.fixture.students[1]
		frappe.get_doc(
			{
				"doctype": "Scholarship",
				"student": second.name,
				"academic_year": self.fixture.academic_year.name,
				"scholarship_type": "Bourse Partielle",
				"discount_percent": 50,
				"status": "Brouillon",
			}
		).insert(ignore_permissions=True)

		percent, notes = discounts.resolve_discount_percent(second.name, self.fixture.academic_year.name)
		self.assertEqual(percent, 0)

	def test_sales_invoice_hook_applies_discount_and_recomputes_total(self):
		settings = frappe.get_single("Burkina Education Settings")
		settings.set("sibling_discount_rules", [])
		settings.append("sibling_discount_rules", {"sibling_rank": 2, "discount_percent": 10})
		settings.save(ignore_permissions=True)

		second = self.fixture.students[1]
		invoice = self.fixture.create_invoice(second, amount=100000, submit=False)
		self.assertEqual(invoice.additional_discount_percentage, 10)
		self.assertAlmostEqual(invoice.grand_total, 90000, places=2)

	def test_sales_invoice_without_fee_schedule_is_untouched(self):
		# The hook must be a no-op on an arbitrary (non-school-fee) Sales
		# Invoice - it should never fire outside the fee-schedule flow.
		second = self.fixture.students[1]
		customer = frappe.db.get_value("Student", second.name, "customer")
		invoice = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": customer,
				"company": self.fixture.company.name,
				"currency": "XOF",
				"set_posting_time": 1,
				"posting_date": frappe.utils.nowdate(),
				"items": [{"item_code": self.fixture.fee_category.item, "qty": 1, "rate": 100000}],
			}
		)
		invoice.insert(ignore_permissions=True)
		self.assertFalse(invoice.additional_discount_percentage)
		self.assertAlmostEqual(invoice.grand_total, 100000, places=2)
