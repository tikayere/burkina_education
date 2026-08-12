# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Scholarship / sibling-discount resolution, and the hook that applies the
combined percentage to a school-fee Sales Invoice (see docs/architecture.md
section H).

Nothing here posts GL entries or touches Fee Component rows directly - it
only sets Sales Invoice's own native ``additional_discount_percentage`` and
lets ERPNext's accounts controller do the actual math.
"""

import frappe


def get_siblings(student, academic_year):
	"""Students considered siblings of ``student``, ordered by creation
	(oldest first) so a stable 1-based rank can be derived. Includes
	``student`` itself.

	Two sources are unioned since either can be the one a school actually
	populates: Education's own ``Student.siblings`` child table (an explicit
	"studying in the same institute" declaration - the more directly-intended
	mechanism), and students sharing at least one Guardian (a looser signal
	that still catches families who never filled in the siblings table).
	"""
	sibling_names = set(
		frappe.get_all(
			"Student Sibling", filters={"parent": student, "parenttype": "Student", "student": ["is", "set"]}, pluck="student"
		)
	)

	guardians = frappe.get_all(
		"Student Guardian", filters={"parent": student, "parenttype": "Student"}, pluck="guardian"
	)
	if guardians:
		sibling_names.update(
			frappe.get_all(
				"Student Guardian",
				filters={"guardian": ["in", guardians], "parenttype": "Student"},
				pluck="parent",
			)
		)

	sibling_names.add(student)
	sibling_names = list(sibling_names)

	siblings = frappe.get_all(
		"Student",
		filters={"name": ["in", sibling_names], "enabled": 1},
		fields=["name", "creation"],
		order_by="creation asc",
	)
	if not any(s.name == student for s in siblings):
		# The student itself might be disabled (edge case) - keep it in its
		# own ranking regardless so the resolver below still has an answer.
		siblings.append(frappe._dict({"name": student, "creation": None}))

	return [s.name for s in siblings]


def sibling_rank(student, academic_year):
	siblings = get_siblings(student, academic_year)
	try:
		return siblings.index(student) + 1
	except ValueError:
		return 1


def sibling_discount_percent(student, academic_year):
	rules = frappe.get_single("Burkina Education Settings").sibling_discount_rules
	if not rules:
		return 0.0

	rank = sibling_rank(student, academic_year)
	# The applicable rule is the highest configured rank that is still <= the
	# student's rank (a rule for rank 3 also covers the 4th child, 5th, ...).
	applicable = [r for r in rules if (r.sibling_rank or 0) <= rank]
	if not applicable:
		return 0.0
	best = max(applicable, key=lambda r: r.sibling_rank or 0)
	return float(best.discount_percent or 0)


def scholarship_discount_percent(student, academic_year, fee_category=None):
	filters = {"student": student, "academic_year": academic_year, "status": "Approuvée"}
	scholarships = frappe.get_all(
		"Scholarship", filters=filters, fields=["discount_percent", "fee_category", "scholarship_type"]
	)
	# A scholarship left unscoped (no fee_category) applies to the whole
	# invoice; one scoped to a specific fee_category only counts when the
	# caller is evaluating that same category.
	applicable = [s for s in scholarships if not s.fee_category or s.fee_category == fee_category]
	if not applicable:
		return 0.0
	return max(float(s.discount_percent or 0) for s in applicable)


def resolve_discount_percent(student, academic_year, fee_category=None):
	"""Combined discount percentage (0-100) for one student/academic year,
	plus a short list of human-readable notes for the invoice remarks."""
	notes = []

	scholarship = scholarship_discount_percent(student, academic_year, fee_category)
	if scholarship >= 100:
		return 100.0, ["Bourse Totale"]
	if scholarship:
		notes.append(f"Bourse ({scholarship:g}%)")

	sibling = sibling_discount_percent(student, academic_year)
	if sibling:
		notes.append(f"Réduction fratrie, rang {sibling_rank(student, academic_year)} ({sibling:g}%)")

	combined = min(100.0, scholarship + sibling)
	return combined, notes


def apply_scholarship_and_sibling_discount(doc, method=None):
	"""``doc_events`` hook on Sales Invoice.validate - only acts on invoices
	generated from a school Fee Schedule (Education's ``student``/``fee_schedule``
	custom fields), never on an arbitrary ERPNext sale.
	"""
	if doc.docstatus != 0:
		return
	if not (doc.get("student") and doc.get("fee_schedule")):
		return

	academic_year = frappe.db.get_value("Fee Schedule", doc.fee_schedule, "academic_year")
	if not academic_year:
		return

	percent, notes = resolve_discount_percent(doc.student, academic_year)
	if not percent:
		return

	doc.apply_discount_on = "Grand Total"
	doc.additional_discount_percentage = percent

	note_text = f"Remise appliquée automatiquement : {', '.join(notes)} — total {percent:g}%."
	if note_text not in (doc.remarks or ""):
		doc.remarks = f"{doc.remarks}\n{note_text}" if doc.remarks else note_text

	# The controller's own validate() already ran (doc_events hooks fire
	# after it - see frappe.model.document.Document.hook), so totals need to
	# be recomputed now that the discount fields changed.
	doc.calculate_taxes_and_totals()
