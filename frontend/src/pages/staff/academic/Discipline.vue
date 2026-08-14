<template>
	<!-- Reached from both the academic (Academic Director) and leadership
	     (School Director) portals - both hold delete on Disciplinary Case
	     (setup/install.py's per-doctype grants), so can-delete is
	     unconditional rather than role-gated here. -->
	<ResourceListPage
		doctype="Disciplinary Case"
		title="Discipline"
		icon="shield"
		empty-title="Aucun dossier disciplinaire"
		new-button-label="Nouveau signalement"
		search-field="student_name"
		order-by="date desc"
		:columns="columns"
		:form-fields="formFields"
		can-delete
	/>
</template>

<script setup>
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const columns = [
	{ fieldname: "student_name", label: "Élève", emphasize: true },
	{ fieldname: "incident_type", label: "Type" },
	{ fieldname: "severity", label: "Gravité", format: "badge", tone: (r) => (r.severity === "Grave" ? "red" : r.severity === "Modérée" ? "gold" : "gray") },
	{ fieldname: "date", label: "Date", format: "date" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Résolu" ? "green" : "red") },
];

const formFields = [
	{ fieldname: "student", label: "Élève", type: "Link", doctype: "Student", searchField: "student_name", required: true },
	{ fieldname: "incident_type", label: "Type d'incident", type: "Select", options: ["Comportement", "Retard", "Absence non justifiée", "Violence", "Vol", "Fraude aux examens", "Dégradation de matériel", "Autre"], required: true },
	{ fieldname: "severity", label: "Gravité", type: "Select", options: ["Mineure", "Modérée", "Grave"], required: true },
	{ fieldname: "date", label: "Date", type: "Date", required: true },
	{ fieldname: "description", label: "Description", type: "Small Text", required: true },
	{ fieldname: "action_taken", label: "Mesure prise", type: "Small Text" },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Ouvert", "En cours", "Résolu"], required: true },
];
</script>
