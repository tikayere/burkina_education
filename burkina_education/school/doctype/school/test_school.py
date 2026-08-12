# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSchool(FrappeTestCase):
	def test_school_code_is_uppercased(self):
		school = frappe.get_doc(
			{
				"doctype": "School",
				"school_name": "École de Test",
				"school_code": "test-code-1",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(school.name, "TEST-CODE-1")

	def test_duplicate_school_code_is_rejected(self):
		frappe.get_doc(
			{"doctype": "School", "school_name": "École A", "school_code": "DUPCODE"}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc(
				{"doctype": "School", "school_name": "École B", "school_code": "DUPCODE"}
			).insert(ignore_permissions=True)
