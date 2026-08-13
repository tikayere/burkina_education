# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Inventory & Assets (master.md §43): "Use ERPNext functionality where
practical." ERPNext's own Assets module (Asset/Asset Category/Location,
already reachable via the Employee-linked ``custodian`` field, plus
Asset Maintenance for upkeep) already covers location/custodian/maintenance
tracking end to end - see docs/architecture.md section K. The only genuine
gap is "condition" (a physical wear state - Bon état/Usé/À réparer/Hors
service), which Asset's own ``status`` field does not express (that field is
a lifecycle state: Draft/Submitted/Scrapped/...). Filled in with a Custom
Field, the same non-invasive-extension mechanism as every other
Education/ERPNext extension in this app (setup/install.py::get_custom_fields()).

Deliberately NOT a Frappe Module of its own (no new DocTypes here) - a
"burkina_education/assets" folder would collide with ERPNext's own "Assets"
Module Def by the exact same name-collision mechanism that broke Phase 4's
first attempt at a "Communication" module (docs/architecture.md section J);
named "inventory" instead, purely a Python namespace for this file.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

#: Furniture/Computers/Projectors/Lab Equipment/Sports Equipment (master.md
#: §43's list, minus "books" - those are Library's own Library Book/Library
#: Book Copy, not ERPNext Assets, see docs/architecture.md section K).
ASSET_CATEGORIES = [
	"Mobilier",
	"Matériel Informatique",
	"Équipement de Laboratoire",
	"Équipement Sportif",
]

ASSET_CONDITION_OPTIONS = "Bon état\nUsé\nÀ réparer\nHors service"


def get_asset_custom_fields():
	return {
		"Asset": [
			{
				"fieldname": "condition",
				"label": "État",
				"fieldtype": "Select",
				"options": ASSET_CONDITION_OPTIONS,
				"default": "Bon état",
				"insert_after": "custodian",
				"in_list_view": 1,
				"in_standard_filter": 1,
			}
		]
	}


def create_asset_custom_fields():
	create_custom_fields(get_asset_custom_fields(), ignore_validate=True)


def create_asset_permissions():
	"""School Director/IT Administrator get full rights on the ERPNext Assets
	doctypes this project relies on; deliberately not granted to any
	Academic-module role (mirrors Finance's Accountant boundary, section H)."""
	from frappe.permissions import add_permission, update_permission_property

	for doctype in ("Asset", "Asset Category", "Asset Movement", "Location"):
		for role in ("School Director", "IT Administrator"):
			add_permission(doctype, role, 0)
			for ptype in ("read", "write", "create", "print", "email", "report", "export"):
				update_permission_property(doctype, role, 0, ptype, 1)


#: category name -> keyword matched against an existing Fixed Asset account's
#: name under the demo Company (Standard chart of accounts already creates
#: one per broad asset type - see _pick_fixed_asset_account()).
_CATEGORY_ACCOUNT_KEYWORDS = {
	"Mobilier": "Furniture",
	"Matériel Informatique": "Electronic",
	"Équipement de Laboratoire": "Plants and Machineries",
	"Équipement Sportif": "Capital Equipments",
}


def seed_asset_categories(company):
	"""Idempotent catalog seed, called from demo data (setup/demo_data.py)
	*after* the demo Company exists - ``Asset Category.accounts`` is
	genuinely mandatory (company_name + fixed_asset_account per row), so this
	cannot run at install time the way create_asset_custom_fields()/
	create_asset_permissions() do (no Company exists yet then, see
	docs/architecture.md section H's own Company bootstrap note)."""
	created = []
	for name in ASSET_CATEGORIES:
		if frappe.db.exists("Asset Category", name):
			created.append(name)
			continue

		account = _pick_fixed_asset_account(company, _CATEGORY_ACCOUNT_KEYWORDS[name])
		if not account:
			continue

		frappe.get_doc(
			{
				"doctype": "Asset Category",
				"asset_category_name": name,
				"accounts": [{"company_name": company, "fixed_asset_account": account}],
			}
		).insert(ignore_permissions=True)
		created.append(name)
	return created


def _pick_fixed_asset_account(company, keyword):
	account = frappe.db.get_value(
		"Account", {"company": company, "account_type": "Fixed Asset", "name": ["like", f"%{keyword}%"]}
	)
	return account or frappe.db.get_value("Account", {"company": company, "account_type": "Fixed Asset"})
