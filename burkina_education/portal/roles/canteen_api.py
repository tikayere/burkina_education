# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Canteen Manager Portal. Meal Plan/Subscription
CRUD is done directly from the frontend (full permissions — docs/
architecture.md section M); this module supplies the dashboard and a bulk
"mark today's roster" action, since checking in a whole dining hall one
``Meal Consumption`` row at a time through a generic form would be unusable.
"""

import frappe
from frappe.utils import nowdate

from burkina_education.portal.permissions import require_any_role

MEAL_TYPES = ("Petit-déjeuner", "Déjeuner", "Goûter")


@frappe.whitelist()
def get_dashboard():
	require_any_role("Canteen Manager")

	plans = frappe.db.count("Meal Plan", {"status": "Active"})
	active_subscriptions = frappe.db.count("Canteen Subscription", {"status": "Active"})
	today = nowdate()
	consumed_today = frappe.db.count("Meal Consumption", {"date": today, "consumed": 1})

	# frappe.get_all's `fields` no longer accepts a raw SQL function string
	# (`"count(name) as n"`) - plain frappe.db.sql instead, same as
	# finance_api.py's own aggregate query.
	by_plan = frappe.db.sql(
		"""select meal_plan, count(name) as n from `tabCanteen Subscription`
		where status = 'Active' group by meal_plan""",
		as_dict=True,
	)
	for row in by_plan:
		row["plan_name"] = frappe.db.get_value("Meal Plan", row.meal_plan, "plan_name")

	return {
		"plans": plans,
		"active_subscriptions": active_subscriptions,
		"consumed_today": consumed_today,
		"by_plan": by_plan,
	}


@frappe.whitelist()
def get_roster(meal_plan=None, date=None, meal_type="Déjeuner"):
	"""Active subscriptions (optionally narrowed to one plan) with whether
	each one already has a Meal Consumption row for ``date``/``meal_type`` —
	the checklist ``mark_consumption`` submits from."""
	require_any_role("Canteen Manager")

	date = date or nowdate()
	filters = {"status": "Active"}
	if meal_plan:
		filters["meal_plan"] = meal_plan

	subs = frappe.get_all(
		"Canteen Subscription", filters=filters, fields=["name", "student", "student_name", "meal_plan"], order_by="student_name"
	)
	if not subs:
		return []

	marked = set(
		frappe.get_all(
			"Meal Consumption",
			filters={"subscription": ["in", [s.name for s in subs]], "date": date, "meal_type": meal_type},
			pluck="subscription",
		)
	)
	for s in subs:
		s["consumed"] = s.name in marked
	return subs


@frappe.whitelist()
def mark_consumption(subscriptions, date=None, meal_type="Déjeuner", consumed=True):
	"""Bulk check-in: one Meal Consumption row per subscription that doesn't
	already have one for this date/meal_type. Idempotent — re-submitting the
	same roster doesn't create duplicates."""
	require_any_role("Canteen Manager")

	subscriptions = frappe.parse_json(subscriptions) if isinstance(subscriptions, str) else subscriptions
	date = date or nowdate()
	consumed = frappe.parse_json(consumed) if isinstance(consumed, str) else consumed

	created, skipped = 0, 0
	for subscription in subscriptions:
		exists = frappe.db.exists(
			"Meal Consumption", {"subscription": subscription, "date": date, "meal_type": meal_type}
		)
		if exists:
			skipped += 1
			continue
		frappe.get_doc(
			{
				"doctype": "Meal Consumption",
				"subscription": subscription,
				"date": date,
				"meal_type": meal_type,
				"consumed": 1 if consumed else 0,
			}
		).insert()
		created += 1

	return {"created": created, "skipped": skipped}
