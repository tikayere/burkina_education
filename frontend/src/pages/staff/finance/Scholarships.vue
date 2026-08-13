<template>
	<ResourceListPage
		doctype="Scholarship"
		title="Bourses"
		icon="award"
		empty-title="Aucune bourse"
		new-button-label="Nouvelle bourse"
		search-field="student_name"
		:columns="columns"
		:form-fields="formFields"
	/>
</template>

<script setup>
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const columns = [
	{ fieldname: "student_name", label: "Élève", emphasize: true },
	{ fieldname: "scholarship_type", label: "Type" },
	{ fieldname: "discount_percent", label: "Réduction", render: (r) => `${r.discount_percent}%` },
	{ fieldname: "fee_category", label: "Catégorie de frais" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Approuvée" ? "green" : r.status === "Rejetée" ? "red" : "gold") },
];

const formFields = [
	{ fieldname: "student", label: "Élève", type: "Link", doctype: "Student", searchField: "student_name", required: true },
	{ fieldname: "academic_year", label: "Année scolaire", type: "Link", doctype: "Academic Year", searchField: "academic_year_name", required: true },
	{ fieldname: "scholarship_type", label: "Type de bourse", type: "Select", options: ["Bourse Partielle", "Bourse Totale"], required: true },
	{ fieldname: "discount_percent", label: "Pourcentage de réduction", type: "Percent", required: true },
	{ fieldname: "fee_category", label: "Catégorie de frais", type: "Link", doctype: "Fee Category", searchField: "category_name" },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Brouillon", "Approuvée", "Rejetée"], required: true },
	{ fieldname: "reason", label: "Motif", type: "Small Text" },
];
</script>
