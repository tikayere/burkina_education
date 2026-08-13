<template>
	<div class="space-y-4">
		<TabButtons :buttons="tabs" v-model="tab" />

		<ResourceListPage
			v-if="tab === 'curriculum'"
			key="curriculum"
			doctype="Curriculum"
			title="Curriculums"
			icon="book"
			empty-title="Aucun curriculum"
			new-button-label="Nouveau curriculum"
			:list-fields="curriculumListFields"
			:columns="curriculumColumns"
			:form-fields="curriculumFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'competencies'"
			key="competencies"
			doctype="Competency"
			title="Compétences"
			icon="target"
			empty-title="Aucune compétence"
			new-button-label="Nouvelle compétence"
			search-field="title"
			:list-fields="['name', 'title', 'curriculum.title as curriculum_title', 'code']"
			:columns="[{ fieldname: 'title', label: 'Titre', emphasize: true }, { fieldname: 'curriculum_title', label: 'Curriculum' }, { fieldname: 'code', label: 'Code' }]"
			:form-fields="competencyFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'units'"
			key="units"
			doctype="Learning Unit"
			title="Unités d'apprentissage"
			icon="package"
			empty-title="Aucune unité"
			new-button-label="Nouvelle unité"
			search-field="title"
			:list-fields="['name', 'title', 'curriculum.title as curriculum_title', 'estimated_hours']"
			:columns="[{ fieldname: 'title', label: 'Titre', emphasize: true }, { fieldname: 'curriculum_title', label: 'Curriculum' }, { fieldname: 'estimated_hours', label: 'Heures estimées' }]"
			:form-fields="unitFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'lessons'"
			key="lessons"
			doctype="Lesson"
			title="Leçons"
			icon="edit-2"
			empty-title="Aucune leçon"
			new-button-label="Nouvelle leçon"
			search-field="title"
			:list-fields="lessonListFields"
			:columns="lessonColumns"
			:form-fields="lessonFields"
		/>
		<ResourceListPage
			v-else-if="tab === 'grading'"
			key="grading"
			doctype="Grading Scheme"
			title="Barèmes de notation"
			icon="award"
			empty-title="Aucun barème"
			new-button-label="Nouveau barème"
			search-field="scheme_name"
			:list-fields="['name', 'scheme_name', 'education_level.education_level_name', 'score_max', 'is_default']"
			:columns="[{ fieldname: 'scheme_name', label: 'Nom', emphasize: true }, { fieldname: 'education_level_name', label: 'Niveau' }, { fieldname: 'score_max', label: 'Note max.' }, { fieldname: 'is_default', label: 'Par défaut', format: 'check' }]"
			:form-fields="gradingFields"
		/>
		<ResourceListPage
			v-else
			key="assessment-types"
			doctype="Assessment Type"
			title="Types d'évaluation"
			icon="check-square"
			empty-title="Aucun type d'évaluation"
			new-button-label="Nouveau type"
			search-field="type_name"
			:columns="[{ fieldname: 'type_name', label: 'Nom', emphasize: true }, { fieldname: 'category', label: 'Catégorie' }, { fieldname: 'default_coefficient', label: 'Coefficient' }]"
			:form-fields="assessmentTypeFields"
		/>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { TabButtons } from "frappe-ui";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const tabs = [
	{ label: "Curriculums", value: "curriculum" },
	{ label: "Compétences", value: "competencies" },
	{ label: "Unités", value: "units" },
	{ label: "Leçons", value: "lessons" },
	{ label: "Barèmes", value: "grading" },
	{ label: "Types d'évaluation", value: "assessment-types" },
];
const tab = ref("curriculum");

// Grade autonames to an opaque hash (docs/architecture.md), so the table
// joins to its "grade_name" via Frappe's dotted-link-join syntax
// (frappe.client.get_list auto-joins Grade and returns the value under the
// trailing key) rather than showing the raw id. Course/Academic Year both
// already autoname to their own readable name, so they're left as-is.
const curriculumListFields = ["name", "grade.grade_name", "course", "academic_year", "is_active"];
const curriculumColumns = [
	{ fieldname: "grade_name", label: "Classe", emphasize: true },
	{ fieldname: "course", label: "Matière" },
	{ fieldname: "academic_year", label: "Année" },
	{ fieldname: "is_active", label: "Actif", format: "check" },
];

