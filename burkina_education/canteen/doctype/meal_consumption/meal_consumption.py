# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class MealConsumption(Document):
	"""One meal check-in for one Canteen Subscription (master.md §41 "meal
	consumption"). Validated against the subscription's own status/period so
	consumption can't be logged for a lapsed or not-yet-started subscription.
	"""

	def validate(self):
		sub = frappe.db.get_value(
			"Canteen Subscription", self.subscription, ["status", "start_date", "end_date"], as_dict=True
		)
		if not sub:
			return
		if sub.status != "Active":
			frappe.throw(frappe._("Cet abonnement n'est pas actif ({0}).").format(sub.status))

		date = getdate(self.date)
		if date < getdate(sub.start_date) or (sub.end_date and date > getdate(sub.end_date)):
			frappe.throw(frappe._("Cette date est en dehors de la période de l'abonnement."))
