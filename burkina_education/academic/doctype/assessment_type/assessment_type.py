# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AssessmentType(Document):
	"""A category of graded work (Devoir, Composition, Examen, ...) carrying a
	default coefficient. Assessment Plan (Education) links to this via a
	Custom Field so the Phase 2 grading engine knows how to weight it -
	Education itself has no notion of assessment coefficients.
	"""

	pass
