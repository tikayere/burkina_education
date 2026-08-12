# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""App-level access check for the Frappe /apps screen and app switcher
(hooks.py::add_to_apps_screen) - not a data-permission check (those are all
per-doctype, see messaging/permissions.py and the rest of this app).
This only decides whether the "Burkina Education" tile/icon is worth
showing at all: any logged-in Desk user, i.e. not Guest and not a
Guardian/Student-only portal account (which never has Desk access to begin
with, so the icon would be dead weight for them).
"""

import frappe


def has_app_permission():
	if frappe.session.user == "Guest":
		return False

	roles = set(frappe.get_roles(frappe.session.user))
	if roles & {"Guardian", "Student"} and not (roles - {"Guardian", "Student", "All"}):
		return False

	return True
