# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CanteenSubscription(Document):
	"""master.md §41: student subscriptions. Billing runs through the
	existing Finance fee engine (a "Cantine" Fee Category), not reinvented
	here - see docs/architecture.md section K, same reuse decision as
	Student Transport Assignment.
	"""

	def validate(self):
		if self.end_date and self.start_date and self.end_date < self.start_date:
			frappe.throw(frappe._("La date de fin ne peut pas précéder la date de début."))
