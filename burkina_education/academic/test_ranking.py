# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.academic import ranking
from burkina_education.academic.tests.fixtures import AcademicFixture


class TestRankingEngine(FrappeTestCase):
	def setUp(self):
		self.fx = AcademicFixture()

	def _submit_report(self, student, score):
		self.fx.create_result(student, self.fx.term_1.name, self.fx.assessment_type_devoir, score=score)
		report = frappe.get_doc(
			{
				"doctype": "Student Term Report",
				"student": student.name,
				"student_group": self.fx.student_group.name,
				"academic_year": self.fx.academic_year.name,
				"academic_term": self.fx.term_1.name,
			}
		).insert(ignore_permissions=True)
		report.compute()
		report.submit()
		return report

	def test_rank_term_reports_orders_by_average_descending(self):
		report_low = self._submit_report(self.fx.students[0], score=8)
		report_high = self._submit_report(self.fx.students[1], score=18)

		ranking.rank_term_reports(self.fx.student_group.name, self.fx.term_1.name)

		self.assertEqual(frappe.db.get_value("Student Term Report", report_high.name, "class_rank"), 1)
		self.assertEqual(frappe.db.get_value("Student Term Report", report_low.name, "class_rank"), 2)
		self.assertEqual(frappe.db.get_value("Student Term Report", report_high.name, "class_size"), 2)

	def test_ranking_disabled_clears_rank(self):
		report = self._submit_report(self.fx.students[0], score=15)

		frappe.db.set_single_value("Burkina Education Settings", "ranking_enabled", 0)
		try:
			ranking.rank_term_reports(self.fx.student_group.name, self.fx.term_1.name)
			self.assertEqual(frappe.db.get_value("Student Term Report", report.name, "class_rank"), 0)
		finally:
			frappe.db.set_single_value("Burkina Education Settings", "ranking_enabled", 1)

	def test_tied_averages_share_a_rank_and_skip_the_next(self):
		# Both students score identically -> both rank 1st, and (were there a
		# third, lower-scoring student) the next rank would be 3rd, not 2nd.
		report_a = self._submit_report(self.fx.students[0], score=14)
		report_b = self._submit_report(self.fx.students[1], score=14)

		ranking.rank_term_reports(self.fx.student_group.name, self.fx.term_1.name)

		self.assertEqual(frappe.db.get_value("Student Term Report", report_a.name, "class_rank"), 1)
		self.assertEqual(frappe.db.get_value("Student Term Report", report_b.name, "class_rank"), 1)
