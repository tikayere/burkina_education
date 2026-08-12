# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Result-available notifications (master.md §32 example "Result available")
- ``doc_events`` hooks on Student Term Report / Student Annual Report
on_submit. See docs/architecture.md section J.
"""

import frappe

from burkina_education.messaging.notify import notify_event


def _guardians_of(student):
	return frappe.get_all("Student Guardian", filters={"parent": student}, pluck="guardian")


def notify_term_report_available(doc, method=None):
	guardians = _guardians_of(doc.student)
	if not guardians:
		return

	scheme = frappe.db.get_value("Grading Scheme", doc.grading_scheme, "passing_score") if doc.grading_scheme else None
	notify_event(
		"Result Available",
		guardians=guardians,
		students=[doc.student],
		context={
			"student_name": doc.student_name,
			"academic_term": frappe.db.get_value("Academic Term", doc.academic_term, "term_name") or doc.academic_term,
			"term_average": doc.term_average,
			"passing_score": scheme,
		},
		reference_doctype=doc.doctype,
		reference_name=doc.name,
	)


def notify_annual_report_available(doc, method=None):
	guardians = _guardians_of(doc.student)
	if not guardians:
		return

	notify_event(
		"Result Available",
		guardians=guardians,
		students=[doc.student],
		context={
			"student_name": doc.student_name,
			"academic_term": frappe.db.get_value("Academic Year", doc.academic_year, "academic_year_name")
			or doc.academic_year,
			"term_average": doc.annual_average,
			"passing_score": None,
		},
		reference_doctype=doc.doctype,
		reference_name=doc.name,
	)
