# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Admissions (master.md §13): Application -> Review -> Acceptance ->
Admission -> Enrollment. Education already ships ``Student Applicant``
(applicant identity, guardians, siblings, a naming series, and its own
``application_status``) and ``Student Admission`` (per-program eligibility
window/age limits) - docs/architecture.md section B's own extension-strategy
table calls for reusing both rather than a parallel doctype, since the
funnel states *can* be modeled as ``Student Applicant`` states plus a
Property Setter (setup/install.py::create_property_setters retargets
``application_status``'s options from Education's own Applied/Approved/
Rejected/Admitted to this pipeline's 8-state set) and Custom Fields
(setup/install.py::get_custom_fields - requested Grade, previous school,
documents checklist, interview, entrance exam, decision, admission fee,
the Student/Program Enrollment this application produced).

The pipeline's actual transitions (and the two steps with real side effects
- collecting the fee, enrolling) are whitelisted **Document methods**, not a
free-text edit of ``application_status`` - the same "doc-level action gets
its own guarded method" pattern as ``Announcement.publish()``/``Student
Boarding Assignment.check_out()`` elsewhere in this app, and the mechanism
Section M's own Vue framework is built to call generically
(``frappe.handler.run_doc_method`` / ``frm.call()``). Since ``Student
Applicant`` is a vendor (Education) DocType, those methods can only be added
by subclassing it via ``override_doctype_class`` (hooks.py) - the same
mechanism ``finance/overrides.py`` uses, extended here beyond that file's
narrower "fix a genuine incompatibility" scope to "add the behavior this
vendor DocType doesn't have at all", since Frappe offers no other way to
attach a whitelisted method to a DocType this app doesn't own.
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from education.education.doctype.student_applicant.student_applicant import (
	StudentApplicant as EducationStudentApplicant,
)

STATUS_DRAFT = "Brouillon"
STATUS_SUBMITTED = "Soumise"
STATUS_UNDER_REVIEW = "En cours d'examen"
STATUS_ACCEPTED = "Acceptée"
STATUS_REJECTED = "Rejetée"
STATUS_WAITLISTED = "Liste d'attente"
STATUS_ENROLLED = "Inscrite"
STATUS_WITHDRAWN = "Retirée"

#: Full pipeline, in this exact order - mirrors the Property Setter options
#: string (setup/install.py) and master.md §13's own state list.
APPLICATION_STATUSES = (
	STATUS_DRAFT,
	STATUS_SUBMITTED,
	STATUS_UNDER_REVIEW,
	STATUS_ACCEPTED,
	STATUS_REJECTED,
	STATUS_WAITLISTED,
	STATUS_ENROLLED,
	STATUS_WITHDRAWN,
)

DECISION_STATUSES = (STATUS_ACCEPTED, STATUS_REJECTED, STATUS_WAITLISTED)

#: A starter checklist seeded once per new application (master.md §13
#: "documents") so the Registrar has something concrete to work through
#: rather than a blank table; rows can be edited/added/removed freely
#: afterwards - this is a convenience default, not an enforced list.
DEFAULT_REQUIRED_DOCUMENTS = (
	"Extrait de naissance ou jugement supplétif",
	"Certificat médical",
	"Bulletins scolaires (2 dernières années)",
	"Photo d'identité",
	"Photocopie CNIB des parents/tuteurs",
)


