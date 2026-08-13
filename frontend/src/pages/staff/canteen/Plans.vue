<template>
	<ResourceListPage
		doctype="Meal Plan"
		title="Formules"
		icon="clipboard"
		empty-title="Aucune formule"
		new-button-label="Nouvelle formule"
		search-field="plan_name"
		:columns="columns"
		:form-fields="formFields"
	/>
</template>

<script setup>
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const columns = [
	{ fieldname: "plan_name", label: "Formule", emphasize: true },
	{ fieldname: "price_per_month", label: "Prix / mois", format: "currency" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Active" ? "green" : "gray") },
];

const formFields = [
	{ fieldname: "plan_name", label: "Nom de la formule", type: "Data", required: true },
	{ fieldname: "price_per_month", label: "Prix par mois (XOF)", type: "Currency", required: true },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Active", "Inactive"], required: true },
	{ fieldname: "description", label: "Description", type: "Small Text" },
];
</script>
