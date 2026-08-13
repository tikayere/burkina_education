<template>
	<div class="space-y-4">
		<TabButtons :buttons="tabs" v-model="tab" />

		<ResourceListPage
			v-if="tab === 'exams'"
			key="exams"
			doctype="Examination"
			title="Examens"
			icon="clipboard"
			empty-title="Aucun examen"
			new-button-label="Nouvel examen"
			search-field="examination_name"
			order-by="from_date desc"
			:columns="examColumns"
			:form-fields="examFields"
		/>
		<ResourceListPage
			v-else
			key="schedules"
			doctype="Examination Schedule"
			title="Programmations"
			icon="calendar"
			empty-title="Aucune programmation"
			new-button-label="Nouvelle programmation"
			order-by="exam_date desc"
			:list-fields="scheduleListFields"
			:columns="scheduleColumns"
			:form-fields="scheduleFields"
		/>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { TabButtons } from "frappe-ui";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const tabs = [
	{ label: "Examens", value: "exams" },
	{ label: "Programmations", value: "schedules" },
];
const tab = ref("exams");

const examColumns = [
	{ fieldname: "examination_name", label: "Nom", emphasize: true },
	{ fieldname: "exam_type", label: "Type" },
	{ fieldname: "from_date", label: "Du", format: "date" },
	{ fieldname: "to_date", label: "Au", format: "date" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Completed" ? "green" : r.status === "Cancelled" ? "red" : "gold") },
];
const examFields = [
	{ fieldname: "examination_name", label: "Nom de l'examen", type: "Data", required: true },
	{ fieldname: "exam_type", label: "Type", type: "Select", options: ["Devoir Surveille", "Composition", "Examen Blanc", "Examen National"], required: true },
	{ fieldname: "academic_year", label: "Année scolaire", type: "Link", doctype: "Academic Year", searchField: "academic_year_name", required: true },
	{ fieldname: "academic_term", label: "Trimestre", type: "Link", doctype: "Academic Term", searchField: "term_name" },
	{ fieldname: "education_level", label: "Niveau", type: "Link", doctype: "Education Level", searchField: "education_level_name" },
	{ fieldname: "from_date", label: "Date de début", type: "Date", required: true },
	{ fieldname: "to_date", label: "Date de fin", type: "Date", required: true },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Draft", "Scheduled", "Ongoing", "Completed", "Cancelled"], required: true },
	{ fieldname: "description", label: "Description", type: "Small Text" },
];

// Examination Schedule/Grade/Room all autoname to an opaque id (see each
// doctype's own docs/architecture.md entry) - "<link>.<name_field>" is
// Frappe's dotted-link-join syntax (frappe.client.get_list auto-joins and
// returns the value under the trailing key), so the table shows real names
// instead of raw ids. Course keeps its plain fieldname: Course already
// autonames to its own course_name, so the raw id is already readable.
const scheduleListFields = [
	"name",
	"examination.examination_name",
	"grade.grade_name",
	"course",
	"exam_date",
	"room.room_name",
	"status",
];
const scheduleColumns = [
	{ fieldname: "examination_name", label: "Examen", emphasize: true },
	{ fieldname: "grade_name", label: "Classe" },
	{ fieldname: "course", label: "Matière" },
	{ fieldname: "exam_date", label: "Date", format: "date" },
	{ fieldname: "room_name", label: "Salle" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Completed" ? "green" : r.status === "Cancelled" ? "red" : "gold") },
];
const scheduleFields = [
	{ fieldname: "examination", label: "Examen", type: "Link", doctype: "Examination", searchField: "examination_name", required: true },
	{ fieldname: "grade", label: "Classe", type: "Link", doctype: "Grade", searchField: "grade_name", required: true },
	{ fieldname: "student_group", label: "Groupe d'élèves", type: "Link", doctype: "Student Group", searchField: "student_group_name" },
	{ fieldname: "course", label: "Matière", type: "Link", doctype: "Course", searchField: "course_name", required: true },
	{ fieldname: "assessment_type", label: "Type d'évaluation", type: "Link", doctype: "Assessment Type", searchField: "type_name" },
	{ fieldname: "exam_date", label: "Date de l'examen", type: "Date", required: true },
	{ fieldname: "from_time", label: "Heure de début", type: "Time" },
	{ fieldname: "to_time", label: "Heure de fin", type: "Time" },
	{ fieldname: "room", label: "Salle", type: "Link", doctype: "Room", searchField: "room_name" },
	{ fieldname: "invigilator", label: "Surveillant", type: "Link", doctype: "Instructor", searchField: "instructor_name" },
	{ fieldname: "max_score", label: "Note maximale", type: "Float" },
	{ fieldname: "coefficient", label: "Coefficient", type: "Float" },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Draft", "Scheduled", "Ongoing", "Completed", "Cancelled"], required: true },
];
</script>
