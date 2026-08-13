<template>
	<div class="space-y-4">
		<TabButtons :buttons="tabs" v-model="tab" />

		<ResourceListPage
			v-if="tab === 'buildings'"
			key="buildings"
			doctype="Boarding Building"
			title="Bâtiments"
			icon="layers"
			empty-title="Aucun bâtiment"
			new-button-label="Nouveau bâtiment"
			search-field="building_name"
			:list-fields="buildingListFields"
			:columns="buildingColumns"
			:form-fields="buildingFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'rooms'"
			key="rooms"
			doctype="Boarding Room"
			title="Chambres"
			icon="grid"
			empty-title="Aucune chambre"
			new-button-label="Nouvelle chambre"
			:columns="roomColumns"
			:form-fields="roomFields"
		/>
		<ResourceListPage
			v-else
			key="beds"
			doctype="Boarding Bed"
			title="Lits"
			icon="moon"
			empty-title="Aucun lit"
			new-button-label="Nouveau lit"
			:columns="bedColumns"
			:form-fields="bedFields"
		/>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { TabButtons } from "frappe-ui";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const tabs = [
	{ label: "Bâtiments", value: "buildings" },
	{ label: "Chambres", value: "rooms" },
	{ label: "Lits", value: "beds" },
];
const tab = ref("buildings");

// Employee autonames to an opaque naming series (docs/architecture.md) -
// dotted-link-join so the table shows the supervisor's real name.
const buildingListFields = ["name", "building_name", "supervisor.employee_name as supervisor_name"];
const buildingColumns = [
	{ fieldname: "building_name", label: "Nom", emphasize: true },
	{ fieldname: "supervisor_name", label: "Surveillant" },
];
const buildingFields = [
	{ fieldname: "building_name", label: "Nom du bâtiment", type: "Data", required: true },
	{ fieldname: "supervisor", label: "Surveillant", type: "Link", doctype: "Employee", searchField: "employee_name" },
];

const roomColumns = [
	{ fieldname: "building", label: "Bâtiment" },
	{ fieldname: "room_number", label: "N° de chambre", emphasize: true },
	{ fieldname: "floor", label: "Étage" },
	{ fieldname: "capacity", label: "Capacité" },
];
const roomFields = [
	{ fieldname: "building", label: "Bâtiment", type: "Link", doctype: "Boarding Building", searchField: "building_name", required: true },
	{ fieldname: "room_number", label: "N° de chambre", type: "Data", required: true },
	{ fieldname: "floor", label: "Étage", type: "Data" },
	{ fieldname: "capacity", label: "Capacité (lits)", type: "Int", required: true },
];

const bedColumns = [
	{ fieldname: "room", label: "Chambre" },
	{ fieldname: "bed_number", label: "N° de lit", emphasize: true },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Disponible" ? "green" : r.status === "Occupé" ? "gold" : "red") },
];
const bedFields = [
	{ fieldname: "room", label: "Chambre", type: "Link", doctype: "Boarding Room", searchField: "room_number", required: true },
	{ fieldname: "bed_number", label: "N° de lit", type: "Data", required: true },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Disponible", "Occupé", "Hors service"], required: true },
];
</script>
