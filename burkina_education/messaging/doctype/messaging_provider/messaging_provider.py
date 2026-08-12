# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MessagingProvider(Document):
	def validate(self):
		if self.is_default:
			other_default = frappe.db.exists(
				"Messaging Provider",
				{"channel": self.channel, "is_default": 1, "name": ["!=", self.name]},
			)
			if other_default:
				frappe.throw(
					_("{0} est déjà le fournisseur par défaut pour le canal {1}.").format(
						other_default, self.channel
					)
				)
