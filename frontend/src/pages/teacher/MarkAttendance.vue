<template>
	<div class="space-y-6">
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
			<div class="flex items-center gap-3">
				<label class="text-sm font-medium text-gray-600">Date</label>
				<input v-model="date" type="date" class="rounded-md border-gray-300 text-sm" @change="load" />
			</div>
			<Button variant="solid" theme="green" :loading="saving" @click="save">Enregistrer l'appel</Button>
		</div>

		<div v-if="loading" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
		</div>
		<SectionCard v-else title="Faire l'appel" no-padding>
			<EmptyState v-if="!roster.length" icon="users" title="Aucun élève dans cette classe" />
			<ul v-else class="divide-y divide-gray-100">
				<li v-for="row in roster" :key="row.student" class="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
					<div>
						<p class="text-sm font-medium text-gray-800">{{ row.student_name }}</p>
						<p class="text-xs text-gray-400">{{ row.group_roll_number ? `#${row.group_roll_number}` : "" }}</p>
					</div>
					<div class="flex flex-wrap gap-1.5">
						<button
							v-for="opt in statusOptions"
							:key="opt.value"
							type="button"
							class="rounded-full border px-3 py-1 text-xs font-medium transition"
							:class="
								row.status === opt.value
									? `${opt.activeClasses} border-transparent`
									: 'border-gray-200 text-gray-500 hover:bg-gray-50'
							"
							@click="row.status = opt.value"
						>
							{{ opt.label }}
						</button>
					</div>
				</li>
			</ul>
		</SectionCard>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Button, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({ group: { type: String, required: true } });

const date = ref(new Date().toISOString().slice(0, 10));
const roster = ref([]);
const loading = ref(true);
const saving = ref(false);

const statusOptions = [
	{ value: "Present", label: "Présent", activeClasses: "bg-bf-green-500 text-white" },
	{ value: "Absent", label: "Absent", activeClasses: "bg-bf-red-500 text-white" },
	{ value: "Late", label: "Retard", activeClasses: "bg-yellow-500 text-white" },
	{ value: "Excused", label: "Excusé", activeClasses: "bg-blue-500 text-white" },
	{ value: "Leave", label: "Congé", activeClasses: "bg-gray-500 text-white" },
];

async function load() {
	loading.value = true;
	try {
		roster.value = await teacherApi.attendanceSheet({ student_group: props.group, date: date.value });
	} catch (e) {
		notifyError(e);
	} finally {
		loading.value = false;
	}
}

async function save() {
	saving.value = true;
	try {
		const records = roster.value.filter((r) => r.status).map((r) => ({ student: r.student, status: r.status, remarks: r.remarks }));
		const result = await teacherApi.markAttendance({ student_group: props.group, date: date.value, records });
		notifySuccess(`Appel enregistré (${result.created} créé(s), ${result.updated} modifié(s), ${result.unchanged} inchangé(s)).`);
		await load();
	} catch (e) {
		notifyError(e);
	} finally {
		saving.value = false;
	}
}

load();
</script>
