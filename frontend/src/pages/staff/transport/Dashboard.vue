<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
			<StatCard label="Itinéraires" :value="data.routes_count" icon="map" tone="gray" />
			<StatCard label="Élèves affectés" :value="data.active_assignments" icon="users" tone="gold" />
			<StatCard label="Sans arrêt défini" :value="data.unassigned_stop" icon="alert-triangle" :tone="data.unassigned_stop ? 'red' : 'gray'" />
		</div>

		<SectionCard v-if="routesChart.length" title="Élèves par itinéraire">
			<BarChart :data="routesChart" />
		</SectionCard>

		<SectionCard title="Occupation par itinéraire" no-padding>
			<EmptyState v-if="!data.routes.length" icon="map" title="Aucun itinéraire" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Itinéraire</th>
						<th class="px-5 py-3">Véhicule</th>
						<th class="px-5 py-3">Chauffeur</th>
						<th class="px-5 py-3">Arrêts</th>
						<th class="px-5 py-3">Élèves</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="r in data.routes" :key="r.name" class="cursor-pointer hover:bg-gray-50" @click="$router.push({ name: 'transport-assignments', query: { route: r.name } })">
						<td class="px-5 py-3 font-medium text-gray-800">{{ r.route_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ r.vehicle || "—" }}</td>
						<td class="px-5 py-3 text-gray-500">{{ r.driver_name || "—" }}</td>
						<td class="px-5 py-3">{{ r.stop_count }}</td>
						<td class="px-5 py-3">{{ r.student_count }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { transportApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import BarChart from "@/components/charts/BarChart.vue";

const { data, loading } = useAsync(() => transportApi.dashboard(), {
	initial: { routes: [], routes_count: 0, active_assignments: 0, unassigned_stop: 0 },
});

const routesChart = computed(() =>
	data.value.routes.filter((r) => r.student_count > 0).map((r) => ({ label: r.route_name, value: r.student_count })),
);
</script>
