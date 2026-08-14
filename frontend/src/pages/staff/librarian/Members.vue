<template>
	<ResourceListPage
		doctype="Library Membership"
		title="Adhésions"
		icon="user-check"
		empty-title="Aucune adhésion"
		new-button-label="Nouvelle adhésion"
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
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Active" ? "green" : "gray") },
	{ fieldname: "max_books", label: "Limite" },
	{ fieldname: "issue_date", label: "Depuis le", format: "date" },
	{ fieldname: "expiry_date", label: "Expire le", format: "date" },
];

const formFields = [
	{ fieldname: "student", label: "Élève", type: "Link", doctype: "Student", searchField: "student_name", required: true },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Active", "Suspendue", "Expirée"], required: true },
	{ fieldname: "max_books", label: "Nombre maximal de livres", type: "Int", required: true },
	{ fieldname: "issue_date", label: "Date d'adhésion", type: "Date", required: true },
	{ fieldname: "expiry_date", label: "Date d'expiration", type: "Date" },
	{ fieldname: "notes", label: "Remarques", type: "Small Text" },
];
</script>
