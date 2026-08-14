<template>
	<!-- Registration itself stays on the Admissions pipeline (Application ->
	     Review -> Acceptance -> Admission -> Enrollment, docs/architecture.md
	     section O) rather than a raw "Nouveau" button here - can-create is
	     deliberately off. This page is for what happens to a Student record
	     afterwards: correcting details, and the status changes master.md §10
	     already names (Suspended/Withdrawn/Transferred/Repeating/Graduated),
	     which the generic edit dialog already covers via the Statut field
	     below - no separate "suspend" action needed. -->
	<ResourceListPage
		doctype="Student"
		title="Élèves"
		icon="users"
		empty-title="Aucun élève"
		new-button-label="Nouvel élève"
		search-field="student_name"
		order-by="student_name asc"
		:list-fields="LIST_FIELDS"
		:columns="columns"
		:form-fields="formFields"
		:can-create="false"
		:can-delete="isAcademicDirector"
	/>
</template>

<script setup>
import { session } from "@/session";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

// Registrar (also on this page via academicNav's hasStructure flag) has
// read/write/create but not delete on Student/Guardian - only Academic
// Director does (setup/install.py::create_student_records_permissions).
const isAcademicDirector = session.roles.includes("Academic Director");

// Grade autonames to a random hash and School to its (non-descriptive)
// school_code - both dotted-joined to their readable name/title fields
// rather than shown raw (same pattern as Structure.vue/Pedagogy.vue).
const LIST_FIELDS = [
	"name",
	"student_name",
	"matricule",
	"grade.grade_name",
	"school.school_name",
	"status",
	"student_mobile_number",
];

const columns = [
	{ fieldname: "student_name", label: "Nom", emphasize: true },
	{ fieldname: "matricule", label: "Matricule" },
	{ fieldname: "grade_name", label: "Classe" },
	{ fieldname: "school_name", label: "École" },
	{
		fieldname: "status",
		label: "Statut",
		format: "badge",
		tone: (r) => (r.status === "Active" ? "green" : ["Suspended", "Withdrawn", "Deceased"].includes(r.status) ? "red" : "gold"),
	},
	{ fieldname: "student_mobile_number", label: "Téléphone" },
];

const formFields = [
	{ fieldname: "first_name", label: "Prénom", type: "Data", required: true },
	{ fieldname: "middle_name", label: "Deuxième prénom", type: "Data" },
	{ fieldname: "last_name", label: "Nom", type: "Data", required: true },
	{ fieldname: "gender", label: "Genre", type: "Link", doctype: "Gender" },
	{ fieldname: "date_of_birth", label: "Date de naissance", type: "Date" },
	{ fieldname: "matricule", label: "Matricule", type: "Data" },
	{ fieldname: "school", label: "École", type: "Link", doctype: "School", searchField: "school_name" },
	{ fieldname: "campus", label: "Campus", type: "Link", doctype: "Campus", searchField: "campus_name" },
	{ fieldname: "grade", label: "Classe", type: "Link", doctype: "Grade", searchField: "grade_name" },
	{
		fieldname: "status",
		label: "Statut",
		type: "Select",
		options: ["Active", "Graduated", "Transferred", "Withdrawn", "Suspended", "Repeating", "Deceased"],
		required: true,
	},
	{ fieldname: "student_email_id", label: "Email", type: "Data" },
	{ fieldname: "student_mobile_number", label: "Téléphone", type: "Data" },
];
</script>
