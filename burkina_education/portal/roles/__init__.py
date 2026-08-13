# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue "staff" portals — one Vue SPA route-group per operational Role, on
top of the same ``frontend/`` app as the Student/Guardian/Teacher portals
(docs/architecture.md section L, then extended per section M: "navigating
doctypes for modifications is tedious, give every role an appropriate
portal/dashboard").

Unlike Guardian/Student/Instructor, every role mapped here already carries
correct, real doctype-level permissions (Custom DocPerm / DocPerm — see
architecture.md section M for the exact grant each role has). So these
portals are *not* ownership-scoped like ``portal/common.py`` — a Librarian
genuinely can see every Library Book, not "their own". That means most
reads/writes here go straight through ``frappe-ui``'s generic
``createListResource``/``createDocumentResource`` (i.e. plain
``frappe.client.get_list``/``insert``/``set_value``/``delete``, permission
checked exactly like Desk) directly from the frontend — no bespoke Python
needed. The modules in this package supply only what a generic list/detail
view can't: dashboard/KPI aggregates, and the handful of guided multi-step
actions (issue/return a book, record a payment, ...) that are more than one
field's worth of change.

``ROLE_PORTAL`` is the single source of truth for which Role maps to which
SPA route-group — read by ``hooks.py`` (``role_home_page``),
``www/portal.py`` (the accept-list of roles allowed into ``/portal``), and
mirrored (by hand — see ``frontend/src/session.js``) on the frontend for nav
selection, since the two can't share a Python import.
"""

# Registrar/Academic Director/Examination Coordinator share one portal
# ("academic") because their real permissions are strictly nested (Registrar
# ⊂ Academic Director for the reference-data doctypes both touch; Examination
# Coordinator's two doctypes are a subset of what Academic Director already
# has) — one Vue route-group with role-aware nav, rather than three near-
# identical copies. See ``academic_api.py``.
ROLE_PORTAL = {
	"Librarian": "librarian",
	"Transport Manager": "transport",
	"Canteen Manager": "canteen",
	"Boarding Manager": "boarding",
	"Clinic Staff": "clinic",
	"Accountant": "finance",
	"Registrar": "academic",
	"Academic Director": "academic",
	"Examination Coordinator": "academic",
	"Secretary": "comms",
	"School Director": "leadership",
}

STAFF_ROLES = list(ROLE_PORTAL.keys())


def current_academic_year():
	"""Best-effort "today's" Academic Year — whichever one's date range
	actually contains today, falling back to the most recently started one
	(e.g. before the new year's Academic Year record has been created yet).
	Used only as a convenience default (guided-workflow endpoints that create
	a doc with an ``academic_year`` field); every such field stays a normal,
	editable Link on the frontend, this just saves re-picking it every time.
	"""
	import frappe
	from frappe.utils import nowdate

	today = nowdate()
	current = frappe.db.get_value(
		"Academic Year", {"year_start_date": ["<=", today], "year_end_date": [">=", today]}, "name"
	)
	if current:
		return current
	return frappe.db.get_value("Academic Year", {}, "name", order_by="year_start_date desc")
