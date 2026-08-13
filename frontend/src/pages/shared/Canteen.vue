<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<EmptyState v-else-if="!data.subscription" icon="coffee" title="Aucun abonnement cantine actif" />
	<div v-else class="space-y-6">
		<div class="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-lg font-semibold text-gray-900">{{ data.subscription.meal_plan_detail?.plan_name }}</h2>
					<p class="text-sm text-gray-500">
						{{ formatDate(data.subscription.start_date) }} → {{ data.subscription.end_date ? formatDate(data.subscription.end_date) : "en cours" }}
					</p>
				</div>
				<StatusBadge text="Actif" tone="green" />
			</div>
			<p class="mt-3 text-sm text-gray-600">
				Tarif mensuel : <span class="font-medium">{{ formatCurrency(data.subscription.meal_plan_detail?.price_per_month) }}</span>
			</p>
		</div>

		<SectionCard title="Repas récents" no-padding>
			<EmptyState v-if="!data.recent_consumption.length" icon="coffee" title="Aucun repas enregistré" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Date</th>
						<th class="px-5 py-3">Repas</th>
						<th class="px-5 py-3">Consommé</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="(c, i) in data.recent_consumption" :key="i">
						<td class="px-5 py-3">{{ formatDate(c.date) }}</td>
						<td class="px-5 py-3 font-medium text-gray-800">{{ c.meal_type }}</td>
						<td class="px-5 py-3"><StatusBadge :text="c.consumed ? 'Oui' : 'Non'" :tone="c.consumed ? 'green' : 'gray'" /></td>
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
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.canteen(), {
	watchSource: () => props.student,
	initial: { subscription: null, recent_consumption: [] },
});
</script>
