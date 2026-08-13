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
	# Phase 3 (Finance, docs/architecture.md section H): master.md §3 names
	"Accountant",  # this role specifically; ERPNext's own "Accounts Manager"/
	# "Accounts User" are broader (multi-company, HR-adjacent) and not reused.
]

#: Finance doctypes (ours + stock Frappe/ERPNext/Education ones) the
#: Accountant role needs — deliberately does NOT include any Academic-module
#: doctype (master.md §64: "accountant cannot modify grades").
ACCOUNTANT_DOCTYPES_FULL = [
	"Sales Invoice",
	"Sales Order",
	"Payment Entry",
	"Payment Request",
	"Fee Category",
	"Fee Structure",
	"Fee Schedule",
	"Fees",
]


def after_install():
	create_roles()
	create_custom_fields(get_custom_fields(), ignore_validate=True)
	create_property_setters()
	create_client_scripts()
	create_finance_permissions()
	create_portal_permissions()
	create_department_head_permissions()
	create_receptionist_permissions()
	enable_xof_currency()
	ensure_item_group_root()
	ensure_stock_uom_default()
	ensure_erpnext_custom_fields()
	ensure_default_price_lists()
	ensure_default_settings()

	# Discipline/Clinic/Library/Transport/Canteen/Boarding DocTypes are all
	# ours (Phase 5) - their role grants live directly in each DocType's own
	# JSON permissions table (the pattern already used for Scholarship etc.),
	# not here. Only the ERPNext Assets doctypes below need the
	# add_permission/Custom DocPerm mechanism, since we don't own them.
	# seed_asset_categories() is NOT called here - it needs a real Company
	# (Asset Category.accounts is mandatory), which doesn't exist until demo
	# data creates one (setup/demo_data.py::create_asset_categories_demo()).
	from burkina_education.inventory.setup import create_asset_custom_fields, create_asset_permissions

	create_asset_custom_fields()
	create_asset_permissions()


