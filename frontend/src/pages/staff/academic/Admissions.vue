<template>
	<ResourceListPage
		ref="listPage"
		doctype="Student Applicant"
		title="Candidatures"
		icon="user-plus"
		empty-title="Aucune candidature"
		new-button-label="Nouvelle candidature"
		search-field="title"
		order-by="creation desc"
		:list-fields="LIST_FIELDS"
		:columns="columns"
		:form-fields="formFields"
		:can-delete="isAcademicDirector"
	>
		<template #rowActions="{ row }">
			<div class="flex items-center justify-end gap-2">
				<Button
					v-if="row.application_status === 'Brouillon'"
					size="sm"
					variant="outline"
					:loading="acting === row.name"
					@click.stop="act(row, 'submit_application')"
				>
					Soumettre
				</Button>
				<Button
					v-if="row.application_status === 'Soumise'"
					size="sm"
					variant="outline"
					:loading="acting === row.name"
					@click.stop="act(row, 'start_review')"
				>
					Examiner
				</Button>
				<template v-if="['En cours d\'examen', 'Liste d\'attente'].includes(row.application_status)">
					<Button size="sm" variant="outline" :loading="acting === row.name" @click.stop="decide(row, 'Acceptée')">
						Accepter
					</Button>
					<Button size="sm" variant="outline" theme="gray" :loading="acting === row.name" @click.stop="decide(row, 'Liste d\'attente')">
						Attente
					</Button>
					<Button size="sm" variant="outline" theme="red" :loading="acting === row.name" @click.stop="decide(row, 'Rejetée')">
						Rejeter
					</Button>
				</template>
				<Button
					v-if="row.application_status === 'Acceptée' && row.admission_fee_required && !row.admission_fee_paid"
					size="sm"
					variant="outline"
					:loading="acting === row.name"
					@click.stop="act(row, 'collect_admission_fee')"
				>
					Encaisser les frais
				</Button>
				<Button
					v-if="row.application_status === 'Acceptée' && (!row.admission_fee_required || row.admission_fee_paid)"
					size="sm"
					variant="solid"
					theme="green"
					:loading="acting === row.name"
					@click.stop="enroll(row)"
				>
					Enrôler
				</Button>
				<Button
					v-if="!['Inscrite', 'Retirée'].includes(row.application_status)"
					size="sm"
					variant="ghost"
					theme="gray"
					:loading="acting === row.name"
					@click.stop="act(row, 'withdraw')"
				>
					Retirer
				</Button>
			</div>
		</template>
	</ResourceListPage>
</template>

<script setup>
/* Admissions (master.md §13): Application -> Review -> Acceptance ->
 * Admission -> Enrollment. The doctype behind this is Education's own
 * Student Applicant, extended with Custom Fields (setup/install.py) and a
 * pipeline of whitelisted Document methods (admissions/overrides.py) - so
 * this page reuses the generic ResourceListPage for identity/list/create/
 * edit (like Structure.vue/Scholarships.vue) and adds only what a config
 * object can't express: the stage-appropriate action buttons, called
 * through runDocMethod exactly like Announcements.vue's publish/archive
 * (docs/architecture.md section O).
 */
import { ref } from "vue";
import { Button } from "frappe-ui";
import { runDocMethod } from "@/api";
import { session } from "@/session";
import { notifyError, notifySuccess } from "@/composables/useAsync";

// Registrar (also on this page) has read/write/create but not delete on
// Student Applicant - only Academic Director does
// (setup/install.py::create_admissions_permissions).
const isAcademicDirector = session.roles.includes("Academic Director");
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const listPage = ref(null);
const acting = ref("");

const LIST_FIELDS = [
	"name",
	"title",
	"requested_grade.grade_name",
	"academic_year",
	"application_status",
	"admission_fee_required",
	"admission_fee_paid",
];

const columns = [
	{ fieldname: "title", label: "Candidat", emphasize: true },
	{ fieldname: "grade_name", label: "Classe demandée" },
	{ fieldname: "academic_year", label: "Année scolaire" },
	{
		fieldname: "application_status",
		label: "Statut",
		format: "badge",
		tone: (r) =>
			({
				Brouillon: "gray",
				Soumise: "blue",
				"En cours d'examen": "gold",
				Acceptée: "green",
				Rejetée: "red",
				"Liste d'attente": "gold",
				Inscrite: "green",
				Retirée: "gray",
			})[r.application_status] || "gray",
	},
];

const formFields = [
	{ fieldname: "first_name", label: "Prénom", type: "Data", required: true },
	{ fieldname: "last_name", label: "Nom", type: "Data" },
	{ fieldname: "gender", label: "Genre", type: "Link", doctype: "Gender" },
	{ fieldname: "date_of_birth", label: "Date de naissance", type: "Date" },
	{ fieldname: "student_email_id", label: "Email", type: "Data" },
	{ fieldname: "student_mobile_number", label: "Téléphone", type: "Data" },
	{ fieldname: "nationality", label: "Nationalité", type: "Data" },
	{ fieldname: "requested_grade", label: "Classe demandée", type: "Link", doctype: "Grade", searchField: "grade_name", required: true },
	{ fieldname: "academic_year", label: "Année scolaire", type: "Link", doctype: "Academic Year", searchField: "academic_year_name", required: true },
	{ fieldname: "previous_school", label: "École précédente", type: "Data" },
	{ fieldname: "interview_required", label: "Entretien requis", type: "Check" },
	{ fieldname: "interview_date", label: "Date de l'entretien", type: "Datetime" },
	{ fieldname: "interview_result", label: "Résultat de l'entretien", type: "Select", options: ["", "Favorable", "Défavorable", "Sous réserve"] },
	{ fieldname: "interview_notes", label: "Notes d'entretien", type: "Small Text" },
	{ fieldname: "entrance_exam_required", label: "Examen d'entrée requis", type: "Check" },
	{ fieldname: "entrance_exam_date", label: "Date de l'examen", type: "Date" },
	{ fieldname: "entrance_exam_score", label: "Note obtenue", type: "Float" },
	{ fieldname: "entrance_exam_max_score", label: "Note maximale", type: "Float" },
	{ fieldname: "decision_notes", label: "Motif de la décision", type: "Small Text" },
	{ fieldname: "admission_fee_required", label: "Frais d'inscription requis", type: "Check" },
	{ fieldname: "admission_fee_amount", label: "Montant des frais", type: "Currency" },
];

async function act(row, method, args = {}) {
	acting.value = row.name;
	try {
		await runDocMethod("Student Applicant", row.name, method, args);
		notifySuccess("Candidature mise à jour.");
		listPage.value?.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		acting.value = "";
	}
}

function decide(row, decision) {
	return act(row, "record_decision", { decision });
}

async function enroll(row) {
	acting.value = row.name;
	try {
		const r = await runDocMethod("Student Applicant", row.name, "enroll");
		notifySuccess(r?.student ? `Élève créé : ${r.student}` : "Candidature enrôlée.");
		listPage.value?.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		acting.value = "";
	}
}
</script>
