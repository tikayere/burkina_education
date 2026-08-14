<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<SectionCard title="Bulletins trimestriels" no-padding>
			<EmptyState v-if="!data.term_reports.length" icon="award" title="Aucun bulletin trimestriel publié" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Période</th>
						<th class="px-5 py-3">Moyenne</th>
						<th class="px-5 py-3">Rang</th>
						<th class="px-5 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="r in data.term_reports" :key="r.name" class="hover:bg-gray-50">
						<td class="px-5 py-3 font-medium text-gray-800">{{ r.academic_term }}</td>
						<td class="px-5 py-3">{{ r.term_average }} / {{ r.max_average }}</td>
						<td class="px-5 py-3">{{ r.class_rank ? `${r.class_rank} / ${r.class_size}` : "—" }}</td>
						<td class="px-5 py-3 text-right">
							<router-link :to="bulletinRoute(r.name)" class="text-bf-green-600 hover:underline">Voir</router-link>
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<SectionCard title="Bulletins annuels" no-padding>
			<EmptyState v-if="!data.annual_reports.length" icon="award" title="Aucun bulletin annuel publié" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Année</th>
						<th class="px-5 py-3">Moyenne</th>
						<th class="px-5 py-3">Rang</th>
						<th class="px-5 py-3">Décision</th>
						<th class="px-5 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="r in data.annual_reports" :key="r.name" class="hover:bg-gray-50">
						<td class="px-5 py-3 font-medium text-gray-800">{{ r.academic_year }}</td>
						<td class="px-5 py-3">{{ r.annual_average }}</td>
						<td class="px-5 py-3">{{ r.annual_rank ? `${r.annual_rank} / ${r.class_size}` : "—" }}</td>
						<td class="px-5 py-3">
							<StatusBadge :text="r.decision" :tone="r.decision === 'Admis' ? 'green' : r.decision === 'Redouble' ? 'red' : 'gray'" />
						</td>
						<td class="px-5 py-3 text-right">
							<router-link :to="annualRoute(r.name)" class="text-bf-green-600 hover:underline">Voir</router-link>
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
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.grades(), { watchSource: () => props.student, initial: { term_reports: [], annual_reports: [] } });

function bulletinRoute(name) {
	return props.student
		? { name: "child-bulletin", params: { student: props.student, name } }
		: { name: "student-bulletin", params: { name } };
}
function annualRoute(name) {
	return props.student
		? { name: "child-bulletin-annuel", params: { student: props.student, name } }
		: { name: "student-bulletin-annuel", params: { name } };
}
</script>
