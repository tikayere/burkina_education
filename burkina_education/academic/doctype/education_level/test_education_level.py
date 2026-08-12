# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestEducationLevel(FrappeTestCase):
	def setUp(self):
		code = frappe.generate_hash(length=6).upper()
		self.school = frappe.get_doc(
			{"doctype": "School", "school_name": f"Test School {code}", "school_code": code}
		).insert(ignore_permissions=True)

	def test_duplicate_education_level_in_same_school_is_rejected(self):
		frappe.get_doc(
			{
				"doctype": "Education Level",
				"education_level_name": "Primaire",
				"school": self.school.name,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Education Level",
					"education_level_name": "Primaire",
					"school": self.school.name,
				}
			).insert(ignore_permissions=True)

	def test_instructor_cannot_create_education_level(self):
		"""A Teacher (Instructor) may read the academic structure but not edit it -
		that is Academic Director / School Director territory (docs/architecture.md
		section D)."""
		user = get_or_create_test_user("instructor_perm_test@example.com", ["Instructor"])

		with self.set_user(user.name):
			doc = frappe.get_doc(
				{
					"doctype": "Education Level",
					"education_level_name": "Secondaire",
					"school": self.school.name,
				}
			)
			with self.assertRaises(frappe.PermissionError):
				doc.insert()

	def test_academic_director_can_create_education_level(self):
		user = get_or_create_test_user("academic_director_perm_test@example.com", ["Academic Director"])

		with self.set_user(user.name):
			doc = frappe.get_doc(
				{
					"doctype": "Education Level",
					"education_level_name": "Technique",
					"school": self.school.name,
				}
			).insert()

		self.assertTrue(frappe.db.exists("Education Level", doc.name))


def get_or_create_test_user(email, roles):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Test",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)

	existing_roles = {r.role for r in user.roles}
	for role in roles:
		if role not in existing_roles:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)
	return user
