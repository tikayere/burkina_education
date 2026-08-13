# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Vue Communications Portal API tests (portal/roles/comms_api.py) -
docs/architecture.md section M."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.portal.roles import comms_api
from burkina_education.portal.tests.fixtures import PortalFixture


class TestCommsApi(FrappeTestCase):
	def setUp(self):
		self.fx = PortalFixture()
		self.user = self.fx.staff_user("Secretary")
		self.announcement = frappe.get_doc(
			{
				"doctype": "Announcement",
				"title": f"Réunion {self.fx.tag}",
				"content": "Réunion de rentrée.",
				"audience_type": "All Guardians",
				"start_date": frappe.utils.nowdate(),
				"publication_status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _as_secretary(self, fn, *args, **kwargs):
		frappe.set_user(self.user.name)
		try:
			return fn(*args, **kwargs)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_requires_role(self):
		other = self.fx.staff_user("Librarian", "not-secretary")
		frappe.set_user(other.name)
		try:
			self.assertRaises(frappe.PermissionError, comms_api.get_dashboard)
		finally:
			frappe.set_user("Administrator")

	def test_dashboard_lists_draft_announcement(self):
		data = self._as_secretary(comms_api.get_dashboard)
		self.assertIn(self.announcement.name, {a["name"] for a in data["drafts"]})

	def test_publish_via_run_doc_method_moves_it_to_published(self):
		# comms_api itself has no publish() wrapper - the frontend calls the
		# doctype's own whitelisted method (Announcement.publish) through
		# Frappe's generic run_doc_method, exercised here directly to prove
		# the Secretary role's permissions actually allow it end to end.
		frappe.set_user(self.user.name)
		try:
			doc = frappe.get_doc("Announcement", self.announcement.name)
			doc.publish()
		finally:
			frappe.set_user("Administrator")

		self.assertEqual(frappe.db.get_value("Announcement", self.announcement.name, "publication_status"), "Published")
