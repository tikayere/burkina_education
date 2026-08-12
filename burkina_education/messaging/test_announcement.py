# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.messaging.doctype.announcement.announcement import resolve_audience
from burkina_education.messaging.tests.fixtures import CommunicationFixture


class TestAnnouncement(FrappeTestCase):
	def setUp(self):
		self.fx = CommunicationFixture()

	def _make(self, audience_type, audience_reference=None):
		return frappe.get_doc(
			{
				"doctype": "Announcement",
				"title": f"Annonce {self.fx.tag}",
				"content": "Contenu de test",
				"audience_type": audience_type,
				"audience_reference_doctype": {
					"Grade": "Grade", "Education Level": "Education Level", "Student Group": "Student Group",
				}.get(audience_type),
				"audience_reference": audience_reference,
				"start_date": frappe.utils.nowdate(),
			}
		).insert(ignore_permissions=True)

	def test_publish_sets_status_and_metadata(self):
		doc = self._make("All Guardians")
		doc.publish()
		doc.reload()
		self.assertEqual(doc.publication_status, "Published")
		self.assertTrue(doc.published_on)
		self.assertEqual(doc.published_by, frappe.session.user)

	def test_publish_twice_is_rejected(self):
		doc = self._make("All Guardians")
		doc.publish()
		doc.reload()
		self.assertRaises(frappe.ValidationError, doc.publish)

	def test_resolve_audience_all_guardians(self):
		doc = self._make("All Guardians")
		guardians, students, users = resolve_audience(doc)
		self.assertIn(self.fx.guardian.name, guardians)
		# "All Guardians" means guardians only - it must not also notify the
		# students directly (regression: resolve_audience used to reuse the
		# same `students` list it queried internally just to compute
		# guardians as the returned audience too).
		self.assertEqual(students, [])

	def test_resolve_audience_grade_scoped(self):
		doc = self._make("Grade", self.fx.grade.name)
		guardians, students, users = resolve_audience(doc)
		self.assertIn(self.fx.students[0].name, students)
		self.assertIn(self.fx.guardian.name, guardians)

	def test_resolve_audience_other_grade_excluded(self):
		other_grade = frappe.get_doc(
			{"doctype": "Grade", "grade_name": f"Autre {self.fx.tag}", "cycle": self.fx.cycle.name}
		).insert(ignore_permissions=True)
		doc = self._make("Grade", other_grade.name)
		guardians, students, users = resolve_audience(doc)
		self.assertNotIn(self.fx.students[0].name, students)

	def test_end_date_before_start_date_is_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "Announcement",
				"title": f"Annonce {self.fx.tag} invalide",
				"content": "x",
				"audience_type": "All",
				"start_date": "2026-10-10",
				"end_date": "2026-10-01",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
