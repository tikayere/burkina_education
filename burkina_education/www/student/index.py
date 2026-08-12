# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Student Portal (master.md §30) - "/student". Same shape as the Guardian
Portal's child-detail page, but scoped to the logged-in Student themselves
via communication.portal.student_dashboard()."""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("Vous devez être connecté pour accéder à cette page."), frappe.PermissionError)

	from burkina_education.messaging.permissions import get_student_for_user

	if not get_student_for_user():
		frappe.throw(
			_("Aucun compte élève n'est associé à cet utilisateur. Contactez l'administration de l'école."),
			frappe.PermissionError,
		)

	context.no_cache = 1
	context.show_sidebar = False
	context.title = _("Espace Élève")
