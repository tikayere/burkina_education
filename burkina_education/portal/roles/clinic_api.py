# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Clinic Staff Portal. Clinic Visit CRUD is
done directly from the frontend (Clinic Staff already has full permissions
on the doctype — docs/architecture.md section M); this module supplies only
the dashboard.
"""

import frappe
from frappe.utils import nowdate

from burkina_education.portal.permissions import require_any_role


@frappe.whitelist()
def get_dashboard():
	require_any_role("Clinic Staff")

	today = nowdate()
	visits_today = frappe.db.count("Clinic Visit", {"date": ["between", (f"{today} 00:00:00", f"{today} 23:59:59")]})
	open_cases = frappe.db.count("Clinic Visit", {"status": "Ouvert"})
	follow_up = frappe.db.count("Clinic Visit", {"status": "Suivi requis"})
	not_notified = frappe.db.count("Clinic Visit", {"parent_notified": 0, "status": ["!=", "Clos"]})

	recent = frappe.get_all(
		"Clinic Visit",
		fields=["name", "student", "student_name", "date", "status", "complaint", "parent_notified"],
		order_by="date desc",
		limit=15,
	)

	return {
		"visits_today": visits_today,
		"open_cases": open_cases,
		"follow_up": follow_up,
		"not_notified": not_notified,
		"recent": recent,
	}
