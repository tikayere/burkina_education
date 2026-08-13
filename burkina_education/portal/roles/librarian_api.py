# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Librarian Portal. Plain catalog/membership
CRUD (Library Book, Library Author, Library Category, Library Membership)
is done directly from the frontend via ``frappe-ui``'s generic list/document
resources — the Librarian role already has full permissions on those
doctypes (docs/architecture.md section M). This module supplies only the
dashboard and the two-step "issue"/"return" workflow, where
``Library Transaction``'s own controller (status transitions, fine
computation, copy-status sync — see that doctype's ``validate``/
``on_update``) already does the actual business logic; these functions just
save the Librarian from having to look up a membership/an available copy by
hand first.
"""

import frappe
from frappe.utils import nowdate

from burkina_education.portal.permissions import require_any_role

OPEN_STATUSES = ("Emprunté", "En retard")


@frappe.whitelist()
def get_dashboard():
	require_any_role("Librarian")

	books = frappe.db.count("Library Book")
	copies = frappe.db.count("Library Book Copy")
	available = frappe.db.count("Library Book Copy", {"status": "Disponible"})
	checked_out = frappe.db.count("Library Transaction", {"status": ["in", OPEN_STATUSES]})
	overdue = frappe.db.count("Library Transaction", {"status": "En retard"}) + frappe.db.count(
		"Library Transaction", {"status": "Emprunté", "due_date": ["<", nowdate()]}
	)
	active_members = frappe.db.count("Library Membership", {"status": "Active"})

	due_soon = frappe.get_all(
		"Library Transaction",
		filters={"status": "Emprunté", "due_date": ["between", (nowdate(), frappe.utils.add_days(nowdate(), 3))]},
		fields=["name", "book_title", "student", "due_date"],
		order_by="due_date asc",
		limit=10,
	)
	overdue_list = frappe.get_all(
		"Library Transaction",
		filters={"status": ["in", ("En retard",)]},
		fields=["name", "book_title", "student", "due_date", "fine_amount"],
		order_by="due_date asc",
		limit=10,
	)

	return {
		"books": books,
		"copies": copies,
		"available": available,
		"checked_out": checked_out,
		"overdue": overdue,
		"active_members": active_members,
		"due_soon": due_soon,
		"overdue_list": overdue_list,
	}


@frappe.whitelist()
def find_member(student):
	"""Membership + current open loans for one student — used by the "issue
	a book" dialog to show the Librarian whether the member can still
	borrow before they pick a book."""
	require_any_role("Librarian")

	membership = frappe.db.get_value(
		"Library Membership",
		{"student": student},
		["name", "student_name", "status", "max_books", "expiry_date"],
		as_dict=True,
	)
	if not membership:
		return None

	open_loans = frappe.get_all(
		"Library Transaction",
		filters={"membership": membership.name, "status": ["in", OPEN_STATUSES]},
		fields=["name", "book_title", "due_date", "status"],
	)
	membership["open_loans"] = open_loans
	membership["can_borrow"] = membership.status == "Active" and len(open_loans) < (membership.max_books or 0)
	return membership


@frappe.whitelist()
def issue_book(student, book):
	"""Issue any one available copy of ``book`` to ``student``'s membership —
	the Librarian picks a title, not a specific barcode/copy."""
	require_any_role("Librarian")

	membership = frappe.db.get_value("Library Membership", {"student": student}, "name")
	if not membership:
		frappe.throw(frappe._("Cet élève n'a pas d'adhésion à la bibliothèque."))

	copy_name = frappe.db.get_value("Library Book Copy", {"book": book, "status": "Disponible"}, "name")
	if not copy_name:
		frappe.throw(frappe._("Aucun exemplaire disponible pour ce livre."))

	doc = frappe.get_doc(
		{
			"doctype": "Library Transaction",
			"membership": membership,
			"book_copy": copy_name,
			"issue_date": nowdate(),
			"status": "Emprunté",
		}
	).insert()
	return doc.name


@frappe.whitelist()
def return_book(transaction, lost=False):
	doc = frappe.get_doc("Library Transaction", transaction)
	frappe.has_permission(doc.doctype, "write", doc, throw=True)
	if doc.status not in OPEN_STATUSES:
		frappe.throw(frappe._("Cet emprunt est déjà clos."))

	if frappe.parse_json(lost) if isinstance(lost, str) else lost:
		doc.status = "Perdu"
	else:
		doc.return_date = nowdate()
		doc.status = "Retourné"
	doc.save()
	return {"name": doc.name, "status": doc.status, "fine_amount": doc.fine_amount}
