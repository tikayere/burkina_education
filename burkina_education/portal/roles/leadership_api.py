# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Leadership Portal (School Director) — one
read-heavy, cross-module dashboard rather than per-module pages, matching
what the role's real permissions actually are: broad oversight of Boarding /
Canteen / Clinic / Transport / Discipline / Scholarship / Announcements /
Settings (docs/architecture.md section M), *not* Finance or Library, which
stay with Accountant/Librarian. Every count below stays inside that real
grant so this dashboard never shows the Director something their own Desk
account couldn't also see.
"""

import frappe

from burkina_education.portal.permissions import require_any_role


@frappe.whitelist()
def get_dashboard():
	require_any_role("School Director")

	return {
		"school": {
			"campuses": frappe.db.count("Campus"),
			"open_discipline_cases": frappe.db.count("Disciplinary Case", {"status": ["!=", "Résolu"]}),
			"pending_scholarships": frappe.db.count("Scholarship", {"status": "Brouillon"}),
		},
		"boarding": {
			"beds": frappe.db.count("Boarding Bed"),
			"occupied": frappe.db.count("Boarding Bed", {"status": "Occupé"}),
		},
		"canteen": {
			"active_subscriptions": frappe.db.count("Canteen Subscription", {"status": "Active"}),
		},
		"transport": {
			"active_routes": frappe.db.count("Transport Route"),
			"active_assignments": frappe.db.count("Student Transport Assignment", {"status": "Actif"}),
		},
		"clinic": {
			"open_cases": frappe.db.count("Clinic Visit", {"status": ["!=", "Clos"]}),
		},
		"comms": {
			"published_announcements": frappe.db.count("Announcement", {"publication_status": "Published"}),
		},
		"recent_discipline": frappe.get_all(
			"Disciplinary Case",
			filters={"status": ["!=", "Résolu"]},
			fields=["name", "student_name", "incident_type", "severity", "date", "status"],
			order_by="date desc",
			limit=8,
		),
	}
