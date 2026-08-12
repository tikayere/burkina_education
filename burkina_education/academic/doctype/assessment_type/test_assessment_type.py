# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestAssessmentType(FrappeTestCase):
	def test_create_and_reuse_default_coefficient(self):
		name = f"Devoir {frappe.generate_hash(length=6)}"
		doc = frappe.get_doc(
			{
				"doctype": "Assessment Type",
				"type_name": name,
				"category": "Devoir",
				"default_coefficient": 1,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(doc.name, name)
		self.assertEqual(frappe.db.get_value("Assessment Type", name, "default_coefficient"), 1)

	def test_duplicate_type_name_is_rejected(self):
		name = f"Composition {frappe.generate_hash(length=6)}"
		frappe.get_doc(
			{
				"doctype": "Assessment Type",
				"type_name": name,
				"category": "Composition",
				"default_coefficient": 2,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc(
				{
					"doctype": "Assessment Type",
					"type_name": name,
					"category": "Composition",
					"default_coefficient": 3,
				}
			).insert(ignore_permissions=True)
