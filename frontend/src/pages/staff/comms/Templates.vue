<template>
	<ResourceListPage
		doctype="Notification Template"
		title="Modèles de notification"
		icon="file-text"
		empty-title="Aucun modèle"
		new-button-label="Nouveau modèle"
		search-field="template_name"
		:columns="columns"
		:form-fields="formFields"
	/>
</template>

<script setup>
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const columns = [
	{ fieldname: "template_name", label: "Nom", emphasize: true },
	{ fieldname: "event_key", label: "Événement" },
	{ fieldname: "channel", label: "Canal" },
	{ fieldname: "is_active", label: "Actif", format: "check" },
];

const formFields = [
	{ fieldname: "template_name", label: "Nom du modèle", type: "Data", required: true },
	{
		fieldname: "event_key",
		label: "Événement",
		type: "Select",
		options: [
			"Absence Notification",
			"Payment Confirmation",
			"Fee Reminder",
			"Result Available",
			"School Announcement",
			"Emergency Message",
			"Parent Meeting",
			"Timetable Change",
			"Library Book Overdue",
			"Other",
		],
		required: true,
	},
	{ fieldname: "channel", label: "Canal", type: "Select", options: ["SMS", "WhatsApp", "Email", "In-App"], required: true },
	{ fieldname: "subject", label: "Sujet (Email)", type: "Data" },
	{ fieldname: "body", label: "Contenu (Jinja)", type: "Code", required: true },
	{ fieldname: "is_active", label: "Actif", type: "Check" },
];
</script>
