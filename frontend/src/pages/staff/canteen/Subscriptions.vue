<template>
	<ResourceListPage
		doctype="Canteen Subscription"
		title="Abonnements"
		icon="users"
		empty-title="Aucun abonnement"
		new-button-label="Nouvel abonnement"
		search-field="student_name"
		:columns="columns"
		:form-fields="formFields"
		can-delete
	/>
</template>

<script setup>
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const columns = [
	{ fieldname: "student_name", label: "Élève", emphasize: true },
	{ fieldname: "meal_plan", label: "Formule" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Active" ? "green" : "gray") },
	{ fieldname: "start_date", label: "Depuis le", format: "date" },
	{ fieldname: "end_date", label: "Jusqu'au", format: "date" },
];

const formFields = [
	{ fieldname: "student", label: "Élève", type: "Link", doctype: "Student", searchField: "student_name", required: true },
	{ fieldname: "meal_plan", label: "Formule", type: "Link", doctype: "Meal Plan", searchField: "plan_name", required: true },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Active", "Suspendue", "Terminée"], required: true },
	{ fieldname: "start_date", label: "Date de début", type: "Date", required: true },
	{ fieldname: "end_date", label: "Date de fin", type: "Date" },
];
</script>
