<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Brouillons" :value="data.drafts.length" icon="edit-2" tone="gray" />
			<StatCard label="Publiées" :value="data.published.length" icon="bell" tone="green" />
			<StatCard label="Envoyés aujourd'hui" :value="data.sent_today" icon="send" tone="gray" />
			<StatCard label="Échecs aujourd'hui" :value="data.failed_today" icon="alert-triangle" :tone="data.failed_today ? 'red' : 'gray'" />
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
import { LoadingIndicator } from "frappe-ui";
import { commsApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const { data, loading } = useAsync(() => commsApi.dashboard(), {
	initial: { drafts: [], published: [], sent_today: 0, failed_today: 0, templates: 0 },
});
</script>
