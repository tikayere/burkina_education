# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BoardingBed(Document):
	def validate(self):
		if self.is_new():
			self._validate_room_capacity()

	def _validate_room_capacity(self):
		capacity = frappe.db.get_value("Boarding Room", self.room, "capacity") or 0
		existing = frappe.db.count("Boarding Bed", {"room": self.room})
		if existing >= capacity:
			frappe.throw(
				frappe._("La chambre {0} a atteint sa capacité maximale ({1} lits).").format(
					self.room, capacity
				)
			)
