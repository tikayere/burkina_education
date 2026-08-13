<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<EmptyState v-else-if="!data.assignment" icon="moon" title="Aucun logement à l'internat" />
	<div v-else class="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
		<div class="flex items-center justify-between">
			<div>
				<h2 class="text-lg font-semibold text-gray-900">{{ data.assignment.building_name }}</h2>
				<p class="text-sm text-gray-500">
					Chambre {{ data.assignment.room?.room_number }} ({{ data.assignment.room?.floor || "—" }}) · Lit {{ data.assignment.bed_number }}
				</p>
			</div>
			<StatusBadge text="Actif" tone="green" />
		</div>
		<dl class="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
			<div><dt class="text-gray-400">Surveillant</dt><dd class="font-medium text-gray-800">{{ data.assignment.supervisor_name || "—" }}</dd></div>
			<div><dt class="text-gray-400">Entrée</dt><dd class="font-medium text-gray-800">{{ formatDate(data.assignment.check_in_date) }}</dd></div>
			<div><dt class="text-gray-400">Sortie prévue</dt><dd class="font-medium text-gray-800">{{ data.assignment.check_out_date ? formatDate(data.assignment.check_out_date) : "—" }}</dd></div>
		</dl>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.boarding(), { watchSource: () => props.student, initial: { assignment: null } });
</script>
