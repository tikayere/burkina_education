# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Grading engine glue: the cancel guard on Education's ``Assessment Result``,
and the weighted-average helpers used by ``Student Term Report``/``Student
Annual Report`` (see docs/architecture.md section G).

No formula here is hard-coded per school - everything reads its parameters
from ``Grading Scheme``.
"""

import frappe
from frappe import _

#: Roles allowed to cancel (and therefore amend) a locked Assessment Result.
#: Kept as a hook rather than rewriting the DocType's permissions - see
#: docs/architecture.md section G for why.
ASSESSMENT_RESULT_CANCEL_ROLES = {"Academic Director", "Examination Coordinator", "System Manager"}


def guard_assessment_result_cancel(doc, method=None):
	if frappe.session.user == "Administrator":
		return

	user_roles = set(frappe.get_roles(frappe.session.user))
	if user_roles & ASSESSMENT_RESULT_CANCEL_ROLES:
		return

	frappe.throw(
		_(
			"Marks have already been submitted (locked). Only an Academic Director or "
			"Examination Coordinator can cancel/amend a submitted Assessment Result."
		),
		frappe.PermissionError,
	)
