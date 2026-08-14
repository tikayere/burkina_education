<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Visites aujourd'hui" :value="data.visits_today" icon="activity" tone="gray" />
			<StatCard label="Dossiers ouverts" :value="data.open_cases" icon="alert-circle" :tone="data.open_cases ? 'gold' : 'gray'" />
			<StatCard label="Suivi requis" :value="data.follow_up" icon="alert-triangle" :tone="data.follow_up ? 'red' : 'gray'" />
			<StatCard label="Parents non informés" :value="data.not_notified" icon="bell" :tone="data.not_notified ? 'red' : 'gray'" />
		</div>

		<SectionCard v-if="statusBreakdown.length" title="Visites récentes par statut">
			<DonutChart :data="statusBreakdown" />
		</SectionCard>

		<SectionCard title="Visites récentes" no-padding>
			<EmptyState v-if="!data.recent.length" icon="activity" title="Aucune visite enregistrée" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Élève</th>
						<th class="px-5 py-3">Date</th>
						<th class="px-5 py-3">Motif</th>
						<th class="px-5 py-3">Statut</th>
						<th class="px-5 py-3">Parent informé</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="v in data.recent" :key="v.name" class="cursor-pointer hover:bg-gray-50" @click="$router.push({ name: 'clinic-visits' })">
						<td class="px-5 py-3 font-medium text-gray-800">{{ v.student_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ formatDateTime(v.date) }}</td>
						<td class="px-5 py-3 text-gray-500">{{ v.complaint }}</td>
						<td class="px-5 py-3"><StatusBadge :text="v.status" :tone="v.status === 'Clos' ? 'green' : v.status === 'Suivi requis' ? 'red' : 'gold'" /></td>
						<td class="px-5 py-3">
							<FeatherIcon :name="v.parent_notified ? 'check-circle' : 'circle'" class="h-4 w-4" :class="v.parent_notified ? 'text-bf-green-500' : 'text-gray-300'" />
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon, LoadingIndicator } from "frappe-ui";
import { clinicApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDateTime } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import DonutChart from "@/components/charts/DonutChart.vue";

const { data, loading } = useAsync(() => clinicApi.dashboard(), {
	initial: { visits_today: 0, open_cases: 0, follow_up: 0, not_notified: 0, recent: [] },
});

// Same tone mapping as the table's own StatusBadge below, just recomputed as
// chart colors - client-side tally over the already-fetched `recent` list
// (no new backend query, same data the table already shows).
const STATUS_COLOR = { Clos: "#1baf7a", "Suivi requis": "#e34948" };
const statusBreakdown = computed(() => {
	const counts = {};
	for (const v of data.value.recent) counts[v.status] = (counts[v.status] || 0) + 1;
	return Object.entries(counts).map(([label, value]) => ({ label, value, color: STATUS_COLOR[label] || "#eda100" }));
});
</script>
