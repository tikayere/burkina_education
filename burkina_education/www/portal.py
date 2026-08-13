# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Server-rendered shell for the Vue 3 + frappe-ui Portal (``frontend/``,
master.md §29/§30/§31 - see docs/architecture.md section L, extended to
every operational staff Role by section M). ``frontend/index.html`` itself
(built by ``yarn build`` into this same ``www/portal.html``, via frappe-ui's
vite "buildConfig" plugin) is the whole page; this module only supplies the
small ``boot`` dict its "jinjaBootData" plugin flattens onto ``window``
before ``</body>`` - just enough for the SPA to know who's logged in and to
authenticate its own POST calls (``frappe-ui``'s ``call()`` reads
``window.csrf_token`` directly), not a full Desk-style boot. The SPA's own
router (not this module) decides which portal to render, from
``window.roles``.
"""

import frappe
from frappe import _
from frappe.sessions import get_csrf_token

from burkina_education.portal.roles import STAFF_ROLES

no_cache = 1

ALLOWED_ROLES = {"Guardian", "Student", "Instructor", *STAFF_ROLES}


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/portal"
		raise frappe.Redirect

	roles = frappe.get_roles()
	if not (set(roles) & ALLOWED_ROLES):
		frappe.throw(
			_("Ce compte n'a accès à aucun espace. Contactez l'administration."),
			frappe.PermissionError,
		)

	context.no_cache = 1
	context.boot = {
		"user": frappe.session.user,
		"full_name": frappe.utils.get_fullname(frappe.session.user),
		"roles": roles,
		"user_image": frappe.db.get_value("User", frappe.session.user, "user_image"),
		"sitename": frappe.local.site,
		"csrf_token": get_csrf_token(),
	}
