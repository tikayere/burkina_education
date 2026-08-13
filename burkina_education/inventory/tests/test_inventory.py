# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase

from burkina_education.finance.tests.fixtures import FinanceFixture
from burkina_education.inventory.setup import seed_asset_categories


class TestInventory(IntegrationTestCase):
	def test_asset_has_condition_field(self):
		self.assertTrue(frappe.db.exists("Custom Field", "Asset-condition"))

	def test_school_director_and_it_administrator_granted_on_asset(self):
		roles = {
			p.role
			for p in frappe.get_all("Custom DocPerm", filters={"parent": "Asset"}, fields=["role"])
		}
		self.assertIn("School Director", roles)
		self.assertIn("IT Administrator", roles)

	def test_seed_asset_categories_creates_categories_with_accounts(self):
		# Idempotent like every other seed helper in setup/install.py (roles,
		# XOF currency, ...): a category already seeded by an earlier run
		# (demo data, or another test) is left as-is rather than re-pointed
		# at this fixture's own Company - so this only asserts every category
		# exists with at least one real accounts row, not which company.
		fixture = FinanceFixture()
		created = seed_asset_categories(fixture.company.name)
		self.assertEqual(len(created), 4)
		for name in created:
			category = frappe.get_doc("Asset Category", name)
			self.assertTrue(category.accounts)
			self.assertTrue(category.accounts[0].company_name)
			self.assertTrue(category.accounts[0].fixed_asset_account)
