# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Clinic Staff Portal API tests (portal/roles/clinic_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import clinic_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestClinicApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("Clinic Staff")
		self.visit = frappe.get_doc(
			{
				"doctype": "Clinic Visit",
				"student": self.fx.students[0].name,
				"date": frappe.utils.now_datetime(),
				"status": "Ouvert",
				"complaint": "Mal de tête",
			}
		).insert(ignore_permissions=True)

	def _as_staff(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_requires_clinic_role(self):
		other = self.fx.staff_user("Librarian", "not-clinic")
		frappe.set_user(other.name)
		try:
			self.assertRaises(frappe.PermissionError, clinic_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_counts_open_visits(self):
		# >= / assertIn rather than == - the dev site's demo data also
		# contributes Clinic Visits (see test_librarian_api.py).
		data = self._as_staff(clinic_api.get_dashboard)
		self.assertGreaterEqual(data["visits_today"], 1)
		self.assertGreaterEqual(data["open_cases"], 1)
		self.assertGreaterEqual(data["not_notified"], 1)
		self.assertIn(self.visit.name, {r["name"] for r in data["recent"]})
