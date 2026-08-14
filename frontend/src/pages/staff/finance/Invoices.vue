<template>
	<div class="space-y-4">
		<div class="relative w-full max-w-xs">
			<FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
			<input
				v-model="query"
				type="text"
				placeholder="Rechercher un élève..."
				class="w-full rounded-md border-gray-200 py-1.5 pl-8 text-sm focus:border-bf-green-400 focus:ring-bf-green-400"
				@input="onSearch"
			/>
		</div>

		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
		</div>
		<SectionCard v-else no-padding>
			<EmptyState v-if="!list.data?.length" icon="file-text" title="Aucune facture" />
			<ResourceTable v-else :columns="columns" :rows="list.data" :on-row-click="(row) => $router.push({ name: 'finance-invoice-detail', params: { name: row.name } })" />
		</SectionCard>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { FeatherIcon, LoadingIndicator, createListResource } from "frappe-ui";
import { notifyError } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import ResourceTable from "@/components/resource/ResourceTable.vue";

const query = ref("");
let searchDebounce = null;

const list = createListResource({
	doctype: "Sales Invoice",
	fields: ["name", "student", "customer_name", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "currency"],
	filters: { docstatus: 1 },
	orderBy: "posting_date desc",
	pageLength: 50,
	auto: true,
	onError: (e) => notifyError(e),
});

const columns = [
	{ fieldname: "name", label: "Facture", emphasize: true },
	{ fieldname: "customer_name", label: "Élève" },
	{ fieldname: "posting_date", label: "Émise le", format: "date" },
	{ fieldname: "due_date", label: "Échéance", format: "date" },
	{ fieldname: "grand_total", label: "Montant", format: "currency" },
	{ fieldname: "outstanding_amount", label: "Solde dû", format: "currency" },
	{ fieldname: "status", label: "Statut", format: "badge", tone: (r) => (r.status === "Paid" ? "green" : r.status === "Overdue" ? "red" : "gold") },
];

function onSearch() {
	clearTimeout(searchDebounce);
	searchDebounce = setTimeout(() => {
		list.filters = { docstatus: 1, ...(query.value ? { customer_name: ["like", `%${query.value}%`] } : {}) };
		list.reload();
	}, 250);
}
</script>
