<template>
	<div class="space-y-4">
		<TabButtons :buttons="tabs" v-model="tab" />

		<ResourceListPage
			v-if="tab === 'books'"
			key="books"
			doctype="Library Book"
			title="Livres"
			icon="book"
			empty-title="Aucun livre au catalogue"
			new-button-label="Nouveau livre"
			search-field="title"
			:columns="bookColumns"
			:form-fields="bookFields"
			can-delete
		/>
		<ResourceListPage
			v-else-if="tab === 'copies'"
			key="copies"
			doctype="Library Book Copy"
			title="Exemplaires"
			icon="layers"
			empty-title="Aucun exemplaire"
			new-button-label="Nouvel exemplaire"
			:columns="copyColumns"
			:form-fields="copyFields"
			can-delete
		/>
		<ResourceListPage
			v-else-if="tab === 'authors'"
			key="authors"
			doctype="Library Author"
			title="Auteurs"
			icon="user"
			empty-title="Aucun auteur"
			new-button-label="Nouvel auteur"
			search-field="author_name"
			:columns="[{ fieldname: 'author_name', label: 'Nom', emphasize: true }]"
			:form-fields="[{ fieldname: 'author_name', label: 'Nom', type: 'Data', required: true }]"
			can-delete
		/>
		<ResourceListPage
			v-else
			key="categories"
			doctype="Library Category"
			title="Catégories"
			icon="tag"
			empty-title="Aucune catégorie"
			new-button-label="Nouvelle catégorie"
			search-field="category_name"
			:columns="[{ fieldname: 'category_name', label: 'Nom', emphasize: true }]"
			:form-fields="[{ fieldname: 'category_name', label: 'Nom', type: 'Data', required: true }]"
			can-delete
		/>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { TabButtons } from "frappe-ui";
import ResourceListPage from "@/components/resource/ResourceListPage.vue";

const tabs = [
	{ label: "Livres", value: "books" },
	{ label: "Exemplaires", value: "copies" },
	{ label: "Auteurs", value: "authors" },
	{ label: "Catégories", value: "categories" },
];
const tab = ref("books");

const bookColumns = [
	{ fieldname: "title", label: "Titre", emphasize: true },
	{ fieldname: "author", label: "Auteur" },
	{ fieldname: "category", label: "Catégorie" },
	{ fieldname: "total_copies", label: "Exemplaires" },
	{ fieldname: "available_copies", label: "Disponibles" },
];
const bookFields = [
	{ fieldname: "title", label: "Titre", type: "Data", required: true },
	{ fieldname: "author", label: "Auteur", type: "Link", doctype: "Library Author", searchField: "author_name" },
	{ fieldname: "category", label: "Catégorie", type: "Link", doctype: "Library Category", searchField: "category_name" },
	{ fieldname: "isbn", label: "ISBN", type: "Data" },
	{ fieldname: "publisher", label: "Éditeur", type: "Data" },
	{ fieldname: "edition", label: "Édition", type: "Data" },
];

const copyColumns = [
	{ fieldname: "book_title", label: "Livre", emphasize: true },
	{ fieldname: "shelf_location", label: "Emplacement" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Disponible" ? "green" : r.status === "Emprunté" ? "gold" : "red") },
];
const copyFields = [
	{ fieldname: "book", label: "Livre", type: "Link", doctype: "Library Book", searchField: "title", required: true },
	{ fieldname: "shelf_location", label: "Emplacement", type: "Data" },
	{
		fieldname: "status",
		label: "Statut",
		type: "Select",
		options: ["Disponible", "Emprunté", "Perdu", "Endommagé", "Retiré"],
		required: true,
	},
];
</script>
