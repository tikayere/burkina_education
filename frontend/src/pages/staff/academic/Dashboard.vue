<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<div v-if="data.structure" class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Campus" :value="data.structure.campuses" icon="map-pin" tone="gray" />
			<StatCard label="Cycles" :value="data.structure.cycles" icon="repeat" tone="gray" />
			<StatCard label="Niveaux" :value="data.structure.education_levels" icon="layers" tone="gray" />
			<StatCard label="Classes" :value="data.structure.grades" icon="grid" tone="gray" />
		</div>

		<template v-if="data.admissions">
			<div class="grid grid-cols-2 gap-4 sm:grid-cols-5">
				<StatCard label="Candidatures soumises" :value="data.admissions.submitted" icon="inbox" tone="gray" />
				<StatCard label="En cours d'examen" :value="data.admissions.under_review" icon="search" tone="gold" />
				<StatCard label="Prêtes à enrôler" :value="data.admissions.ready_to_enroll" icon="check-circle" :tone="data.admissions.ready_to_enroll ? 'green' : 'gray'" />
				<StatCard label="Liste d'attente" :value="data.admissions.waitlisted" icon="clock" tone="gray" />
				<StatCard label="Inscrits cette année" :value="data.admissions.enrolled_this_year" icon="user-check" tone="green" />
			</div>

			<SectionCard title="Pipeline des admissions">
				<BarChart :data="admissionsFunnel" :height="150" />
			</SectionCard>
		</template>

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

		<!-- Department Head (no "director" section) - the same three counts,
		     scoped to just what Pédagogie covers. -->
		<div v-else-if="data.pedagogy" class="grid grid-cols-3 gap-4">
			<StatCard label="Curriculums" :value="data.pedagogy.curriculum_count" icon="book" tone="gray" />
			<StatCard label="Compétences" :value="data.pedagogy.competency_count" icon="target" tone="gray" />
			<StatCard label="Leçons planifiées" :value="data.pedagogy.lesson_count" icon="edit-2" tone="gray" />
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { academicApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import BarChart from "@/components/charts/BarChart.vue";

const { data, loading } = useAsync(() => academicApi.dashboard(), { initial: {} });

// Same five counts as the stat cards above, as a funnel bar chart -
// Application -> Review -> Acceptance -> Admission -> Enrollment
// (docs/architecture.md section O) reads more clearly as a shape than as
// four separate numbers.
const admissionsFunnel = computed(() => {
	const a = data.value.admissions || {};
	return [
		{ label: "Soumises", value: a.submitted || 0 },
		{ label: "En examen", value: a.under_review || 0 },
		{ label: "Liste d'attente", value: a.waitlisted || 0 },
		{ label: "Prêtes", value: a.ready_to_enroll || 0 },
		{ label: "Inscrites", value: a.enrolled_this_year || 0 },
	];
});
</script>
