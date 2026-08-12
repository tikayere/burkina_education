# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic import grading


class TestGradingScheme(FrappeTestCase):
	def setUp(self):
		# Demo data (setup/demo_data.py) may have already installed a real
		# global-default Grading Scheme ("Barème Général") - deactivate any
		# such rows for the duration of this test so it doesn't collide with
		# the single-active-default-per-scope rule under test. FrappeTestCase
		# rolls the whole transaction back afterwards.
		frappe.db.sql(
			"""update `tabGrading Scheme` set is_default = 0
			where is_default = 1 and (education_level is null or education_level = '')"""
		)

	def test_global_default_is_resolved_when_education_level_is_blank(self):
		"""Regression test: an unset Link field is stored as NULL, not "" -
		resolve_grading_scheme() and validate_single_default() both have to
		use the "is not set" operator, not an equality filter, to find it."""
		tag = frappe.generate_hash(length=6).upper()
		scheme = frappe.get_doc(
			{
				"doctype": "Grading Scheme",
				"scheme_name": f"Global {tag}",
				"score_max": 20,
				"passing_score": 10,
				"is_default": 1,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(grading.resolve_grading_scheme(grade=None), scheme.name)

	def test_second_global_default_is_rejected(self):
		tag = frappe.generate_hash(length=6).upper()
		frappe.get_doc(
			{
				"doctype": "Grading Scheme",
				"scheme_name": f"Global A {tag}",
				"score_max": 20,
				"passing_score": 10,
				"is_default": 1,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Grading Scheme",
					"scheme_name": f"Global B {tag}",
					"score_max": 20,
					"passing_score": 10,
					"is_default": 1,
					"is_active": 1,
				}
			).insert(ignore_permissions=True)