const curriculumFields = [
	{ fieldname: "grade", label: "Classe", type: "Link", doctype: "Grade", searchField: "grade_name", required: true },
	{ fieldname: "course", label: "Matière", type: "Link", doctype: "Course", searchField: "course_name", required: true },
	{ fieldname: "academic_year", label: "Année scolaire", type: "Link", doctype: "Academic Year", searchField: "academic_year_name", required: true },
	{ fieldname: "title", label: "Titre", type: "Data" },
	{ fieldname: "is_active", label: "Actif", type: "Check" },
	{ fieldname: "description", label: "Description", type: "Small Text" },
];

const competencyFields = [
	{ fieldname: "curriculum", label: "Curriculum", type: "Link", doctype: "Curriculum", required: true },
	{ fieldname: "title", label: "Titre", type: "Data", required: true },
	{ fieldname: "code", label: "Code", type: "Data" },
	{ fieldname: "sequence", label: "Ordre", type: "Int" },
	{ fieldname: "description", label: "Description", type: "Small Text" },
];

const unitFields = [
	{ fieldname: "curriculum", label: "Curriculum", type: "Link", doctype: "Curriculum", required: true },
	{ fieldname: "title", label: "Titre", type: "Data", required: true },
	{ fieldname: "sequence", label: "Ordre", type: "Int" },
	{ fieldname: "estimated_hours", label: "Heures estimées", type: "Float" },
	{ fieldname: "description", label: "Description", type: "Small Text" },
];

// Learning Unit also autonames to an opaque hash - same dotted-join fix.
const lessonListFields = ["name", "title", "learning_unit.title as learning_unit_title", "planned_date", "status"];
const lessonColumns = [
	{ fieldname: "title", label: "Titre", emphasize: true },
	{ fieldname: "learning_unit_title", label: "Unité" },
	{ fieldname: "planned_date", label: "Date prévue", format: "date" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Delivered" ? "green" : r.status === "Cancelled" ? "red" : "gray") },
];
const lessonFields = [
	{ fieldname: "learning_unit", label: "Unité d'apprentissage", type: "Link", doctype: "Learning Unit", required: true },
	{ fieldname: "title", label: "Titre", type: "Data", required: true },
	{ fieldname: "sequence", label: "Ordre", type: "Int" },
	{ fieldname: "status", label: "Statut", type: "Select", options: ["Planned", "Delivered", "Cancelled"] },
	{ fieldname: "instructor", label: "Enseignant", type: "Link", doctype: "Instructor", searchField: "instructor_name" },
	{ fieldname: "planned_date", label: "Date prévue", type: "Date" },
	{ fieldname: "duration_minutes", label: "Durée (minutes)", type: "Int" },
];

const gradingFields = [
	{ fieldname: "scheme_name", label: "Nom du barème", type: "Data", required: true },
	{ fieldname: "education_level", label: "Niveau", type: "Link", doctype: "Education Level", searchField: "education_level_name" },
	{ fieldname: "score_max", label: "Note maximale", type: "Float", required: true },
	{ fieldname: "passing_score", label: "Note de passage", type: "Float", required: true },
	{ fieldname: "rounding_precision", label: "Précision d'arrondi", type: "Int" },
	{ fieldname: "use_coefficients", label: "Utiliser les coefficients", type: "Check" },
	{ fieldname: "is_default", label: "Barème par défaut", type: "Check" },
	{ fieldname: "is_active", label: "Actif", type: "Check" },
];

const assessmentTypeFields = [
	{ fieldname: "type_name", label: "Nom", type: "Data", required: true },
	{ fieldname: "category", label: "Catégorie", type: "Select", options: ["Devoir", "Composition", "Interrogation", "Examen", "Projet", "Oral", "Pratique", "Autre"], required: true },
	{ fieldname: "grading_type", label: "Type de notation", type: "Select", options: ["Numeric", "Letter", "Competency", "Pass/Fail", "Custom"] },
	{ fieldname: "default_coefficient", label: "Coefficient par défaut", type: "Float", required: true },
	{ fieldname: "is_active", label: "Actif", type: "Check" },
];
</script>