class StudentApplicant(EducationStudentApplicant):
	def validate(self):
		super().validate()
		if not self.application_status:
			self.application_status = STATUS_DRAFT
		self.sync_program_from_grade()
		self.seed_required_documents()
		self.compute_entrance_exam_result()

	def sync_program_from_grade(self):
		"""``requested_grade`` (Custom Field) is what the Registrar actually
		picks; ``program`` is Education's own required field underneath it
		(Grade owns a Program 1:1, docs/architecture.md section B) - kept in
		sync explicitly rather than via ``fetch_from`` (documented elsewhere
		in this app as unreliable for anything beyond the simplest case, see
		docs/architecture.md section K's own ``fetch_from`` gotcha)."""
		if not self.requested_grade:
			return
		program = frappe.db.get_value("Grade", self.requested_grade, "program")
		if program and self.program != program:
			self.program = program

	def seed_required_documents(self):
		if not self.is_new() or self.documents:
			return
		for document_type in DEFAULT_REQUIRED_DOCUMENTS:
			self.append("documents", {"document_type": document_type})

	def compute_entrance_exam_result(self):
		"""Normalizes the entrance exam score onto the school's own grading
		scale (``Burkina Education Settings.max_grade``/``passing_grade``,
		Phase 2) rather than inventing a separate pass mark - read-only,
		recomputed on every save."""
		if not self.entrance_exam_score:
			self.entrance_exam_passed = 0
			return
		max_score = flt(self.entrance_exam_max_score) or 20
		settings = frappe.get_cached_doc("Burkina Education Settings")
		scale = flt(settings.max_grade) or 20
		passing = flt(settings.passing_grade) or (scale / 2)
		normalized = flt(self.entrance_exam_score) / max_score * scale
		self.entrance_exam_passed = 1 if normalized >= passing else 0

	# --- Pipeline transitions (master.md §13) --------------------------------

	@frappe.whitelist()
	def submit_application(self):
		"""Draft -> Submitted."""
		self._check_write()
		self._require_status(STATUS_DRAFT)
		self._require_fields()
		self.application_status = STATUS_SUBMITTED
		if not self.application_date:
			self.application_date = nowdate()
		self.save()
		return self.application_status

	@frappe.whitelist()
	def start_review(self):
		"""Submitted -> Under Review."""
		self._check_write()
		self._require_status(STATUS_SUBMITTED)
		self.application_status = STATUS_UNDER_REVIEW
		self.save()
		return self.application_status

	@frappe.whitelist()
	def record_decision(self, decision, notes=None):
		"""Under Review (or a re-decided Waitlisted) -> Accepted/Rejected/Waitlisted."""
		self._check_write()
		if decision not in DECISION_STATUSES:
			frappe.throw(_("Décision invalide : {0}").format(decision))
		self._require_status(STATUS_UNDER_REVIEW, STATUS_WAITLISTED)
		self.application_status = decision
		if notes:
			self.decision_notes = notes
		self.decision_by = frappe.session.user
		self.decision_date = nowdate()
		self.save()
		return self.application_status

	@frappe.whitelist()
	def collect_admission_fee(self, mode_of_payment=None):
		"""Records the admission fee as paid. Kept as a simple flag/date/mode
		rather than a real Sales Invoice: the applicant isn't a Student (and
		has no Customer/receivable party, docs/architecture.md section H) at
		this point in the pipeline, so Phase 3's fee engine doesn't apply yet
		- see docs/architecture.md section O for this scoping call."""
		self._check_write()
		if not self.admission_fee_required:
			frappe.throw(_("Aucun frais d'inscription n'est requis pour cette candidature."))
		if not self.admission_fee_amount:
			frappe.throw(_("Indiquez le montant des frais avant de les encaisser."))
		self.admission_fee_paid = 1
		self.admission_fee_payment_date = nowdate()
		if mode_of_payment:
			self.admission_fee_mode_of_payment = mode_of_payment
		self.save()
		return self.application_status

	@frappe.whitelist()
	def enroll(self, academic_term=None):
		"""Accepted -> Enrolled: creates the real Student and a draft Program
		Enrollment (docs/architecture.md section C reuses both unchanged).
		Class/Section assignment and the Program Enrollment's own submit are
		left to the Registrar afterwards (master.md §14's own "Validation ->
		Class Assignment" step), not done automatically here."""
		self._check_write()
		self._require_status(STATUS_ACCEPTED)
		if self.admission_fee_required and not self.admission_fee_paid:
			frappe.throw(_("Les frais d'inscription doivent être encaissés avant l'enrôlement."))
		if not self.program:
			frappe.throw(_("Sélectionnez d'abord la classe demandée."))
		if self.enrolled_student:
			frappe.throw(_("Cette candidature a déjà produit l'élève {0}.").format(self.enrolled_student))

		student = self._create_student()
		program_enrollment = self._create_program_enrollment(student.name, academic_term)

		# Education's own Student.validate() (update_applicant_status) just
		# forced application_status back to its own "Admitted" via a direct
		# frappe.db.set_value the instant _create_student() inserted above -
		# which also bumps this row's own `modified` timestamp in the
		# database without touching this in-memory copy, so the plain
		# self.save() below would otherwise fail with a TimestampMismatchError
		# ("has been modified after you have opened it"). reload() first so
		# this pipeline's own terminal state can win cleanly.
		self.reload()
		self.enrolled_student = student.name
		self.enrolled_program_enrollment = program_enrollment.name
		self.application_status = STATUS_ENROLLED
		self.save()
		return {"student": student.name, "program_enrollment": program_enrollment.name}

	@frappe.whitelist()
	def withdraw(self, reason=None):
		"""Any pre-enrollment state -> Withdrawn (a family pulling out of the
		process). Withdrawing an already-Enrolled application is not this
		method's job - that's the real Student's own lifecycle
		(``Student.status``), not the application's."""
		self._check_write()
		if self.application_status in (STATUS_ENROLLED, STATUS_WITHDRAWN):
			frappe.throw(
				_("Impossible de retirer une candidature déjà {0}.").format(self.application_status.lower())
			)
		self.application_status = STATUS_WITHDRAWN
		if reason:
			self.withdrawal_reason = reason
		self.save()
		return self.application_status

	# --- helpers --------------------------------------------------------------

	def _check_write(self):
		frappe.has_permission(self.doctype, "write", self, throw=True)

	def _require_status(self, *allowed):
		if self.application_status not in allowed:
			frappe.throw(
				_("Cette action n'est pas possible depuis le statut « {0} ».").format(self.application_status)
			)

	def _require_fields(self):
		required = (
			("first_name", _("Prénom")),
			("program", _("Classe demandée")),
			("academic_year", _("Année académique")),
		)
		missing = [label for fieldname, label in required if not self.get(fieldname)]
		if missing:
			frappe.throw(_("Champs obligatoires manquants avant soumission : {0}").format(", ".join(missing)))

	def _create_student(self):
		student = frappe.get_doc(
			{
				"doctype": "Student",
				"first_name": self.first_name,
				"middle_name": self.middle_name,
				"last_name": self.last_name,
				"student_name": self.title
				or " ".join(filter(None, [self.first_name, self.middle_name, self.last_name])),
				"student_email_id": self.student_email_id,
				"student_mobile_number": self.student_mobile_number,
				"date_of_birth": self.date_of_birth,
				"gender": self.gender,
				"nationality": self.nationality,
				"student_applicant": self.name,
				"grade": self.requested_grade,
				"school": frappe.db.get_value("Grade", self.requested_grade, "school"),
				"status": "Active",
				"enabled": 1,
				"joining_date": nowdate(),
			}
		)
		for row in self.guardians:
			student.append("guardians", {"guardian": row.guardian, "relation": row.relation})
		student.insert(ignore_permissions=True)
		return student

	def _create_program_enrollment(self, student_name, academic_term=None):
		return frappe.get_doc(
			{
				"doctype": "Program Enrollment",
				"student": student_name,
				"program": self.program,
				"academic_year": self.academic_year,
				"academic_term": academic_term or self.academic_term,
				"student_category": self.student_category,
				"enrollment_date": nowdate(),
			}
		).insert(ignore_permissions=True)
