# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Grade(Document):
	"""A Burkina-style class/grade (e.g. "6ème", "CP1").

	Education's fee, enrollment and assessment engine is keyed off ``Program``,
	so every Grade owns exactly one Program under the hood (see
	docs/architecture.md, section B). Users never see or manage the Program
	directly - it is created and named automatically here.
	"""

	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Grade",
			{
				"cycle": self.cycle,
				"grade_name": self.grade_name,
				"stream": self.stream,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(_("Grade {0} already exists for this Cycle").format(frappe.bold(self.grade_name)))

	def after_insert(self):
		self.create_linked_program()

	def create_linked_program(self):
		if self.program:
			return

		program_name = f"{self.grade_name} ({self.school})"
		if frappe.db.exists("Program", program_name):
			program_name = f"{self.grade_name} ({self.school}) - {self.name[-6:]}"

		program = frappe.get_doc(
			{
				"doctype": "Program",
				"program_name": program_name,
				"program_abbreviation": self.grade_name[:140],
			}
		).insert(ignore_permissions=True)

		self.db_set("program", program.name, update_modified=False)

	def on_trash(self):
		# force=1: at this point in on_trash the Grade row itself still exists,
		# so the link-exists check would otherwise block deletion on the very
		# Grade->Program link we are cleaning up.
		if self.program and not frappe.db.exists("Program Enrollment", {"program": self.program}):
			frappe.delete_doc(
				"Program", self.program, ignore_permissions=True, ignore_missing=True, force=1
			)
