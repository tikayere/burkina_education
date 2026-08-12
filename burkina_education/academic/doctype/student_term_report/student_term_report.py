# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from burkina_education.academic import grading


class StudentTermReport(Document):
	"""One student's computed report for one Academic Term: subject averages,
	term average, class rank, attendance summary. Computed from submitted
	Education ``Assessment Result``s and ``Student Attendance`` - see
	``academic/grading.py`` for the (fully configurable, not hard-coded)
	math, and docs/architecture.md section G for the overall design.
	"""

	def validate(self):
		self.validate_duplicate()
		self.set_verification_code()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Student Term Report",
			{"student": self.student, "academic_term": self.academic_term, "name": ["!=", self.name]},
		)
		if duplicate:
			frappe.throw(
				_("A Student Term Report already exists for {0} in {1}: {2}").format(
					self.student, self.academic_term, duplicate
				)
			)

	def set_verification_code(self):
		if not self.verification_code:
			self.verification_code = frappe.generate_hash(length=12)

	@frappe.whitelist()
	def compute(self):
		"""(Re)compute subject averages, term average and attendance from
		submitted Assessment Results / Student Attendance. Safe to call
		repeatedly while the report is still in Draft; a submitted report is
		locked (call amend first, matching the rest of the app's marks-lock
		policy)."""
		if self.docstatus != 0:
			frappe.throw(_("Cannot recompute a submitted Student Term Report. Amend it first."))

		scheme_name = self.grading_scheme or grading.resolve_grading_scheme(self.grade)
		if not scheme_name:
			frappe.throw(
				_(
					"No Grading Scheme is configured (for this Education Level, or as a global "
					"default). Create one before computing report averages."
				)
			)
		scheme = frappe.get_cached_doc("Grading Scheme", scheme_name)
		self.grading_scheme = scheme_name

		subject_rows = grading.compute_subject_results(
			self.student,
			self.academic_term,
			use_coefficients=bool(scheme.use_coefficients),
			score_max=scheme.score_max,
			rounding=scheme.rounding_precision or 2,
		)

		self.set("subjects", [])
		for row in subject_rows:
			self.append("subjects", row)

		self.term_average = grading.compute_term_average(
			subject_rows,
			use_coefficients=bool(scheme.use_coefficients),
			method=scheme.term_average_method,
			rounding=scheme.rounding_precision or 2,
		)
		self.max_average = scheme.score_max

		from_date, to_date = frappe.db.get_value(
			"Academic Term", self.academic_term, ["term_start_date", "term_end_date"]
		)
		if from_date and to_date:
			attendance = grading.get_attendance_summary(self.student, from_date, to_date)
			self.attendance_present = attendance["present"]
			self.attendance_absent = attendance["absent"]
			self.attendance_late = attendance["late"]
			self.attendance_percentage = attendance["percentage"]

		self.save()
		return self
