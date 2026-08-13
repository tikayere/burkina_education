<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<SectionCard v-else title="Emploi du temps (14 prochains jours)" no-padding>
		<EmptyState v-if="!data.length" icon="calendar" title="Aucun cours planifié" />
		<ul v-else class="divide-y divide-gray-100">
			<li v-for="s in data" :key="s.name" class="flex items-center justify-between px-5 py-3">
				<div>
					<p class="text-sm font-medium text-gray-800">{{ s.course }}</p>
					<p class="text-xs text-gray-500">{{ s.student_group }} · Salle {{ s.room || "—" }}</p>
				</div>
				<div class="text-right text-sm text-gray-500">
					<p>{{ formatDate(s.schedule_date) }}</p>
					<p>{{ formatTime(s.from_time) }} - {{ formatTime(s.to_time) }}</p>
				</div>
			</li>
		</ul>
	</SectionCard>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate, formatTime } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const { data, loading } = useAsync(() => teacherApi.schedule(), { initial: [] });
</script>
