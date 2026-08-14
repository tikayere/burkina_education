<template>
	<ResourceListPage
		doctype="Clinic Visit"
		title="Visites"
		icon="activity"
		empty-title="Aucune visite"
		new-button-label="Nouvelle visite"
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
	{ fieldname: "date", label: "Date", format: "datetime" },
	{ fieldname: "complaint", label: "Motif" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Clos" ? "green" : r.status === "Suivi requis" ? "red" : "gold") },
	{ fieldname: "parent_notified", label: "Parent informé", format: "check" },
];

const formFields = [
	{ fieldname: "student", label: "Élève", type: "Link", doctype: "Student", searchField: "student_name", required: true },
	{ fieldname: "date", label: "Date et heure", type: "Datetime", required: true },
	{ fieldname: "complaint", label: "Motif de la visite", type: "Small Text", required: true },
	{ fieldname: "treatment", label: "Soins prodigués", type: "Small Text" },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Ouvert", "Suivi requis", "Clos"], required: true },
	{ fieldname: "referral", label: "Orientation", type: "Select", options: ["Aucun", "Médecin", "Hôpital", "Pharmacie"] },
	{ fieldname: "referral_details", label: "Détails de l'orientation", type: "Small Text" },
	{ fieldname: "parent_notified", label: "Parent informé", type: "Check" },
	{ fieldname: "follow_up", label: "Suivi", type: "Small Text" },
];
</script>
