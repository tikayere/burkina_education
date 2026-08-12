# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Install-time setup for burkina_education.

Runs once when the app is installed on a site (``hooks.py`` -> ``after_install``).
Every step here is idempotent so it is also safe to re-run manually
(``bench execute burkina_education.setup.install.after_install``) while a
DocType's custom fields are still evolving during development.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Roles from docs/architecture.md section D / master prompt section 3 that have
# no existing equivalent in frappe/erpnext/education. Roles that already exist
# upstream (Instructor, Student, Accounts Manager, HR Manager, ...) are reused,
# not recreated here.
NEW_ROLES = [
	"School Director",
	"Academic Director",
	"Secretary",
	"Registrar",
	"Receptionist",
	"Class Teacher",
	"Department Head",
	"Examination Coordinator",
	"Guardian",
	"Librarian",
	"Transport Manager",
	"Canteen Manager",
	"Boarding Manager",
	"Clinic Staff",
	"IT Administrator",
]


def after_install():
	create_roles()
	create_custom_fields(get_custom_fields(), ignore_validate=True)
	ensure_default_settings()


def create_roles():
	for role in NEW_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def ensure_default_settings():
	settings = frappe.get_single("Burkina Education Settings")
	if not settings.default_currency:
		settings.default_currency = "XOF"
	if not settings.default_language:
		settings.default_language = "fr"
	settings.save(ignore_permissions=True)


def get_custom_fields():
	"""Custom Fields that extend Education/ERPNext DocTypes.

	See docs/architecture.md section B for the reuse/extend rationale behind
	each field.
	"""
	return {
		"Student": [
			{
				"fieldname": "matricule",
				"label": "Matricule",
				"fieldtype": "Data",
				"insert_after": "student_email_id",
				"unique": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
			},
			{
				"fieldname": "school",
				"label": "École",
				"fieldtype": "Link",
				"options": "School",
				"insert_after": "matricule",
				"in_standard_filter": 1,
			},
			{
				"fieldname": "campus",
				"label": "Campus",
				"fieldtype": "Link",
				"options": "Campus",
				"insert_after": "school",
			},
			{
				"fieldname": "grade",
				"label": "Classe",
				"fieldtype": "Link",
				"options": "Grade",
				"insert_after": "campus",
				"in_standard_filter": 1,
			},
			{
				"fieldname": "status",
				"label": "Statut",
				"fieldtype": "Select",
				"options": "Active\nGraduated\nTransferred\nWithdrawn\nSuspended\nRepeating\nDeceased",
				"default": "Active",
				"insert_after": "enabled",
				"in_standard_filter": 1,
			},
			{
				"fieldname": "place_of_birth",
				"label": "Lieu de naissance",
				"fieldtype": "Data",
				"insert_after": "nationality",
			},
		],
		"Guardian": [
			{
				"fieldname": "whatsapp_number",
				"label": "Numéro WhatsApp",
				"fieldtype": "Data",
				"insert_after": "alternate_number",
			},
			{
				"fieldname": "preferred_channel",
				"label": "Canal de communication préféré",
				"fieldtype": "Select",
				"options": "SMS\nWhatsApp\nEmail\nPortail",
				"default": "SMS",
				"insert_after": "whatsapp_number",
			},
			{
				"fieldname": "sms_consent",
				"label": "Consentement SMS",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "preferred_channel",
			},
			{
				"fieldname": "portal_access",
				"label": "Accès au portail parent",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "sms_consent",
			},
			{
				"fieldname": "payment_responsibility",
				"label": "Responsable financier",
				"fieldtype": "Check",
				"insert_after": "portal_access",
			},
		],
		"Course": [
			{
				"fieldname": "course_code",
				"label": "Code",
				"fieldtype": "Data",
				"insert_after": "course_name",
				"in_list_view": 1,
			},
			{
				"fieldname": "coefficient",
				"label": "Coefficient",
				"fieldtype": "Float",
				"default": "1",
				"insert_after": "course_code",
			},
			{
				"fieldname": "hours_per_week",
				"label": "Heures / semaine",
				"fieldtype": "Float",
				"insert_after": "coefficient",
			},
			{
				"fieldname": "grading_type",
				"label": "Type de notation",
				"fieldtype": "Select",
				"options": "Numeric\nLetter\nCompetency\nPass/Fail\nCustom",
				"default": "Numeric",
				"insert_after": "hours_per_week",
			},
			{
				"fieldname": "is_active",
				"label": "Actif",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "grading_type",
			},
		],
		"Academic Term": [
			{
				"fieldname": "sequence",
				"label": "Ordre",
				"fieldtype": "Int",
				"insert_after": "term_end_date",
			},
			{
				"fieldname": "weight",
				"label": "Pondération (moyenne annuelle)",
				"fieldtype": "Float",
				"default": "1",
				"insert_after": "sequence",
			},
		],
	}
