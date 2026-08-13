<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<div v-if="data.structure" class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Campus" :value="data.structure.campuses" icon="map-pin" tone="gray" />
			<StatCard label="Cycles" :value="data.structure.cycles" icon="repeat" tone="gray" />
			<StatCard label="Niveaux" :value="data.structure.education_levels" icon="layers" tone="gray" />
			<StatCard label="Classes" :value="data.structure.grades" icon="grid" tone="gray" />
		</div>

		<div v-if="data.exams" class="grid gap-6 lg:grid-cols-2">
			<SectionCard title="Examens à venir" no-padding>
				<EmptyState v-if="!data.exams.upcoming.length" icon="clipboard" title="Aucun examen programmé" />
				<table v-else class="w-full text-sm">
					<tbody class="divide-y divide-gray-100">
						<tr v-for="e in data.exams.upcoming" :key="e.name">
							<td class="px-5 py-3 font-medium text-gray-800">{{ e.examination_name }}</td>
							<td class="px-5 py-3 text-gray-500">{{ e.exam_type }}</td>
							<td class="px-5 py-3 text-right">{{ formatDate(e.from_date) }} → {{ formatDate(e.to_date) }}</td>
						</tr>
					</tbody>
				</table>
			</SectionCard>
			<div class="flex flex-col justify-center gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
				<StatCard label="Programmations cette semaine" :value="data.exams.schedules_this_week" icon="calendar" tone="gold" />
			</div>
		</div>

		<div v-if="data.director" class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Dossiers disciplinaires ouverts" :value="data.director.open_discipline_cases" icon="shield" :tone="data.director.open_discipline_cases ? 'red' : 'gray'" />
			<StatCard label="Bourses en attente" :value="data.director.pending_scholarships" icon="award" tone="gold" />
			<StatCard label="Annonces publiées" :value="data.director.published_announcements" icon="bell" tone="gray" />
			<StatCard label="Leçons planifiées" :value="data.director.lesson_count" icon="edit-2" tone="gray" />
		</div>
	</div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";
import { academicApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const { data, loading } = useAsync(() => academicApi.dashboard(), { initial: {} });
</script>
