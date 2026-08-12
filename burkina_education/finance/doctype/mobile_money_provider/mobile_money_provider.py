# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MobileMoneyProvider(Document):
	"""Per-provider configuration (master.md §28: "do NOT tightly couple the
	application to a single provider"). ``provider_code`` selects the adapter
	in ``finance.mobile_money.gateway``; credentials are stored as encrypted
	``Password`` fields, never in source code.
	"""

	pass
