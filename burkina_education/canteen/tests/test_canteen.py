# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from burkina_education.school.tests.fixtures import MinimalSchoolFixture


class TestCanteen(IntegrationTestCase):
	def setUp(self):
		self.fixture = MinimalSchoolFixture()
		self.meal_plan = frappe.get_doc(
			{"doctype": "Meal Plan", "plan_name": f"Formule {self.fixture.tag}", "price_per_month": 20000}
		).insert(ignore_permissions=True)
		self.subscription = frappe.get_doc(
			{
				"doctype": "Canteen Subscription",
				"student": self.fixture.student.name,
				"meal_plan": self.meal_plan.name,
			}
		).insert(ignore_permissions=True)

	def test_consumption_logged_for_active_subscription(self):
		log = frappe.get_doc(
			{"doctype": "Meal Consumption", "subscription": self.subscription.name}
		).insert(ignore_permissions=True)
		self.assertEqual(log.student, self.fixture.student.student_name)

	def test_consumption_rejected_for_suspended_subscription(self):
		self.subscription.status = "Suspendue"
		self.subscription.save()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{"doctype": "Meal Consumption", "subscription": self.subscription.name}
			).insert(ignore_permissions=True)

	def test_consumption_rejected_outside_subscription_period(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Meal Consumption",
					"subscription": self.subscription.name,
					"date": add_days(nowdate(), -5),
				}
			).insert(ignore_permissions=True)

	def test_end_date_before_start_date_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Canteen Subscription",
					"student": self.fixture.student.name,
					"meal_plan": self.meal_plan.name,
					"end_date": add_days(nowdate(), -1),
				}
			).insert(ignore_permissions=True)
