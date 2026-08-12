# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Guardian Portal dashboard (master.md §29) - "/parent". Server-rendered
shell; the actual data comes from a client-side call to
communication.portal.guardian_dashboard() so the page works the same way
whether it's a first load or a soft-refresh after acting on something.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("Vous devez être connecté pour accéder à cette page."), frappe.PermissionError)

	from burkina_education.messaging.permissions import get_students_for_guardian_user

	if not get_students_for_guardian_user():
		frappe.throw(
			_("Aucun compte tuteur n'est associé à cet utilisateur. Contactez l'administration de l'école."),
			frappe.PermissionError,
		)

	context.no_cache = 1
	context.show_sidebar = False
	context.title = _("Espace Parent")
