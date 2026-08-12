# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Guardian Portal - one child's detail. "/parent/student?name=<student>".
Ownership (this student actually belongs to the logged-in guardian) is
re-checked server-side by communication.portal.guardian_student_detail() on
every data call, not just here - this get_context() only gates the page
shell itself.
"""

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("Vous devez être connecté pour accéder à cette page."), frappe.PermissionError)

	student = frappe.form_dict.get("name")
	if not student:
		frappe.throw(_("Élève non spécifié."), frappe.DoesNotExistError)

	from burkina_education.messaging.permissions import get_students_for_guardian_user

	if student not in get_students_for_guardian_user():
		frappe.throw(_("Vous n'avez pas accès à cet élève."), frappe.PermissionError)

	context.no_cache = 1
	context.show_sidebar = False
	context.student = student
	context.title = _("Espace Parent")
