<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<StatCard
			label="Solde total dû"
			:value="formatCurrency(data.outstanding_balance)"
			icon="credit-card"
			:tone="data.outstanding_balance > 0 ? 'red' : 'green'"
		/>

		<SectionCard title="Factures" no-padding>
			<EmptyState v-if="!data.invoices.length" icon="file-text" title="Aucune facture" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Facture</th>
						<th class="px-5 py-3">Échéance</th>
						<th class="px-5 py-3">Montant</th>
						<th class="px-5 py-3">Solde</th>
						<th class="px-5 py-3">Statut</th>
						<th class="px-5 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="inv in data.invoices" :key="inv.name" class="hover:bg-gray-50">
						<td class="px-5 py-3 font-medium text-gray-800">{{ inv.name }}</td>
						<td class="px-5 py-3">{{ formatDate(inv.due_date) }}</td>
						<td class="px-5 py-3">{{ formatCurrency(inv.grand_total, inv.currency) }}</td>
						<td class="px-5 py-3">{{ formatCurrency(inv.outstanding_amount, inv.currency) }}</td>
						<td class="px-5 py-3"><StatusBadge :text="inv.status" :tone="inv.outstanding_amount > 0 ? 'red' : 'green'" /></td>
						<td class="px-5 py-3 text-right">
							<router-link :to="invoiceRoute(inv.name)" class="text-bf-red-600 hover:underline">Détails</router-link>
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.fees(), {
	watchSource: () => props.student,
	initial: { invoices: [], outstanding_balance: 0 },
});

function invoiceRoute(name) {
	return props.student
		? { name: "child-invoice", params: { student: props.student, name } }
		: { name: "student-invoice", params: { name } };
}
</script>
