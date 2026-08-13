# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StudentTransportAssignment(Document):
	"""master.md §40: pickup/drop-off assignments. Transport fees are billed
	through the existing Finance fee engine (a "Transport" Fee Category), not
	reinvented here - see docs/architecture.md section K.
	"""

	def validate(self):
		self._validate_stop_belongs_to_route()
		self._validate_single_active_assignment()

	def _validate_stop_belongs_to_route(self):
		if not self.stop_name:
			return
		stop_names = frappe.get_all(
			"Transport Route Stop", filters={"parent": self.route}, pluck="stop_name"
		)
		if self.stop_name not in stop_names:
			frappe.throw(
				frappe._("« {0} » n'est pas un arrêt défini sur l'itinéraire {1}.").format(
					self.stop_name, self.route
				)
			)

	def _validate_single_active_assignment(self):
		if self.status != "Actif":
			return
		duplicate = frappe.db.exists(
			"Student Transport Assignment",
			{"student": self.student, "status": "Actif", "name": ["!=", self.name]},
		)
		if duplicate:
			frappe.throw(
				frappe._("{0} a déjà une affectation de transport active ({1}).").format(
					self.student_name or self.student, duplicate
				)
			)
