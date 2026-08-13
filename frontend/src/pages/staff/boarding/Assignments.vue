<template>
	<div class="space-y-4">
		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
		</div>
		<SectionCard v-else title="Affectations internat" no-padding>
			<EmptyState v-if="!list.data?.length" icon="moon" title="Aucune affectation" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Élève</th>
						<th class="px-5 py-3">Lit</th>
						<th class="px-5 py-3">Surveillant</th>
						<th class="px-5 py-3">Entrée</th>
						<th class="px-5 py-3">Statut</th>
						<th class="px-5 py-3 text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="a in list.data" :key="a.name">
						<td class="px-5 py-3 font-medium text-gray-800">{{ a.student_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ a.bed }}</td>
						<td class="px-5 py-3 text-gray-500">{{ a.supervisor || "—" }}</td>
						<td class="px-5 py-3">{{ formatDate(a.check_in_date) }}</td>
						<td class="px-5 py-3"><StatusBadge :text="a.status" :tone="a.status === 'Actif' ? 'green' : 'gray'" /></td>
						<td class="px-5 py-3 text-right">
							<Button v-if="a.status === 'Actif'" size="sm" variant="outline" :loading="acting === a.name" @click="checkOut(a)">
								Départ
							</Button>
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Button, LoadingIndicator, createListResource } from "frappe-ui";
import { runDocMethod } from "@/api";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const acting = ref("");

const list = createListResource({
	doctype: "Student Boarding Assignment",
	fields: ["name", "student_name", "bed", "supervisor", "check_in_date", "check_out_date", "status"],
	orderBy: "status asc, check_in_date desc",
	pageLength: 100,
	auto: true,
	onError: (e) => notifyError(e),
});

async function checkOut(assignment) {
	acting.value = assignment.name;
	try {
		await runDocMethod("Student Boarding Assignment", assignment.name, "check_out");
		notifySuccess(`${assignment.student_name} a quitté l'internat.`);
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		acting.value = "";
	}
}
</script>
