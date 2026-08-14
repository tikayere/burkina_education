<template>
	<div v-if="error" class="rounded-lg bg-bf-red-50 p-4 text-sm text-bf-red-600">{{ error }}</div>
	<div v-else class="space-y-6">
		<div class="flex justify-end">
			<Button variant="solid" theme="green" @click="openDialog">Nouveau signalement</Button>
		</div>

		<div v-if="loading" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
		</div>
		<SectionCard v-else title="Dossiers disciplinaires" no-padding>
			<EmptyState v-if="!data.length" icon="shield" title="Aucun dossier" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Élève</th>
						<th class="px-5 py-3">Type</th>
						<th class="px-5 py-3">Gravité</th>
						<th class="px-5 py-3">Date</th>
						<th class="px-5 py-3">Statut</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="c in data" :key="c.name">
						<td class="px-5 py-3 font-medium text-gray-800">{{ c.student_name }}</td>
						<td class="px-5 py-3">{{ c.incident_type }}</td>
						<td class="px-5 py-3"><StatusBadge :text="c.severity" :tone="c.severity === 'Grave' ? 'red' : c.severity === 'Modérée' ? 'gold' : 'gray'" /></td>
						<td class="px-5 py-3">{{ formatDate(c.date) }}</td>
						<td class="px-5 py-3"><StatusBadge :text="c.status" :tone="c.status === 'Résolu' ? 'green' : 'red'" /></td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<Dialog v-model="dialogOpen" :options="{ title: 'Nouveau signalement disciplinaire' }">
			<template #body-content>
				<div class="space-y-4">
					<FormControl type="select" label="Classe" v-model="form.student_group" :options="groupOptions" @update:modelValue="onGroupChange" />
					<FormControl type="select" label="Élève" v-model="form.student" :options="studentOptions" />
					<FormControl
						type="select"
						label="Type d'incident"
						v-model="form.incident_type"
						:options="['Comportement', 'Retard', 'Absence non justifiée', 'Violence', 'Vol', 'Fraude aux examens', 'Dégradation de matériel', 'Autre']"
					/>
					<FormControl type="select" label="Gravité" v-model="form.severity" :options="['Mineure', 'Modérée', 'Grave']" />
					<FormControl type="textarea" label="Description" v-model="form.description" />
					<FormControl type="textarea" label="Mesure prise (optionnel)" v-model="form.action_taken" />
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="green" class="w-full" :loading="creating" @click="submitCase">Enregistrer</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Button, Dialog, FormControl, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const { data, loading, error, reload } = useAsync(() => teacherApi.disciplineCases(), { initial: [] });

const dialogOpen = ref(false);
const creating = ref(false);
const groups = ref([]);
const students = ref([]);
const form = reactive({ student_group: "", student: "", incident_type: "Comportement", severity: "Mineure", description: "", action_taken: "" });

const groupOptions = computed(() => [{ label: "Sélectionner une classe...", value: "" }, ...groups.value.map((g) => ({ label: g.student_group_name, value: g.name }))]);
const studentOptions = computed(() => [{ label: "Sélectionner un élève...", value: "" }, ...students.value.map((s) => ({ label: s.student_name, value: s.student }))]);

async function openDialog() {
	dialogOpen.value = true;
	if (!groups.value.length) groups.value = await teacherApi.groups();
}

async function onGroupChange(value) {
	form.student = "";
	students.value = value ? await teacherApi.groupStudents({ student_group: value }) : [];
}

async function submitCase() {
	if (!form.student || !form.description) {
		notifyError(null, "Veuillez choisir un élève et décrire l'incident.");
		return;
	}
	creating.value = true;
	try {
		await teacherApi.createDisciplineCase({
			student: form.student,
			incident_type: form.incident_type,
			severity: form.severity,
			description: form.description,
			action_taken: form.action_taken,
		});
		notifySuccess("Signalement enregistré.");
		dialogOpen.value = false;
		Object.assign(form, { student_group: "", student: "", incident_type: "Comportement", severity: "Mineure", description: "", action_taken: "" });
		reload();
	} catch (e) {
		notifyError(e);
	} finally {
		creating.value = false;
	}
}
</script>
