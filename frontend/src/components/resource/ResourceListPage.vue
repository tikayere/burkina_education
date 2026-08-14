<template>
	<div class="space-y-4">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div class="relative w-full max-w-xs" v-if="searchField">
				<FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
				<input
					v-model="query"
					type="text"
					placeholder="Rechercher..."
					class="w-full rounded-md border-gray-200 py-1.5 pl-8 text-sm focus:border-bf-green-400 focus:ring-bf-green-400"
					@input="onSearch"
				/>
			</div>
			<div v-else />
			<Button v-if="canCreate" variant="solid" theme="green" @click="openCreate">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				{{ newButtonLabel }}
			</Button>
		</div>

		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
		</div>
		<SectionCard v-else no-padding>
			<EmptyState v-if="!list.data?.length" :icon="icon" :title="emptyTitle" />
			<ResourceTable v-else :columns="columns" :rows="list.data" :on-row-click="canEdit ? openEdit : null">
				<template v-if="canDelete || $slots.rowActions" #actions="{ row }">
					<div class="flex items-center justify-end gap-2">
						<slot name="rowActions" :row="row" />
						<button v-if="canDelete" class="text-gray-400 hover:text-bf-red-500" @click="confirmDelete(row)">
							<FeatherIcon name="trash-2" class="h-4 w-4" />
						</button>
					</div>
				</template>
			</ResourceTable>
		</SectionCard>

		<ResourceFormDialog
			v-model="dialogOpen"
			:doctype="doctype"
			:title="editingRecord ? `Modifier - ${title}` : newButtonLabel"
			:fields="formFields"
			:record="editingRecord"
			:defaults="defaults"
			@saved="list.reload()"
		/>
	</div>
</template>

<script setup>
/* Generic list+create+edit page for the plain-CRUD doctypes the staff
 * portals expose directly (docs/architecture.md section M) - a whole
 * page/tab is a config object (columns + form fields) plus this component,
 * rather than a bespoke .vue file per doctype. Pages with real custom
 * workflow (issuing a book, marking a meal roster, ...) still get their own
 * component; this is only for "list it, create it, edit it".
 */
import { ref } from "vue";
import { Button, FeatherIcon, LoadingIndicator, confirmDialog, createListResource } from "frappe-ui";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import ResourceTable from "@/components/resource/ResourceTable.vue";
import ResourceFormDialog from "@/components/resource/ResourceFormDialog.vue";

const props = defineProps({
	doctype: { type: String, required: true },
	title: { type: String, required: true },
	icon: { type: String, default: "list" },
	emptyTitle: { type: String, default: "Aucun élément" },
	newButtonLabel: { type: String, default: "Nouveau" },
	columns: { type: Array, required: true },
	formFields: { type: Array, required: true },
	listFields: { type: Array, default: null },
	filters: { type: Object, default: () => ({}) },
	defaults: { type: Object, default: () => ({}) },
	orderBy: { type: String, default: "modified desc" },
	searchField: { type: String, default: "" },
	canCreate: { type: Boolean, default: true },
	canEdit: { type: Boolean, default: true },
	canDelete: { type: Boolean, default: false },
	pageLength: { type: Number, default: 50 },
});

const dialogOpen = ref(false);
const editingRecord = ref(null);
const query = ref("");
let searchDebounce = null;

const fields = props.listFields || Array.from(new Set(["name", ...props.columns.map((c) => c.fieldname), ...props.formFields.map((f) => f.fieldname)]));

const list = createListResource({
	doctype: props.doctype,
	fields,
	filters: props.filters,
	orderBy: props.orderBy,
	pageLength: props.pageLength,
	auto: true,
	onError: (e) => notifyError(e),
});

function openCreate() {
	editingRecord.value = null;
	dialogOpen.value = true;
}

function openEdit(row) {
	editingRecord.value = row;
	dialogOpen.value = true;
}

function onSearch() {
	clearTimeout(searchDebounce);
	searchDebounce = setTimeout(() => {
		list.filters = { ...props.filters };
		if (query.value) list.filters[props.searchField] = ["like", `%${query.value}%`];
		list.reload();
	}, 250);
}

function confirmDelete(row) {
	confirmDialog({
		title: "Confirmer la suppression",
		message: `Voulez-vous vraiment supprimer « ${row[props.searchField] || row.name} » ? Cette action est irréversible.`,
		onConfirm: async ({ hideDialog }) => {
			try {
				await list.delete.submit(row.name);
				notifySuccess("Élément supprimé.");
				hideDialog();
			} catch (e) {
				notifyError(e);
			}
		},
	});
}

defineExpose({ reload: () => list.reload() });
</script>
