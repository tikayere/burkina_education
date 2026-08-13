# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Transport Manager Portal. Route/assignment
CRUD is done directly from the frontend (Transport Manager already has full
permissions on both doctypes — docs/architecture.md section M); this module
only supplies the dashboard, since "occupancy per route" isn't something a
plain list view can compute.
"""

import frappe

from burkina_education.portal.permissions import require_any_role


@frappe.whitelist()
def get_dashboard():
	require_any_role("Transport Manager")

	routes = frappe.get_all(
		"Transport Route", fields=["name", "route_name", "vehicle", "driver", "distance_km"], order_by="route_name"
	)
	# frappe.get_all's `fields` no longer accepts a raw SQL function string
	# (`"count(name) as n"`) - plain frappe.db.sql instead, same as
	# finance_api.py's own aggregate query.
	assignment_counts = frappe.db.sql(
		"""select route, count(name) as n from `tabStudent Transport Assignment`
		where status = 'Actif' group by route""",
		as_dict=True,
	)
	counts_by_route = {r.route: r.n for r in assignment_counts}
	for route in routes:
		route["stop_count"] = frappe.db.count("Transport Route Stop", {"parent": route.name})
		route["student_count"] = counts_by_route.get(route.name, 0)
		if route.driver:
			route["driver_name"] = frappe.db.get_value("Driver", route.driver, "full_name")

	active_assignments = frappe.db.count("Student Transport Assignment", {"status": "Actif"})
	unassigned_stop = frappe.db.count("Student Transport Assignment", {"status": "Actif", "stop_name": ["in", ("", None)]})

	return {
		"routes": routes,
		"routes_count": len(routes),
		"active_assignments": active_assignments,
		"unassigned_stop": unassigned_stop,
	}


@frappe.whitelist()
def get_route_students(route):
	require_any_role("Transport Manager")
	return frappe.get_all(
		"Student Transport Assignment",
		filters={"route": route, "status": "Actif"},
		fields=["name", "student", "student_name", "stop_name", "start_date"],
		order_by="stop_name",
	)
