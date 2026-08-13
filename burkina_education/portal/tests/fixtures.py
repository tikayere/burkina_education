# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Shared test fixtures for the Vue portal test suites (portal/tests/) -
builds on CommunicationFixture (Phase 4, itself built on AcademicFixture,
Phase 2) the same layered way finance/tests/fixtures.py does, adding just
what the Teacher Portal needs on top: a Company (Employee.company is
mandatory), an Employee/Instructor pair wired into the fixture's own
Student Group, and a helper to promote that Employee to a real portal
login (Instructor has no ``user`` field of its own - see
portal/permissions.py::get_instructor_for_user).
"""

import frappe

from burkina_education.academic.tests.fixtures import get_or_create_user
from burkina_education.messaging.tests.fixtures import CommunicationFixture


class PortalFixture(CommunicationFixture):
	def __init__(self):
		super().__init__()

		if not frappe.db.get_value("Currency", "XOF", "enabled"):
			frappe.db.set_value("Currency", "XOF", "enabled", 1)

		self.company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"Test Co {self.tag}",
				"abbr": self.tag,
				"default_currency": "XOF",
				"country": "Burkina Faso",
			}
		).insert(ignore_permissions=True)

		self.employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": f"Prof {self.tag}",
				"company": self.company.name,
				"gender": "Male",
				"date_of_birth": "1985-01-01",
				"date_of_joining": frappe.utils.nowdate(),
			}
		).insert(ignore_permissions=True)

		self.instructor = frappe.get_doc(
			{
				"doctype": "Instructor",
				"instructor_name": f"Prof {self.tag}",
				"employee": self.employee.name,
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		self.student_group.append("instructors", {"instructor": self.instructor.name})
		self.student_group.save(ignore_permissions=True)

	def link_instructor_to_user(self, extra_roles=None):
		"""Employee.user_id (not Instructor - see the module docstring) is
		what portal/permissions.py::get_instructor_for_user actually walks."""
		roles = ["Instructor"] + (extra_roles or [])
		user = get_or_create_user(f"teacher.user.{self.tag}@test-fixture.bf", roles)
		self.employee.db_set("user_id", user.name)
		return user

	def other_student_group(self):
		"""A second Student Group (same term) this fixture's Instructor is
		*not* attached to - for ownership-boundary tests."""
		group = frappe.get_doc(
			{
				"doctype": "Student Group",
				"student_group_name": f"Autre Groupe {self.tag}",
				"academic_year": self.academic_year.name,
				"academic_term": self.term_1.name,
				"group_based_on": "Batch",
				"program": self.grade.program,
				"max_strength": 0,
			}
		).insert(ignore_permissions=True)
		return group
