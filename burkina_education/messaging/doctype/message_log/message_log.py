# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MessageLog(Document):
	"""One outbound (or logged in-app) notification attempt - the audit trail
	master.md §33 asks for ("SMS Log") generalised to every channel, so
	Absence/Payment/Fee/Result/Announcement notifications all land in one
	place instead of four near-identical doctypes (docs/architecture.md
	section J). Always created server-side by messaging/notify.py -
	never edited by hand, see message_log.js.
	"""

	pass
