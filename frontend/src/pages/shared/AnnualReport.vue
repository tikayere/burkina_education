<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else-if="data" class="space-y-6">
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<div>
				<h2 class="text-lg font-semibold text-gray-900">Bulletin annuel — {{ data.academic_year }}</h2>
				<p class="text-sm text-gray-500">{{ data.student_name }}</p>
			</div>
			<div class="flex items-center gap-6">
				<div class="text-right">
					<p class="text-xs uppercase tracking-wide text-gray-400">Moyenne</p>
					<p class="text-xl font-semibold text-gray-900">{{ data.annual_average }}</p>
				</div>
				<div class="text-right">
					<p class="text-xs uppercase tracking-wide text-gray-400">Rang</p>
					<p class="text-xl font-semibold text-gray-900">{{ data.annual_rank ? `${data.annual_rank}/${data.class_size}` : "—" }}</p>
				</div>
				<StatusBadge :text="data.decision" :tone="data.decision === 'Admis' ? 'green' : data.decision === 'Redouble' ? 'red' : 'gray'" />
			</div>
		</div>

		<SectionCard title="Détail par trimestre" no-padding>
			<table class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Trimestre</th>
						<th class="px-5 py-3">Moyenne</th>
						<th class="px-5 py-3">Pondération</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="t in data.terms" :key="t.academic_term">
						<td class="px-5 py-3 font-medium text-gray-800">{{ t.academic_term }}</td>
						<td class="px-5 py-3">{{ t.term_average }}</td>
						<td class="px-5 py-3 text-gray-500">{{ t.weight }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<SectionCard title="Appréciation de la direction">
			<p class="text-sm text-gray-700">{{ data.principal_comment || "—" }}</p>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" }, name: { type: String, required: true } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.annualReport({ name: props.name }), { watchSource: () => [props.student, props.name] });
</script>
