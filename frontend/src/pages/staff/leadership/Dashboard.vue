<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
			<StatCard label="Campus" :value="data.school.campuses" icon="map-pin" tone="gray" />
			<StatCard label="Dossiers disciplinaires ouverts" :value="data.school.open_discipline_cases" icon="shield" :tone="data.school.open_discipline_cases ? 'red' : 'gray'" />
			<StatCard label="Bourses en attente" :value="data.school.pending_scholarships" icon="award" tone="gold" />
		</div>

		<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
			<StatCard label="Occupation internat" :value="`${data.boarding.occupied} / ${data.boarding.beds}`" icon="moon" tone="gray" />
			<StatCard label="Abonnés cantine" :value="data.canteen.active_subscriptions" icon="coffee" tone="gray" />
			<StatCard label="Élèves transportés" :value="data.transport.active_assignments" icon="truck" tone="gray" />
			<StatCard label="Dossiers infirmerie ouverts" :value="data.clinic.open_cases" icon="activity" :tone="data.clinic.open_cases ? 'gold' : 'gray'" />
		</div>

		<SectionCard title="Discipline - dossiers ouverts" no-padding>
			<EmptyState v-if="!data.recent_discipline.length" icon="check-circle" title="Aucun dossier ouvert" />
			<table v-else class="w-full text-sm">
				<tbody class="divide-y divide-gray-100">
					<tr v-for="c in data.recent_discipline" :key="c.name" class="cursor-pointer hover:bg-gray-50" @click="$router.push({ name: 'leadership-discipline' })">
						<td class="px-5 py-3 font-medium text-gray-800">{{ c.student_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ c.incident_type }}</td>
						<td class="px-5 py-3"><StatusBadge :text="c.severity" :tone="c.severity === 'Grave' ? 'red' : c.severity === 'Modérée' ? 'gold' : 'gray'" /></td>
						<td class="px-5 py-3 text-right text-gray-500">{{ formatDate(c.date) }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";
import { leadershipApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const { data, loading } = useAsync(() => leadershipApi.dashboard(), {
	initial: {
		school: { campuses: 0, open_discipline_cases: 0, pending_scholarships: 0 },
		boarding: { beds: 0, occupied: 0 },
		canteen: { active_subscriptions: 0 },
		transport: { active_routes: 0, active_assignments: 0 },
		clinic: { open_cases: 0 },
		comms: { published_announcements: 0 },
		recent_discipline: [],
	},
});
</script>
