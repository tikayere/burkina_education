# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""master.md §13: Application -> Review -> Acceptance -> Admission ->
Enrollment, driven entirely through admissions/overrides.py's whitelisted
transition methods on Student Applicant (docs/architecture.md section O)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from burkina_education.admissions.tests.fixtures import AdmissionsFixture


class TestAdmissionsPipeline(FrappeTestCase):
	def setUp(self):
		self.fixture = AdmissionsFixture()

	def test_defaults_to_draft_and_syncs_program_from_requested_grade(self):
		applicant = self.fixture.create_applicant()
		self.assertEqual(applicant.application_status, "Brouillon")
		self.assertEqual(applicant.program, self.fixture.grade.program)

	def test_seeds_a_default_document_checklist_once(self):
		applicant = self.fixture.create_applicant()
		self.assertTrue(len(applicant.documents) > 0)
		seeded_count = len(applicant.documents)

		# Re-saving must not seed a second copy of the checklist.
		applicant.save()
		self.assertEqual(len(applicant.documents), seeded_count)

	def test_submit_application_requires_draft_status(self):
		applicant = self.fixture.create_applicant()
		applicant.submit_application()
		self.assertEqual(applicant.application_status, "Soumise")

		with self.assertRaises(frappe.ValidationError):
			applicant.submit_application()

	def test_full_pipeline_to_enrollment(self):
		applicant = self.fixture.create_applicant()
		applicant.submit_application()
		applicant.start_review()
		self.assertEqual(applicant.application_status, "En cours d'examen")

		applicant.record_decision("Acceptée", notes="Dossier complet.")
		self.assertEqual(applicant.application_status, "Acceptée")
		self.assertEqual(applicant.decision_by, frappe.session.user)
		self.assertIsNotNone(applicant.decision_date)

		# Fee required by default (Custom Field default) and not yet paid.
		self.assertTrue(applicant.admission_fee_required)
		with self.assertRaises(frappe.ValidationError):
			applicant.enroll()

		applicant.admission_fee_amount = 15000
		applicant.save()
		applicant.collect_admission_fee(mode_of_payment=None)
		self.assertTrue(applicant.admission_fee_paid)

		result = applicant.enroll()
		self.assertEqual(applicant.application_status, "Inscrite")
		self.assertEqual(applicant.enrolled_student, result["student"])
		self.assertEqual(applicant.enrolled_program_enrollment, result["program_enrollment"])

		# Education's own Student.validate() (update_applicant_status) forces
		# application_status back to its own "Admitted" the instant the
		# Student is inserted - this pipeline's own "Inscrite" must win, not
		# silently get clobbered back to Education's upstream value.
		self.assertEqual(
			frappe.db.get_value("Student Applicant", applicant.name, "application_status"), "Inscrite"
		)

		student = frappe.get_doc("Student", result["student"])
		self.assertEqual(student.student_applicant, applicant.name)
		self.assertEqual(student.grade, self.fixture.grade.name)
		self.assertEqual(len(student.guardians), 1)
		self.assertEqual(student.guardians[0].guardian, self.fixture.guardian.name)

		program_enrollment = frappe.get_doc("Program Enrollment", result["program_enrollment"])
		self.assertEqual(program_enrollment.student, result["student"])
		self.assertEqual(program_enrollment.program, self.fixture.grade.program)
		# Class/Section assignment is left to the Registrar afterwards
		# (master.md §14) - enroll() must not auto-submit this draft.
		self.assertEqual(program_enrollment.docstatus, 0)

	def test_enroll_without_fee_requirement_does_not_need_payment(self):
		applicant = self.fixture.create_applicant(admission_fee_required=0)
		applicant.submit_application()
		applicant.start_review()
		applicant.record_decision("Acceptée")
		result = applicant.enroll()
		self.assertEqual(applicant.application_status, "Inscrite")
		self.assertTrue(frappe.db.exists("Student", result["student"]))

	def test_waitlisted_can_be_redecided(self):
		applicant = self.fixture.create_applicant()
		applicant.submit_application()
		applicant.start_review()
		applicant.record_decision("Liste d'attente")
		self.assertEqual(applicant.application_status, "Liste d'attente")

		applicant.record_decision("Acceptée", notes="Une place s'est libérée.")
		self.assertEqual(applicant.application_status, "Acceptée")

	def test_record_decision_rejects_invalid_value(self):
		applicant = self.fixture.create_applicant()
		applicant.submit_application()
		applicant.start_review()
		with self.assertRaises(frappe.ValidationError):
			applicant.record_decision("Peut-être")

	def test_withdraw_from_mid_pipeline(self):
		applicant = self.fixture.create_applicant()
		applicant.submit_application()
		applicant.withdraw(reason="La famille a déménagé.")
		self.assertEqual(applicant.application_status, "Retirée")
		self.assertEqual(applicant.withdrawal_reason, "La famille a déménagé.")

	def test_cannot_withdraw_an_enrolled_application(self):
		applicant = self.fixture.create_applicant(admission_fee_required=0)
		applicant.submit_application()
		applicant.start_review()
		applicant.record_decision("Acceptée")
		applicant.enroll()
		with self.assertRaises(frappe.ValidationError):
			applicant.withdraw(reason="Trop tard")

	def test_entrance_exam_result_computed_from_settings_scale(self):
		settings = frappe.get_single("Burkina Education Settings")
		max_grade = settings.max_grade or 20
		passing_grade = settings.passing_grade or (max_grade / 2)

		applicant = self.fixture.create_applicant(
			entrance_exam_required=1, entrance_exam_max_score=100, entrance_exam_score=0
		)
		self.assertFalse(applicant.entrance_exam_passed)

		# A score that normalizes to exactly the passing mark on the
		# school's own grading scale should pass.
		applicant.entrance_exam_score = (passing_grade / max_grade) * 100
		applicant.save()
		self.assertTrue(applicant.entrance_exam_passed)
