# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AttendanceAlert(Document):
	"""A logged low-attendance detection for one student over one period
	(master.md §24). Actually notifying the guardian/administration by
	SMS/WhatsApp/portal is Phase 4 (Communication) - this is the detection
	and audit log layer only, see docs/architecture.md section G.
	"""

	pass