#: Education/ERPNext DocTypes that are frequently picked from a Link field
#: across this app (school.doctype.school.json § "most-linked" audit) and
#: already ship a sensible ``title_field`` upstream, but not
#: ``show_title_field_in_link`` — without it, every Link dropdown/awesomebar
#: search result shows only the opaque autoname (e.g. "EDU-GRD-2024-00042"
#: for a Guardian) instead of the human name next to it. Frappe's own
#: Student/Course/Academic Year etc. don't need this (their autoname already
#: *is* the readable field), so only the doctypes below are missing it.
TITLE_LINK_DOCTYPES = [
	"Guardian",
	"Instructor",
	"Room",
	"Fees",
	"Fee Structure",
	"Employee",
	"Driver",
]


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
	property_setters += [
		{"doctype": dt, "fieldname": None, "property": "show_title_field_in_link", "value": "1"}
		for dt in TITLE_LINK_DOCTYPES
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

	property_type = "Check" if property in ("track_changes", "show_title_field_in_link") else "Text"
	make_property_setter(
		doctype,
		fieldname,
		property,
		value,
		property_type,
		for_doctype=fieldname is None,
	)


#: Client Scripts that extend a *stock* Frappe/ERPNext/Education DocType's
#: Desk UI without touching its source - the JS equivalent of
#: create_property_setters() above. Our own DocTypes get their client
#: scripts the normal way (a same-named .js file next to the .json), so this
#: list only needs an entry per vendor DocType we extend.
CLIENT_SCRIPTS = [
	{
		"name": "Burkina Education: Sales Invoice Mobile Money Button",
		"dt": "Sales Invoice",
		"view": "Form",
		"script_path": ("finance", "client_scripts", "sales_invoice_mobile_money.js"),
	},
	{
		"name": "Burkina Education: Guardian Portal Invite Button",
		"dt": "Guardian",
		"view": "Form",
		"script_path": ("messaging", "client_scripts", "guardian_portal_invite.js"),
	},
	{
		"name": "Burkina Education: Student Portal Invite Button",
		"dt": "Student",
		"view": "Form",
		"script_path": ("messaging", "client_scripts", "student_portal_invite.js"),
	},
]


def create_client_scripts():
	for spec in CLIENT_SCRIPTS:
		script_path = frappe.get_app_path("burkina_education", *spec["script_path"])
		with open(script_path) as f:
			script = f.read()

		existing = frappe.db.get_value("Client Script", {"dt": spec["dt"], "view": spec["view"]})
		if existing:
			frappe.db.set_value("Client Script", existing, "script", script)
			continue

		# Client Script has no autoname (autoname: "Prompt") - an explicit
		# name is mandatory or insert() throws "Please set the document name".
		frappe.get_doc(
			{
				"doctype": "Client Script",
				"name": spec["name"],
				"dt": spec["dt"],
				"view": spec["view"],
				"script": script,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)


def create_roles():
	for role in NEW_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def create_finance_permissions():
	"""Grant the Accountant role full rights on Sales Invoice/Payment
	Entry/Fee* — the same mechanism (Custom DocPerm via ``add_permission``)
	Education's own ``install.py`` uses to grant the Student role rights on
	Sales Invoice, so it composes rather than replacing standard permission
	rows (docs/architecture.md section H).
	"""
	from frappe.permissions import add_permission, update_permission_property

	for doctype in ACCOUNTANT_DOCTYPES_FULL:
		add_permission(doctype, "Accountant", 0)
		for ptype in ("read", "write", "create", "print", "email", "report", "export"):
			update_permission_property(doctype, "Accountant", 0, ptype, 1)


#: Doctypes the Guardian/Student Portals need plain **read** access to
#: (``/printview``, the portal's own whitelisted API calls). This alone
#: would let any Guardian/Student read *any* record - narrowed down to only
#: their own children/own record by the ``has_permission`` hook in hooks.py
#: (messaging/permissions.py), which can only ever deny, never grant.
PORTAL_READ_ONLY_DOCTYPES = ["Student Term Report", "Student Annual Report", "Student Attendance", "Sales Invoice"]


def create_portal_permissions():
	from frappe.permissions import add_permission, update_permission_property

	for doctype in PORTAL_READ_ONLY_DOCTYPES:
		for role in ("Guardian", "Student"):
			add_permission(doctype, role, 0)
			update_permission_property(doctype, role, 0, "read", 1)


#: Same doctypes/permission level Instructor already gets (education's own
#: install.py) - a Department Head oversees a subject/department across
#: several teachers, so needs the same curriculum-authoring rights as any one
#: of them, not the full Academic Director set (no Discipline, Scholarship,
#: School, or Settings access). Curriculum itself stays read-only (the
#: Academic Director defines *which* curriculum applies to which
#: grade/subject; a Department Head fills it in - competencies, units,
#: lessons - underneath). Portal wiring: portal/roles/__init__.py,
#: frontend/src/session.js, frontend/src/navigation.js (docs/architecture.md
#: section N).
DEPARTMENT_HEAD_PEDAGOGY_DOCTYPES = {
	"Curriculum": ("read", "report"),
	"Competency": ("read", "report", "write", "create", "print", "email"),
	"Learning Unit": ("read", "report", "write", "create", "print", "email"),
	"Lesson": ("read", "report", "write", "create", "print", "email"),
	"Learning Objective": ("read", "report", "write", "create", "print", "email"),
	# Read-only: Department Head links an existing Course into a
	# Curriculum/Lesson, but doesn't own the Course master itself.
	"Course": ("read", "report"),
}


def create_department_head_permissions():
	from frappe.permissions import add_permission, update_permission_property

	for doctype, ptypes in DEPARTMENT_HEAD_PEDAGOGY_DOCTYPES.items():
		add_permission(doctype, "Department Head", 0)
		for ptype in ptypes:
			update_permission_property(doctype, "Department Head", 0, ptype, 1)


#: A Receptionist's whole job here is answering "who is this / how do I
#: reach their guardian" at the front desk - read-only is deliberate (they
#: triage and redirect, they don't maintain records - master.md §54 "least
#: privilege"). Portal wiring: portal/roles/__init__.py,
#: frontend/src/session.js, frontend/src/navigation.js (docs/architecture.md
#: section N).
RECEPTIONIST_READ_ONLY_DOCTYPES = ["Student", "Guardian"]


def create_receptionist_permissions():
	from frappe.permissions import add_permission, update_permission_property

	for doctype in RECEPTIONIST_READ_ONLY_DOCTYPES:
		add_permission(doctype, "Receptionist", 0)
		for ptype in ("read", "report"):
			update_permission_property(doctype, "Receptionist", 0, ptype, 1)


def enable_xof_currency():
	"""XOF (Franc CFA) ships disabled by default; the Setup Wizard would
	normally enable a school's chosen currency — skipped in this dev
	environment (see docs/installation.md), so enable it explicitly here."""
	if not frappe.db.get_value("Currency", "XOF", "enabled"):
		frappe.db.set_value("Currency", "XOF", "enabled", 1)


def ensure_erpnext_custom_fields():
	"""``erpnext.setup.install.create_address_and_contact_custom_fields()``
	(which adds ``Contact.is_billing_contact`` — read unconditionally by
	``erpnext.accounts.party.get_default_contact``) normally runs as part of
	``erpnext``'s own ``after_install`` when ``erpnext`` itself is installed,
	but was missing on this dev site. Calling just this one function (not the
	full ``after_install``, which also touches Role Profiles and other
	state that isn't safe to insert twice) closes the gap; ``create_custom_fields``
	is idempotent on its own."""
	from erpnext.setup.install import create_address_and_contact_custom_fields

	create_address_and_contact_custom_fields()


#: Deliberately NOT named "Standard Buying"/"Standard Selling" - ERPNext's own
#: generic test bootstrap (``erpnext.tests.utils.BootStrapTestData.make_price_list``)
#: hardcodes those exact names with ``currency: "INR"``, and its existence
#: check matches on name+currency+buying+selling together, so an XOF version
#: under the same name doesn't satisfy it and it tries (and fails) to insert
#: a second "Standard Buying"/"Standard Selling" - a duplicate key. Distinct
#: names sidestep the collision entirely; only Selling/Buying Settings need
#: to point at them, nothing else references these by their literal name.
XOF_PRICE_LISTS = (("Standard Buying (XOF)", 0), ("Standard Selling (XOF)", 1))


def ensure_default_price_lists():
	"""Price Lists are normally created by the Setup Wizard
	(``install_fixtures.install_defaults``) — skipped in this dev environment.
	Without one, every Sales Invoice fails mandatory validation on
	``selling_price_list``/``price_list_currency`` regardless of which Company
	it's for, so these are created once, XOF, shared across every company
	(Price List isn't company-scoped in ERPNext)."""
	for name, selling in XOF_PRICE_LISTS:
		if frappe.db.exists("Price List", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": name,
				"enabled": 1,
				"buying": 0 if selling else 1,
				"selling": selling,
				"currency": "XOF",
			}
		).insert(ignore_permissions=True)

	selling_name = XOF_PRICE_LISTS[1][0]
	buying_name = XOF_PRICE_LISTS[0][0]
	if not frappe.db.get_single_value("Selling Settings", "selling_price_list"):
		frappe.db.set_single_value("Selling Settings", "selling_price_list", selling_name)
	if not frappe.db.get_single_value("Buying Settings", "buying_price_list"):
		frappe.db.set_single_value("Buying Settings", "buying_price_list", buying_name)


def ensure_item_group_root():
	"""Education's Fee Category creates its ``Item``s under an ad-hoc "Fee
	Component" Item Group (see ``create_item()`` in Education's fee_category.py)
	without first checking that ERPNext's own canonical root ("All Item
	Groups", normally seeded by the Setup Wizard — skipped here, see
	``ensure_default_price_lists()`` above) exists. ``get_root_of()`` then
	picks "Fee Component" itself up as the tree's root, so it's stuck with no
	parent — invalid ERPNext data (a rootless non-"All Item Groups" node) that
	only surfaces when something needs the real root by its hardcoded name,
	e.g. ERPNext's own test fixtures (``erpnext.tests.utils.make_item_group``).
	Idempotent: re-parents the ad-hoc root under the canonical one and rebuilds
	the nested set, safe to re-run."""
	from frappe.utils.nestedset import rebuild_tree

	root_name = "All Item Groups"
	if not frappe.db.exists("Item Group", root_name):
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": root_name,
				"is_group": 1,
				"parent_item_group": "",
			}
		).insert(ignore_permissions=True)

	stray_root = frappe.db.get_value(
		"Item Group", {"parent_item_group": ["in", ["", None]], "name": ["!=", root_name]}
	)
	if stray_root:
		frappe.db.set_value("Item Group", stray_root, "parent_item_group", root_name)
		if frappe.db.count("Item Group", {"parent_item_group": stray_root}):
			# It has children of its own now (e.g. "Fee Component" > "Products"/
			# "Services"/...) so it must be flagged as a group, or ERPNext's own
			# Item Group validation rejects it.
			frappe.db.set_value("Item Group", stray_root, "is_group", 1)
		rebuild_tree("Item Group")


