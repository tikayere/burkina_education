# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class School(Document):
	def before_insert(self):
		# autoname (field:school_code) runs before validate(), so the code
		# must already be normalized by the time set_new_name() reads it.
		self.normalize_code()

	def validate(self):
		self.normalize_code()

	def normalize_code(self):
		self.school_code = (self.school_code or "").strip().upper()
