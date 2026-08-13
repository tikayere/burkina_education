# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class StudentBoardingAssignment(Document):
	"""master.md §42: check-in/out. Boarding fees are billed through the
	existing Finance fee engine (an "Internat" Fee Category), not reinvented
	here - see docs/architecture.md section K, same reuse decision as
	Transport/Canteen.
	"""

	def validate(self):
		if self.is_new():
			self._validate_bed_available()

		if self.check_out_date and self.status != "Terminé":
			self.status = "Terminé"

		self.set_supervisor()

	def on_update(self):
		self._sync_bed_status()

	def set_supervisor(self):
		"""``fetch_from`` only resolves one Link hop - Boarding Bed -> Boarding
		Room -> Boarding Building -> supervisor is three, so it's walked here
		instead."""
		if not self.bed:
			self.supervisor = None
			return
		room = frappe.db.get_value("Boarding Bed", self.bed, "room")
		building = room and frappe.db.get_value("Boarding Room", room, "building")
		self.supervisor = building and frappe.db.get_value("Boarding Building", building, "supervisor")

	def _validate_bed_available(self):
		bed_status = frappe.db.get_value("Boarding Bed", self.bed, "status")
		if bed_status == "Occupé":
			frappe.throw(frappe._("Ce lit est déjà occupé."))
		if bed_status == "Hors service":
			frappe.throw(frappe._("Ce lit est hors service."))

	def _sync_bed_status(self):
		new_status = "Disponible" if self.status == "Terminé" else "Occupé"
		if frappe.db.get_value("Boarding Bed", self.bed, "status") != new_status:
			frappe.db.set_value("Boarding Bed", self.bed, "status", new_status)

	@frappe.whitelist()
	def check_out(self):
		frappe.has_permission(self.doctype, "write", self, throw=True)
		self.check_out_date = nowdate()
		self.status = "Terminé"
		self.save()
