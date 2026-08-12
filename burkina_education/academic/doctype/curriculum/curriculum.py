# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Curriculum(Document):
	"""One Grade's syllabus for one Subject in one Academic Year: the root of
	Competency -> Learning Objective and Learning Unit -> Lesson (master.md §17).

	Content (competencies, lessons, ...) is entirely user-authored - nothing
	here is hard-coded, per §17's explicit instruction.
	"""

	def validate(self):
		self.validate_duplicate()
		self.set_title()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Curriculum",
			{
				"grade": self.grade,
				"course": self.course,
				"academic_year": self.academic_year,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				_("A Curriculum already exists for {0} / {1} / {2}").format(
					self.grade, self.course, self.academic_year
				)
			)

	def set_title(self):
		self.title = f"{self.grade} - {self.course} ({self.academic_year})"
