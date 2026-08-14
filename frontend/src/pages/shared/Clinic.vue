<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<SectionCard v-else title="Infirmerie" subtitle="Visible uniquement par vous - non partagé avec les enseignants." no-padding>
		<EmptyState v-if="!data.length" icon="heart" title="Aucune visite à l'infirmerie enregistrée" />
		<ul v-else class="divide-y divide-gray-100">
			<li v-for="v in data" :key="v.name" class="p-5">
				<div class="flex items-center justify-between">
					<p class="text-sm font-medium text-gray-800">{{ v.complaint }}</p>
					<div class="flex items-center gap-2">
						<span class="text-xs text-gray-400">{{ formatDateTime(v.date) }}</span>
						<StatusBadge :text="v.status" :tone="v.status === 'Clos' ? 'green' : 'gold'" />
					</div>
				</div>
				<p v-if="v.treatment" class="mt-1 text-sm text-gray-500"><span class="font-medium">Traitement :</span> {{ v.treatment }}</p>
				<p v-if="v.referral && v.referral !== 'Aucun'" class="mt-1 text-sm text-gray-500">
					<span class="font-medium">Orientation :</span> {{ v.referral }}
				</p>
				<p v-if="v.follow_up" class="mt-1 text-sm text-gray-500"><span class="font-medium">Suivi :</span> {{ v.follow_up }}</p>
			</li>
		</ul>
	</SectionCard>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDateTime } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

// Guardian-only (never routed to for the Student Portal itself - see
// router.js, no "student-clinic" route exists) - docs/architecture.md
// section L on why health data stops at the guardian.
const props = defineProps({ student: { type: String, required: true } });
const api = computed(() => childApi(props.student));
const { data, loading } = useAsync(() => api.value.clinic(), { watchSource: () => props.student, initial: [] });
</script>
