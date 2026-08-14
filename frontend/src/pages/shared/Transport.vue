<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<EmptyState v-else-if="!data.assignment" icon="truck" title="Aucune affectation de transport" />
	<div v-else class="space-y-6">
		<div class="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-lg font-semibold text-gray-900">{{ data.assignment.route_detail?.route_name }}</h2>
					<p class="text-sm text-gray-500">Arrêt : {{ data.assignment.stop_name }}</p>
				</div>
				<StatusBadge text="Actif" tone="green" />
			</div>
			<dl class="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
				<div><dt class="text-gray-400">Véhicule</dt><dd class="font-medium text-gray-800">{{ data.assignment.route_detail?.vehicle || "—" }}</dd></div>
				<div><dt class="text-gray-400">Chauffeur</dt><dd class="font-medium text-gray-800">{{ data.assignment.route_detail?.driver_name || "—" }}</dd></div>
				<div><dt class="text-gray-400">Distance</dt><dd class="font-medium text-gray-800">{{ data.assignment.route_detail?.distance_km || "—" }} km</dd></div>
				<div><dt class="text-gray-400">Depuis le</dt><dd class="font-medium text-gray-800">{{ formatDate(data.assignment.start_date) }}</dd></div>
			</dl>
		</div>

		<SectionCard title="Arrêts de l'itinéraire" no-padding>
			<table class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">#</th>
						<th class="px-5 py-3">Arrêt</th>
						<th class="px-5 py-3">Ramassage</th>
						<th class="px-5 py-3">Dépose</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="s in data.assignment.route_detail?.stops || []" :key="s.sequence" :class="{ 'bg-bf-green-50': s.stop_name === data.assignment.stop_name }">
						<td class="px-5 py-3">{{ s.sequence }}</td>
						<td class="px-5 py-3 font-medium text-gray-800">{{ s.stop_name }}</td>
						<td class="px-5 py-3">{{ formatTime(s.pickup_time) }}</td>
						<td class="px-5 py-3">{{ formatTime(s.drop_time) }}</td>
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
import { formatDate, formatTime } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.transport(), { watchSource: () => props.student, initial: { assignment: null } });
</script>
