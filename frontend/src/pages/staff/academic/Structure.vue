<template>
	<div class="space-y-4">
		<TabButtons :buttons="tabs" v-model="tab" />

		<ResourceListPage
			v-if="tab === 'campuses'"
			key="campuses"
			doctype="Campus"
			title="Campus"
			icon="map-pin"
			empty-title="Aucun campus"
			new-button-label="Nouveau campus"
			search-field="campus_name"
			:columns="[{ fieldname: 'campus_name', label: 'Nom', emphasize: true }, { fieldname: 'city', label: 'Ville' }, { fieldname: 'is_active', label: 'Actif', format: 'check' }]"
			:form-fields="campusFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'cycles'"
			key="cycles"
			doctype="Cycle"
			title="Cycles"
			icon="repeat"
			empty-title="Aucun cycle"
			new-button-label="Nouveau cycle"
			search-field="cycle_name"
			:columns="[{ fieldname: 'cycle_name', label: 'Nom', emphasize: true }, { fieldname: 'education_level', label: 'Niveau' }]"
			:form-fields="cycleFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'levels'"
			key="levels"
			doctype="Education Level"
			title="Niveaux"
			icon="layers"
			empty-title="Aucun niveau"
			new-button-label="Nouveau niveau"
			search-field="education_level_name"
			:columns="[{ fieldname: 'education_level_name', label: 'Nom', emphasize: true }, { fieldname: 'school', label: 'École' }]"
			:form-fields="levelFields"
		/>
		<ResourceListPage
			v-else
			key="grades"
			doctype="Grade"
			title="Classes"
			icon="grid"
			empty-title="Aucune classe"
			new-button-label="Nouvelle classe"
			search-field="grade_name"
			:columns="[{ fieldname: 'grade_name', label: 'Nom', emphasize: true }, { fieldname: 'cycle', label: 'Cycle' }, { fieldname: 'stream', label: 'Filière' }]"
			:form-fields="gradeFields"
		/>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { TabButtons } from "frappe-ui";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const tabs = [
	{ label: "Campus", value: "campuses" },
	{ label: "Cycles", value: "cycles" },
	{ label: "Niveaux", value: "levels" },
	{ label: "Classes", value: "grades" },
];
const tab = ref("campuses");

const campusFields = [
	{ fieldname: "campus_name", label: "Nom du campus", type: "Data", required: true },
	{ fieldname: "school", label: "École", type: "Link", doctype: "School", searchField: "school_name", required: true },
	{ fieldname: "city", label: "Ville", type: "Data" },
	{ fieldname: "phone", label: "Téléphone", type: "Data" },
	{ fieldname: "email", label: "Email", type: "Data" },
	{ fieldname: "is_active", label: "Actif", type: "Check" },
];

const cycleFields = [
	{ fieldname: "cycle_name", label: "Nom du cycle", type: "Data", required: true },
	{ fieldname: "education_level", label: "Niveau", type: "Link", doctype: "Education Level", searchField: "education_level_name", required: true },
	{ fieldname: "school", label: "École", type: "Link", doctype: "School", searchField: "school_name" },
	{ fieldname: "sequence", label: "Ordre", type: "Int" },
];

const levelFields = [
	{ fieldname: "education_level_name", label: "Nom du niveau", type: "Data", required: true },
	{ fieldname: "school", label: "École", type: "Link", doctype: "School", searchField: "school_name", required: true },
	{ fieldname: "sequence", label: "Ordre", type: "Int" },
	{ fieldname: "description", label: "Description", type: "Small Text" },
];

const gradeFields = [
	{ fieldname: "grade_name", label: "Nom de la classe", type: "Data", required: true },
	{ fieldname: "cycle", label: "Cycle", type: "Link", doctype: "Cycle", searchField: "cycle_name", required: true },
	{ fieldname: "school", label: "École", type: "Link", doctype: "School", searchField: "school_name" },
	{ fieldname: "stream", label: "Filière", type: "Data" },
	{ fieldname: "sequence", label: "Ordre", type: "Int" },
];
</script>
