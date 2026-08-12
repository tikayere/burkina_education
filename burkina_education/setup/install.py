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
	create_property_setters()
	ensure_default_settings()


def create_property_setters():
	"""Alter behavior of Education's own fields without touching its source
	(master.md's mandated mechanism for this — see docs/architecture.md section G).
	"""
	property_setters = [
		{
			# Student Attendance ships with Present/Absent/Leave only; the
			# master prompt (§24) needs Late/Excused too. "Leave" is kept for
			# backward compatibility with Education's leave_application link.
			"doctype": "Student Attendance",
			"fieldname": "status",
			"property": "options",
			"value": "Present\nAbsent\nLate\nExcused\nLeave",
		},
		{
			# Every modification to submitted marks must be auditable (§20).
			# Education doesn't turn this on by default.
			"doctype": "Assessment Result",
			"fieldname": None,
			"property": "track_changes",
			"value": "1",
		},
	]

	for ps in property_setters:
		_set_property(**ps)


def _set_property(doctype, fieldname, property, value):
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	# Property Setter has no natural autoname, so re-running this (e.g. a
	# second after_install, or a manual re-run during development) would
	# otherwise stack up duplicate rows - guard explicitly instead. Query by
	# SQL directly since `field_name` is NULL (not "") for doctype-level
	# properties, and dict-filter equality against None is unreliable.
	rows = frappe.db.sql(
		"""select name, value from `tabProperty Setter`
		where doc_type=%(doctype)s and property=%(property)s
		and field_name {op}""".format(op="is null" if fieldname is None else "= %(fieldname)s"),
		{"doctype": doctype, "property": property, "fieldname": fieldname},
		as_dict=True,
	)
	if rows:
		if rows[0].value != value:
			frappe.db.set_value("Property Setter", rows[0].name, "value", value)
		return

	property_type = "Check" if property == "track_changes" else "Text"
	make_property_setter(
		doctype,
		fieldname,
		property,
		value,
		property_type,
		for_doctype=fieldname is None,
	)


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
		# Phase 2 - grading engine (docs/architecture.md section G): Assessment
		# Plan has no notion of an assessment's category/coefficient upstream.
		"Assessment Plan": [
			{
				"fieldname": "assessment_type",
				"label": "Type d'évaluation",
				"fieldtype": "Link",
				"options": "Assessment Type",
				"insert_after": "assessment_group",
			},
			{
				"fieldname": "coefficient",
				"label": "Coefficient",
				"fieldtype": "Float",
				"default": "1",
				"description": "Pré-rempli depuis le Type d'évaluation ; modifiable pour ce plan précis.",
				"insert_after": "assessment_type",
			},
		],
		"Student Attendance": [
			{
				"fieldname": "remarks",
				"label": "Remarques",
				"fieldtype": "Small Text",
				"insert_after": "status",
			},
		],
	}