def ensure_stock_uom_default():
	"""Education's Fee Category auto-creates a (non-stock, service) Item per
	fee component, but never sets ``stock_uom`` — normally pre-filled by the
	Setup Wizard/Item form JS, neither of which run for a server-side insert
	in this headless dev environment (see docs/installation.md). A Property
	Setter default is the same mechanism the Setup Wizard itself would have
	used, and it's honoured by any new-document creation, not just the UI."""
	_set_property("Item", "stock_uom", "default", "Nos")


def ensure_default_settings():
	"""A Single doctype's ``"default"`` in its JSON only ever gets written to
	``tabSingles`` the moment the field is first added while the Single has
	no row yet - a field added later via ``reload-doctype`` on an
	already-installed site (like Phase 5's ``library_loan_period_days``/
	``library_fine_per_day``) leaves that row missing, and
	``get_single_value`` then returns ``None``, not the JSON default (the
	same class of environment-bootstrap gap as Phase 3's ``Item.stock_uom``
	default - see docs/installation.md's quirks list). Filled in explicitly
	here rather than relied on implicitly.
	"""
	settings = frappe.get_single("Burkina Education Settings")
	if not settings.default_currency:
		settings.default_currency = "XOF"
	if not settings.default_language:
		settings.default_language = "fr"
	if not settings.library_loan_period_days:
		settings.library_loan_period_days = 14
	if not settings.library_fine_per_day:
		settings.library_fine_per_day = 25
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
				# Phase 4 (Communication, docs/architecture.md section J) - WhatsApp
				# gets its own opt-in, independent of sms_consent (master.md §34:
				# "opt-in/opt-out" per channel, a guardian may want one but not
				# the other).
				"fieldname": "whatsapp_consent",
				"label": "Consentement WhatsApp",
				"fieldtype": "Check",
				"insert_after": "sms_consent",
			},
			{
				"fieldname": "portal_access",
				"label": "Accès au portail parent",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "whatsapp_consent",
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
