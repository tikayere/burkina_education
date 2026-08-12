# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from burkina_education.academic import grading


class StudentAnnualReport(Document):
	"""Rolls up a student's submitted ``Student Term Report``s for one
	Academic Year into an annual average (weighted by each Academic Term's
	``weight``, per the resolved Grading Scheme) - see docs/architecture.md
	section G.
	"""

	def validate(self):
		self.validate_duplicate()
		self.set_verification_code()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Student Annual Report",
			{"student": self.student, "academic_year": self.academic_year, "name": ["!=", self.name]},
		)
		if duplicate:
			frappe.throw(
				_("A Student Annual Report already exists for {0} in {1}: {2}").format(
					self.student, self.academic_year, duplicate
				)
			)

	def set_verification_code(self):
		if not self.verification_code:
			self.verification_code = frappe.generate_hash(length=12)

	@frappe.whitelist()
	def compute(self):
		if self.docstatus != 0:
			frappe.throw(_("Cannot recompute a submitted Student Annual Report. Amend it first."))

		scheme_name = self.grading_scheme or grading.resolve_grading_scheme(self.grade)
		if not scheme_name:
			frappe.throw(_("No Grading Scheme is configured. Create one before computing annual averages."))
		scheme = frappe.get_cached_doc("Grading Scheme", scheme_name)
		self.grading_scheme = scheme_name

		term_reports = frappe.get_all(
			"Student Term Report",
			filters={"student": self.student, "academic_year": self.academic_year, "docstatus": 1},
			fields=["name", "academic_term", "term_average"],
		)
		if not term_reports:
			frappe.throw(
				_(
					"No submitted Student Term Report found for {0} in {1}. Submit at least one term "
					"report first."
				).format(self.student, self.academic_year)
			)

		self.set("terms", [])
		term_rows = []
		for tr in term_reports:
			weight = frappe.db.get_value("Academic Term", tr.academic_term, "weight") or 1
			self.append(
				"terms",
				{
					"academic_term": tr.academic_term,
					"student_term_report": tr.name,
					"term_average": tr.term_average,
					"weight": weight,
				},
			)
			term_rows.append({"term_average": tr.term_average, "weight": weight})

		self.annual_average = grading.compute_annual_average(
			term_rows, method=scheme.annual_average_method, rounding=scheme.rounding_precision or 2
		)

		self.save()
		return self
