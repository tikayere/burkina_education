# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Ranking engine (master.md §23): class/term/annual rank with tie handling,
gated by ``Burkina Education Settings.ranking_enabled``. Only ``Student Term
Report``/``Student Annual Report`` rows that are *submitted* (locked) are
ranked - ranking a class before every teacher has finished entering marks
would be misleading.

Rank fields are updated directly via ``db_set`` rather than a full
``doc.save()``: these documents are submitted/locked, and ranking is an
annotation step that runs across a whole class at once (not a single-document
edit a user is expected to review field-by-field).
"""

import frappe
from frappe import _


def ranking_enabled():
	return bool(frappe.db.get_single_value("Burkina Education Settings", "ranking_enabled"))


def _assign_ranks(rows, value_field):
	"""Standard competition ranking ("1224"): equal values share a rank, and
	the next distinct value's rank accounts for how many were tied ahead of
	it. ``rows`` must already be sorted best-first.
	"""
	ranked = []
	previous_value = None
	previous_rank = 0
	for index, row in enumerate(rows, start=1):
		value = row[value_field]
		rank = previous_rank if value == previous_value else index
		ranked.append((row["name"], rank))
		previous_value, previous_rank = value, rank
	return ranked


@frappe.whitelist()
def rank_term_reports(student_group, academic_term):
	"""Rank every submitted Student Term Report for one Student Group/Academic
	Term by ``term_average`` (descending). Returns the ranked list.
	"""
	frappe.has_permission("Student Term Report", "write", throw=True)

	rows = frappe.get_all(
		"Student Term Report",
		filters={"student_group": student_group, "academic_term": academic_term, "docstatus": 1},
		fields=["name", "term_average"],
		order_by="term_average desc",
	)

	class_size = len(rows)
	if not ranking_enabled():
		for row in rows:
			frappe.db.set_value(
				"Student Term Report", row.name, {"class_rank": 0, "class_size": class_size}
			)
		return rows

	for name, rank in _assign_ranks(rows, "term_average"):
		frappe.db.set_value("Student Term Report", name, {"class_rank": rank, "class_size": class_size})

	return rows


@frappe.whitelist()
def rank_annual_reports(grade, academic_year):
	"""Rank every submitted Student Annual Report for one Grade/Academic Year
	by ``annual_average`` (descending)."""
	frappe.has_permission("Student Annual Report", "write", throw=True)

	rows = frappe.get_all(
		"Student Annual Report",
		filters={"grade": grade, "academic_year": academic_year, "docstatus": 1},
		fields=["name", "annual_average"],
		order_by="annual_average desc",
	)

	class_size = len(rows)
	if not ranking_enabled():
		for row in rows:
			frappe.db.set_value(
				"Student Annual Report", row.name, {"annual_rank": 0, "class_size": class_size}
			)
		return rows

	for name, rank in _assign_ranks(rows, "annual_average"):
		frappe.db.set_value("Student Annual Report", name, {"annual_rank": rank, "class_size": class_size})

	return rows
