<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<SectionCard v-else title="Dossier disciplinaire" no-padding>
		<EmptyState v-if="!data.length" icon="shield" title="Aucun incident enregistré" description="Aucune sanction ni signalement à ce jour." />
		<ul v-else class="divide-y divide-gray-100">
			<li v-for="c in data" :key="c.name" class="p-5">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<StatusBadge :text="c.incident_type" tone="gray" />
						<StatusBadge :text="c.severity" :tone="c.severity === 'Grave' ? 'red' : c.severity === 'Modérée' ? 'gold' : 'gray'" />
					</div>
					<div class="flex items-center gap-2">
						<span class="text-xs text-gray-400">{{ formatDate(c.date) }}</span>
						<StatusBadge :text="c.status" :tone="c.status === 'Résolu' ? 'green' : 'red'" />
					</div>
				</div>
				<p class="mt-2 text-sm text-gray-700">{{ c.description }}</p>
				<p v-if="c.action_taken" class="mt-1 text-sm text-gray-500"><span class="font-medium">Mesure :</span> {{ c.action_taken }}</p>
				<p v-if="c.resolution" class="mt-1 text-sm text-gray-500"><span class="font-medium">Résolution :</span> {{ c.resolution }}</p>
			</li>
		</ul>
	</SectionCard>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.discipline(), { watchSource: () => props.student, initial: [] });
</script>
