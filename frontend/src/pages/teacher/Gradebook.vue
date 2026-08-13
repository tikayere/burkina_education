<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<SectionCard v-else title="Évaluations" no-padding>
		<EmptyState v-if="!data.length" icon="award" title="Aucune évaluation planifiée" />
		<table v-else class="w-full text-sm">
			<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
				<tr>
					<th class="px-5 py-3">Évaluation</th>
					<th class="px-5 py-3">Classe</th>
					<th class="px-5 py-3">Matière</th>
					<th class="px-5 py-3">Date</th>
					<th class="px-5 py-3">Barème</th>
					<th class="px-5 py-3"></th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-100">
				<tr v-for="p in data" :key="p.name" class="hover:bg-gray-50">
					<td class="px-5 py-3 font-medium text-gray-800">{{ p.assessment_name }}</td>
					<td class="px-5 py-3">{{ p.student_group }}</td>
					<td class="px-5 py-3">{{ p.course }}</td>
					<td class="px-5 py-3">{{ formatDate(p.schedule_date) }}</td>
					<td class="px-5 py-3">/ {{ p.maximum_assessment_score }}</td>
					<td class="px-5 py-3 text-right">
						<router-link :to="{ name: 'teacher-gradebook-plan', params: { plan: p.name } }" class="text-bf-red-600 hover:underline">
							Saisir les notes
						</router-link>
					</td>
				</tr>
			</tbody>
		</table>
	</SectionCard>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const { data, loading } = useAsync(() => teacherApi.assessmentPlans(), { initial: [] });
</script>
