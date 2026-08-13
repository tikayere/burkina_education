# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Canteen Manager Portal API tests (portal/roles/canteen_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import canteen_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestCanteenApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("Canteen Manager")
		self.plan = frappe.get_doc(
			{"doctype": "Meal Plan", "plan_name": f"Formule {self.fx.tag}", "price_per_month": 15000, "status": "Active"}
		).insert(ignore_permissions=True)
		self.subscription = frappe.get_doc(
			{
				"doctype": "Canteen Subscription",
				"student": self.fx.students[0].name,
				"meal_plan": self.plan.name,
				"status": "Active",
				"start_date": frappe.utils.add_days(frappe.utils.nowdate(), -5),
			}
		).insert(ignore_permissions=True)

	def _as_manager(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_counts(self):
		# >= rather than == - the dev site's demo data also contributes
		# Meal Plans/Canteen Subscriptions (see test_librarian_api.py).
		data = self._as_manager(canteen_api.get_dashboard)
		self.assertGreaterEqual(data["active_subscriptions"], 1)
		self.assertGreaterEqual(data["plans"], 1)

	def test_get_roster_reports_unmarked_subscription(self):
		rows = self._as_manager(canteen_api.get_roster, meal_plan=self.plan.name, meal_type="Déjeuner")
		self.assertEqual(len(rows), 1)
		self.assertFalse(rows[0]["consumed"])

	def test_mark_consumption_is_idempotent(self):
		first = self._as_manager(
			canteen_api.mark_consumption, subscriptions=[self.subscription.name], meal_type="Déjeuner"
		)
		self.assertEqual(first, {"created": 1, "skipped": 0})

		second = self._as_manager(
			canteen_api.mark_consumption, subscriptions=[self.subscription.name], meal_type="Déjeuner"
		)
		self.assertEqual(second, {"created": 0, "skipped": 1})

		rows = self._as_manager(canteen_api.get_roster, meal_plan=self.plan.name, meal_type="Déjeuner")
		self.assertTrue(rows[0]["consumed"])
