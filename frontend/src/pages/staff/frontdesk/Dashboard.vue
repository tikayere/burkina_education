<template>
	<div class="space-y-4">
		<TabButtons :buttons="tabs" v-model="tab" />

		<ResourceListPage
			v-if="tab === 'students'"
			key="students"
			doctype="Student"
			title="Élèves"
			icon="user"
			empty-title="Aucun élève"
			search-field="student_name"
			:can-create="false"
			:can-edit="false"
			:list-fields="studentListFields"
			:columns="studentColumns"
			:form-fields="[]"
		/>
		<ResourceListPage
			v-else-if="tab === 'guardians'"
			key="guardians"
			doctype="Guardian"
			title="Parents & tuteurs"
			icon="users"
			empty-title="Aucun parent enregistré"
			search-field="guardian_name"
			:can-create="false"
			:can-edit="false"
			:columns="guardianColumns"
			:form-fields="[]"
		/>
		<ResourceListPage
			v-else-if="tab === 'announcements'"
			key="announcements"
			doctype="Announcement"
			title="Annonces"
			icon="bell"
			empty-title="Aucune annonce publiée"
			:can-create="false"
			:can-edit="false"
			:filters="{ publication_status: 'Published' }"
			order-by="published_on desc"
			:columns="announcementColumns"
			:form-fields="[]"
		/>
	</div>
</template>

<script setup>
/* Front-desk directory - read-only lookup of "who is this / how do I reach
 * their guardian" (master.md §3 "Receptionist"), plus the published
 * announcements a visitor might ask about. Same generic ResourceListPage
 * every other staff portal uses (docs/architecture.md section M/N), just
 * with canCreate/canEdit off and no formFields - a Receptionist reads,
 * never maintains, these records (least privilege - see
 * setup/install.py::create_receptionist_permissions).
 */
import { ref } from "vue";
import { TabButtons } from "frappe-ui";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const tabs = [
	{ label: "Élèves", value: "students" },
	{ label: "Parents & tuteurs", value: "guardians" },
	{ label: "Annonces", value: "announcements" },
];
const tab = ref("students");

// Grade's own name is an opaque hash (docs/architecture.md - see Grade
// doctype's autoname) - "grade.grade_name" is Frappe's dotted-link-join
// syntax (frappe.client.get_list auto-joins "Grade" and returns the value
// under the trailing key "grade_name"), so the table shows "6ème A" instead
// of the raw Grade id.
const studentListFields = ["name", "student_name", "matricule", "grade.grade_name", "student_mobile_number", "status"];
const studentColumns = [
	{ fieldname: "student_name", label: "Nom", emphasize: true },
	{ fieldname: "matricule", label: "Matricule" },
	{ fieldname: "grade_name", label: "Classe" },
	{ fieldname: "student_mobile_number", label: "Téléphone" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Active" ? "green" : "gray") },
];

const guardianColumns = [
	{ fieldname: "guardian_name", label: "Nom", emphasize: true },
	{ fieldname: "mobile_number", label: "Téléphone" },
	{ fieldname: "whatsapp_number", label: "WhatsApp" },
	{ fieldname: "email_address", label: "E-mail" },
	{ fieldname: "occupation", label: "Profession" },
];

const announcementColumns = [
	{ fieldname: "title", label: "Titre", emphasize: true },
	{ fieldname: "audience_type", label: "Audience" },
	{ fieldname: "published_on", label: "Publiée le", format: "date" },
];
</script>
