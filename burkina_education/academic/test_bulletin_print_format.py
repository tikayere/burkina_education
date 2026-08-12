# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.www.printview import get_html_and_style

from burkina_education.academic.tests.fixtures import AcademicFixture


class TestBulletinPrintFormat(FrappeTestCase):
	def setUp(self):
		self.fx = AcademicFixture()

	def test_bulletin_renders_without_error(self):
		student = self.fx.students[0]
		self.fx.create_result(student, self.fx.term_1.name, self.fx.assessment_type_devoir, score=14)

		report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
				"teacher_comment": "Bon trimestre.",
			}
		).insert(ignore_permissions=True)
		report.compute()
		report.submit()

		result = get_html_and_style(doc="Student Term Report", name=report.name, print_format="Bulletin Burkina")

		self.assertIn(student.student_name, result["html"])
		self.assertIn("14.00", result["html"])
		self.assertIn(report.verification_code, result["html"])
