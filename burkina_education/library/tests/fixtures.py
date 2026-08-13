# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe

from burkina_education.school.tests.fixtures import MinimalSchoolFixture


class LibraryFixture(MinimalSchoolFixture):
	"""Adds one Library Book with two copies and one active Library
	Membership on top of the shared School/Grade/Student chain."""

	def __init__(self):
		super().__init__()

		self.author = frappe.get_doc(
			{"doctype": "Library Author", "author_name": f"Auteur {self.tag}"}
		).insert(ignore_permissions=True)

		self.book = frappe.get_doc(
			{"doctype": "Library Book", "title": f"Livre {self.tag}", "author": self.author.name}
		).insert(ignore_permissions=True)

		self.copy_1 = frappe.get_doc(
			{"doctype": "Library Book Copy", "book": self.book.name}
		).insert(ignore_permissions=True)
		self.copy_2 = frappe.get_doc(
			{"doctype": "Library Book Copy", "book": self.book.name}
		).insert(ignore_permissions=True)

		self.membership = frappe.get_doc(
			{
				"doctype": "Library Membership",
				"student": self.student.name,
				"max_books": 1,
			}
		).insert(ignore_permissions=True)
