<template>
	<ResourceListPage
		:key="route.query.route || 'all'"
		doctype="Student Transport Assignment"
		title="Affectations transport"
		icon="users"
		empty-title="Aucune affectation"
		new-button-label="Nouvelle affectation"
		search-field="student_name"
		:filters="filters"
		:columns="columns"
		:form-fields="formFields"
		:defaults="filters"
		can-delete
	/>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const route = useRoute();
const filters = computed(() => (route.query.route ? { route: route.query.route } : {}));

const columns = [
	{ fieldname: "student_name", label: "Élève", emphasize: true },
	{ fieldname: "route", label: "Itinéraire" },
	{ fieldname: "stop_name", label: "Arrêt" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Actif" ? "green" : "gray") },
	{ fieldname: "start_date", label: "Depuis le", format: "date" },
];

const formFields = [
	{ fieldname: "student", label: "Élève", type: "Link", doctype: "Student", searchField: "student_name", required: true },
	{ fieldname: "academic_year", label: "Année scolaire", type: "Link", doctype: "Academic Year", searchField: "academic_year_name", required: true },
	{ fieldname: "route", label: "Itinéraire", type: "Link", doctype: "Transport Route", searchField: "route_name", required: true },
	{ fieldname: "stop_name", label: "Arrêt", type: "Data", required: true },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Actif", "Suspendu", "Terminé"], required: true },
	{ fieldname: "start_date", label: "Date de début", type: "Date", required: true },
	{ fieldname: "end_date", label: "Date de fin", type: "Date" },
];
</script>
