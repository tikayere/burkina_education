<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Brouillons" :value="data.drafts.length" icon="edit-2" tone="gray" />
			<StatCard label="Publiées" :value="data.published.length" icon="bell" tone="green" />
			<StatCard label="Envoyés aujourd'hui" :value="data.sent_today" icon="send" tone="gray" />
			<StatCard label="Échecs aujourd'hui" :value="data.failed_today" icon="alert-triangle" :tone="data.failed_today ? 'red' : 'gray'" />
		</div>

		<div v-if="messagesBreakdown.length || draftsByPriority.length" class="grid gap-6 lg:grid-cols-2">
			<SectionCard v-if="messagesBreakdown.length" title="Messages envoyés aujourd'hui">
				<DonutChart :data="messagesBreakdown" />
			</SectionCard>
			<SectionCard v-if="draftsByPriority.length" title="Brouillons par priorité">
				<BarChart :data="draftsByPriority" />
			</SectionCard>
		</div>

		<SectionCard title="Annonces en brouillon" no-padding>
			<EmptyState v-if="!data.drafts.length" icon="edit-2" title="Aucun brouillon" />
			<table v-else class="w-full text-sm">
				<tbody class="divide-y divide-gray-100">
					<tr v-for="a in data.drafts" :key="a.name" class="cursor-pointer hover:bg-gray-50" @click="$router.push({ name: 'comms-announcements' })">
						<td class="px-5 py-3 font-medium text-gray-800">{{ a.title }}</td>
						<td class="px-5 py-3 text-gray-500">{{ a.audience_type }}</td>
						<td class="px-5 py-3 text-right"><StatusBadge :text="a.priority" :tone="a.priority === 'Urgente' ? 'red' : a.priority === 'Élevée' ? 'gold' : 'gray'" /></td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { commsApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import DonutChart from "@/components/charts/DonutChart.vue";
import BarChart from "@/components/charts/BarChart.vue";

const { data, loading } = useAsync(() => commsApi.dashboard(), {
	initial: { drafts: [], published: [], sent_today: 0, failed_today: 0, templates: 0 },
});

const messagesBreakdown = computed(() =>
	[
		{ label: "Envoyés", value: data.value.sent_today, color: "#1baf7a" },
		{ label: "Échecs", value: data.value.failed_today, color: "#e34948" },
	].filter((p) => p.value > 0),
);

// Client-side tally over the drafts list this page already fetches - same
// priority tones as the table's StatusBadge above (Urgente=red, Élevée=gold).
const PRIORITY_COLOR = { Urgente: "#e34948", Élevée: "#eda100" };
const draftsByPriority = computed(() => {
	const counts = {};
	for (const a of data.value.drafts) counts[a.priority] = (counts[a.priority] || 0) + 1;
	return Object.entries(counts).map(([label, value]) => ({ label, value, color: PRIORITY_COLOR[label] || "#9ca3af" }));
});
</script>
