<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else-if="data" class="space-y-6">
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<div>
				<h2 class="text-lg font-semibold text-gray-900">Bulletin — {{ data.academic_term }}</h2>
				<p class="text-sm text-gray-500">{{ data.student_name }} · {{ data.academic_year }}</p>
			</div>
			<div class="flex gap-6 text-right">
				<div>
					<p class="text-xs uppercase tracking-wide text-gray-400">Moyenne</p>
					<p class="text-xl font-semibold text-gray-900">{{ data.term_average }} / {{ data.max_average }}</p>
				</div>
				<div>
					<p class="text-xs uppercase tracking-wide text-gray-400">Rang</p>
					<p class="text-xl font-semibold text-gray-900">{{ data.class_rank ? `${data.class_rank}/${data.class_size}` : "—" }}</p>
				</div>
			</div>
		</div>

		<SectionCard title="Matières" no-padding>
			<table class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Matière</th>
						<th class="px-5 py-3">Coefficient</th>
						<th class="px-5 py-3">Moyenne</th>
						<th class="px-5 py-3">Évaluations</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="s in data.subjects" :key="s.course">
						<td class="px-5 py-3 font-medium text-gray-800">{{ s.course_name || s.course }}</td>
						<td class="px-5 py-3">{{ s.coefficient }}</td>
						<td class="px-5 py-3">{{ s.subject_average }} / {{ s.max_score }}</td>
						<td class="px-5 py-3 text-gray-500">{{ s.assessment_count }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<div class="grid gap-6 sm:grid-cols-2">
			<SectionCard title="Assiduité">
				<dl class="grid grid-cols-2 gap-4 text-sm">
					<div><dt class="text-gray-400">Présent</dt><dd class="font-medium text-gray-800">{{ data.attendance_present }}</dd></div>
					<div><dt class="text-gray-400">Absent</dt><dd class="font-medium text-gray-800">{{ data.attendance_absent }}</dd></div>
					<div><dt class="text-gray-400">Retard</dt><dd class="font-medium text-gray-800">{{ data.attendance_late }}</dd></div>
					<div><dt class="text-gray-400">Taux</dt><dd class="font-medium text-gray-800">{{ data.attendance_percentage }}%</dd></div>
				</dl>
			</SectionCard>
			<SectionCard title="Appréciations">
				<p class="text-sm text-gray-700"><span class="font-medium">Professeur :</span> {{ data.teacher_comment || "—" }}</p>
				<p class="mt-2 text-sm text-gray-700"><span class="font-medium">Direction :</span> {{ data.principal_comment || "—" }}</p>
			</SectionCard>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";

const props = defineProps({ student: { type: String, default: "" }, name: { type: String, required: true } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.termReport({ name: props.name }), { watchSource: () => [props.student, props.name] });
</script>
