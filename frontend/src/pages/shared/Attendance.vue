<template>
	<div class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Taux (30 jours)" :value="`${summary.last_30_days.percentage}%`" icon="check-square" tone="green" />
			<StatCard label="Taux (année)" :value="`${summary.this_year.percentage}%`" icon="calendar" tone="gold" />
			<StatCard label="Absences (30j)" :value="summary.last_30_days.absent" icon="x-circle" tone="red" />
			<StatCard label="Retards (30j)" :value="summary.last_30_days.late" icon="clock" tone="gray" />
		</div>

		<SectionCard title="Historique">
			<template #actions>
				<input v-model="fromDate" type="date" class="rounded-md border-gray-300 text-sm" @change="reload" />
				<span class="text-sm text-gray-400">→</span>
				<input v-model="toDate" type="date" class="rounded-md border-gray-300 text-sm" @change="reload" />
			</template>
			<div v-if="loading" class="flex justify-center py-10">
				<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
			</div>
			<EmptyState v-else-if="!records.length" icon="calendar" title="Aucun enregistrement sur cette période" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="py-2">Date</th>
						<th class="py-2">Statut</th>
						<th class="py-2">Remarques</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="r in records" :key="r.name">
						<td class="py-2">{{ formatDate(r.date) }}</td>
						<td class="py-2"><StatusBadge :text="statusLabel(r.status)" :tone="statusTone(r.status)" /></td>
						<td class="py-2 text-gray-500">{{ r.remarks || "—" }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));

const today = new Date().toISOString().slice(0, 10);
const ninetyDaysAgo = new Date(Date.now() - 90 * 86400000).toISOString().slice(0, 10);
const fromDate = ref(ninetyDaysAgo);
const toDate = ref(today);

const { data, loading, reload } = useAsync(
	() => api.value.attendance({ from_date: fromDate.value, to_date: toDate.value }),
	{
		watchSource: () => props.student,
		initial: { summary: { last_30_days: {}, this_year: {} }, records: [] },
	},
);

const summary = computed(() => data.value.summary);
const records = computed(() => data.value.records);

const LABELS = { Present: "Présent", Absent: "Absent", Late: "Retard", Excused: "Excusé", Leave: "Congé" };
const TONES = { Present: "green", Absent: "red", Late: "gold", Excused: "blue", Leave: "gray" };
function statusLabel(s) {
	return LABELS[s] || s;
}
function statusTone(s) {
	return TONES[s] || "gray";
}
</script>
