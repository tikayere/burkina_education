# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MobileMoneyTransaction(Document):
	"""Audit/dedup log for one mobile money payment attempt. State changes are
	driven server-side only, from ``finance.mobile_money.api`` - see
	docs/architecture.md section H (never trust a client redirect).
	"""

	pass
