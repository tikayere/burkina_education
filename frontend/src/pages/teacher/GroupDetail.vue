<template>
	<div class="space-y-6">
		<div class="flex items-center justify-between">
			<p class="text-sm text-gray-500">{{ students.length }} élève(s)</p>
			<Button variant="solid" theme="green" @click="$router.push({ name: 'teacher-attendance', params: { group } })">
				Faire l'appel
			</Button>
		</div>

		<div v-if="loading" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
		</div>
		<SectionCard v-else title="Liste des élèves" no-padding>
			<EmptyState v-if="!students.length" icon="users" title="Aucun élève dans cette classe" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">#</th>
						<th class="px-5 py-3">Élève</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="s in students" :key="s.student">
						<td class="px-5 py-3 text-gray-500">{{ s.group_roll_number || "—" }}</td>
						<td class="px-5 py-3 font-medium text-gray-800">{{ s.student_name }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { Button, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({ group: { type: String, required: true } });
const { data: students, loading } = useAsync(() => teacherApi.groupStudents({ student_group: props.group }), {
	watchSource: () => props.group,
	initial: [],
});
</script>
