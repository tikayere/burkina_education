# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Shared test fixtures for the Phase 3 finance test suites (discounts,
mobile money, permissions) - see academic/tests/fixtures.py for the
equivalent Phase 2 pattern this mirrors.
"""

import frappe
from frappe.utils import add_days, nowdate


class FinanceFixture:
	"""One Company (XOF, Standard chart of accounts), one Grade/Program, one
	Academic Year, one Fee Category/Structure/Schedule, and three sibling
	Students (sharing one Guardian) so sibling-rank discount logic has
	something real to rank. Everything is tagged with a random suffix so
	tests can run in parallel/repeatedly without name clashes.
	"""

	def __init__(self):
		frappe.db.set_single_value("Education Settings", "user_creation_skip", 1)
		self.tag = frappe.generate_hash(length=6).upper()

		if not frappe.db.get_value("Currency", "XOF", "enabled"):
			frappe.db.set_value("Currency", "XOF", "enabled", 1)

		self.company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": f"Test Co {self.tag}",
				# Explicit, not auto-derived: Company.validate_abbr() otherwise
				# only takes the *first character* of each space-separated word
				# (so "Test Co <tag>" collapses to "TC" + one character of the
				# tag), which collides far too easily across tests.
				"abbr": self.tag,
				"default_currency": "XOF",
				"country": "Burkina Faso",
				"create_chart_of_accounts_based_on": "Standard Template",
				"chart_of_accounts": "Standard",
			}
		).insert(ignore_permissions=True)

		self.school = frappe.get_doc(
			{"doctype": "School", "school_name": f"Test School {self.tag}", "school_code": self.tag}
		).insert(ignore_permissions=True)

		self.education_level = frappe.get_doc(
			{
				"doctype": "Education Level",
				"education_level_name": f"Niveau {self.tag}",
				"school": self.school.name,
			}
		).insert(ignore_permissions=True)

		self.cycle = frappe.get_doc(
			{
				"doctype": "Cycle",
				"cycle_name": f"Cycle {self.tag}",
				"education_level": self.education_level.name,
				"school": self.school.name,
			}
		).insert(ignore_permissions=True)

		self.grade = frappe.get_doc(
			{"doctype": "Grade", "grade_name": f"Classe {self.tag}", "cycle": self.cycle.name}
		).insert(ignore_permissions=True)

		self.academic_year = frappe.get_doc(
			{
				"doctype": "Academic Year",
				"academic_year_name": f"AY {self.tag}",
				"year_start_date": "2025-09-01",
				"year_end_date": "2026-06-30",
			}
		).insert(ignore_permissions=True)

		self.guardian = frappe.get_doc(
			{
				"doctype": "Guardian",
				"guardian_name": f"Tuteur {self.tag}",
				"email_address": f"tuteur.{self.tag}@test-fixture.bf".lower(),
			}
		).insert(ignore_permissions=True)

		# Three siblings, oldest first (creation order = sibling rank).
		self.students = [self._create_student(i) for i in (1, 2, 3)]

		self.fee_category = frappe.get_doc(
			{"doctype": "Fee Category", "category_name": f"Scolarite {self.tag}"}
		).insert(ignore_permissions=True)

		self.fee_structure = frappe.get_doc(
			{
				"doctype": "Fee Structure",
				"program": self.grade.program,
				"academic_year": self.academic_year.name,
				"company": self.company.name,
				"components": [{"fees_category": self.fee_category.name, "amount": 100000}],
			}
		).insert(ignore_permissions=True)
		self.fee_structure.submit()

		self.student_group = frappe.get_doc(
			{
				"doctype": "Student Group",
				"student_group_name": f"Groupe {self.tag}",
				"academic_year": self.academic_year.name,
				"group_based_on": "Batch",
				"program": self.grade.program,
				"max_strength": 0,
				"students": [
					{"student": s.name, "student_name": s.student_name, "active": 1} for s in self.students
				],
			}
		).insert(ignore_permissions=True)

		self.fee_schedule = frappe.get_doc(
			{
				"doctype": "Fee Schedule",
				"fee_structure": self.fee_structure.name,
				"academic_year": self.academic_year.name,
				"company": self.company.name,
				"due_date": add_days(nowdate(), 30),
				"components": [{"fees_category": self.fee_category.name, "amount": 100000, "total": 100000}],
				"student_groups": [{"student_group": self.student_group.name}],
			}
		).insert(ignore_permissions=True)

	def _create_student(self, index):
		self._ensure_gender("Female")
		student = frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": f"Eleve{index}",
				"last_name": self.tag,
				"gender": "Female",
				"student_email_id": f"eleve{index}.{self.tag}@test-fixture.bf".lower(),
				"grade": self.grade.name,
				"guardians": [{"guardian": self.guardian.name}],
			}
		).insert(ignore_permissions=True)
		return student

	@staticmethod
	def _ensure_gender(gender):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)
		return gender

	def create_invoice(self, student, amount=100000, submit=True):
		"""A school-fee Sales Invoice exactly like ``Fee Schedule.create_fees()``
		would generate (student/fee_schedule set, one Fee Category item row) -
		built directly here to keep fixture setup fast, since the discount hook
		only cares about those two fields being present.
		"""
		customer = frappe.db.get_value("Student", student.name, "customer")
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": customer,
				"student": student.name,
				"fee_schedule": self.fee_schedule.name,
				"company": self.company.name,
				"currency": "XOF",
				"due_date": add_days(nowdate(), 15),
				"set_posting_time": 1,
				"posting_date": nowdate(),
				"items": [{"item_code": self.fee_category.item, "qty": 1, "rate": amount}],
			}
		)
		si.insert(ignore_permissions=True)
		if submit:
			si.submit()
		return si
