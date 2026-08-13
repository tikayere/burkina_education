# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class TransportRoute(Document):
	def validate(self):
		self._autofill_stop_sequence()

	def _autofill_stop_sequence(self):
		"""A stop left blank keeps the row order it was entered in, mirroring
		the auto-sequencing pattern already used for Curriculum/Lesson rows
		(docs/architecture.md section I)."""
		for row in self.stops:
			if not row.sequence:
				row.sequence = row.idx
