<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
			<StatCard label="Solde impayé" :value="formatCurrency(data.outstanding_total)" :hint="`${data.outstanding_count} facture(s)`" icon="file-text" tone="gold" />
			<StatCard label="En retard" :value="formatCurrency(data.overdue_total)" :hint="`${data.overdue_count} facture(s)`" icon="alert-triangle" :tone="data.overdue_count ? 'red' : 'gray'" />
			<StatCard label="Encaissé ce mois-ci" :value="formatCurrency(data.collected_this_month)" icon="trending-up" tone="green" />
			<StatCard label="Mobile money en attente" :value="data.pending_mobile_money" icon="smartphone" :tone="data.pending_mobile_money ? 'gold' : 'gray'" />
		</div>

		<SectionCard title="Encaissements" subtitle="6 derniers mois - paiements reçus">
			<TrendChart
				:labels="data.monthly_collections.map((m) => m.label)"
				:values="data.monthly_collections.map((m) => m.amount)"
				:format-value="formatCurrency"
				:min="0"
				:height="160"
			/>
		</SectionCard>

		<div class="grid gap-6 lg:grid-cols-2">
			<SectionCard title="Factures les plus en retard" no-padding>
				<EmptyState v-if="!data.top_overdue.length" icon="check-circle" title="Aucun retard" />
				<table v-else class="w-full text-sm">
					<tbody class="divide-y divide-gray-100">
						<tr v-for="i in data.top_overdue" :key="i.name" class="cursor-pointer hover:bg-gray-50" @click="$router.push({ name: 'finance-invoice-detail', params: { name: i.name } })">
							<td class="px-5 py-3 font-medium text-gray-800">{{ i.student_name || i.student }}</td>
							<td class="px-5 py-3 text-gray-500">{{ formatDate(i.due_date) }}</td>
							<td class="px-5 py-3 text-right text-bf-red-600">{{ formatCurrency(i.outstanding_amount) }}</td>
						</tr>
					</tbody>
				</table>
			</SectionCard>

			<SectionCard title="Recettes par catégorie">
				<EmptyState v-if="!data.by_category.length" icon="pie-chart" title="Aucune donnée" />
				<template v-else>
					<BarChart
						:data="data.by_category.map((c) => ({ label: c.fee_category, value: c.invoiced_amount }))"
						:format-value="formatCurrency"
						:height="150"
					/>
					<table class="mt-4 w-full text-sm">
						<tbody class="divide-y divide-gray-100">
							<tr v-for="c in data.by_category" :key="c.fee_category">
								<td class="px-5 py-3 font-medium text-gray-800">{{ c.fee_category }}</td>
								<td class="px-5 py-3 text-gray-500">{{ c.invoice_count }} facture(s)</td>
								<td class="px-5 py-3 text-right">{{ formatCurrency(c.invoiced_amount) }}</td>
							</tr>
						</tbody>
					</table>
				</template>
			</SectionCard>
		</div>
	</div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";
import { financeApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import TrendChart from "@/components/charts/TrendChart.vue";
import BarChart from "@/components/charts/BarChart.vue";

const { data, loading } = useAsync(() => financeApi.dashboard(), {
	initial: {
		outstanding_total: 0,
		outstanding_count: 0,
		overdue_total: 0,
		overdue_count: 0,
		collected_this_month: 0,
		pending_scholarships: 0,
		pending_mobile_money: 0,
		by_category: [],
		top_overdue: [],
		monthly_collections: [],
	},
});
</script>
