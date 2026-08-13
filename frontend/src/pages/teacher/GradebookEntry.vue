<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else-if="sheet" class="space-y-6">
		<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
			<div>
				<h2 class="font-semibold text-gray-900">{{ sheet.plan.assessment_name }}</h2>
				<p class="text-sm text-gray-500">{{ sheet.plan.course }} · sur {{ sheet.plan.maximum_assessment_score }} points</p>
			</div>
			<Button variant="solid" theme="red" :loading="saving" @click="saveAll">Enregistrer les notes</Button>
		</div>

		<SectionCard title="Saisie" no-padding>
			<div class="overflow-x-auto">
				<table class="w-full min-w-[720px] text-sm">
					<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
						<tr>
							<th class="px-5 py-3">Élève</th>
							<th v-for="c in sheet.plan.criteria" :key="c.assessment_criteria" class="px-3 py-3">
								{{ c.assessment_criteria }} <span class="text-gray-300">/{{ c.maximum_score }}</span>
							</th>
							<th class="px-3 py-3">Total</th>
							<th class="px-3 py-3">Commentaire</th>
							<th class="px-3 py-3"></th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="row in rows" :key="row.student">
							<td class="px-5 py-2 font-medium text-gray-800">{{ row.student_name }}</td>
							<td v-for="(d, i) in row.details" :key="i" class="px-3 py-2">
								<input
									type="number"
									class="w-16 rounded-md border-gray-300 text-sm"
									:max="d.maximum_score"
									min="0"
									v-model.number="d.score"
									:disabled="row.submitted"
								/>
							</td>
							<td class="px-3 py-2 font-medium text-gray-800">{{ rowTotal(row) }}</td>
							<td class="px-3 py-2">
								<input
									type="text"
									class="w-32 rounded-md border-gray-300 text-sm"
									v-model="row.comment"
									:disabled="row.submitted"
								/>
							</td>
							<td class="px-3 py-2 text-right">
								<StatusBadge v-if="row.submitted" text="Validé" tone="green" />
								<Button v-else-if="row.result_name" variant="outline" theme="gray" size="sm" @click="submitRow(row)">
									Valider
								</Button>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</SectionCard>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Button, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ plan: { type: String, required: true } });

const sheet = ref(null);
const rows = ref([]);
const loading = ref(true);
const saving = ref(false);

async function load() {
	loading.value = true;
	try {
		sheet.value = await teacherApi.assessmentResultSheet({ assessment_plan: props.plan });
		rows.value = sheet.value.roster.map((r) => ({
			...r,
			details: r.details.length
				? r.details
				: sheet.value.plan.criteria.map((c) => ({ assessment_criteria: c.assessment_criteria, maximum_score: c.maximum_score, score: 0 })),
		}));
	} catch (e) {
		notifyError(e);
	} finally {
		loading.value = false;
	}
}

function rowTotal(row) {
	return row.details.reduce((sum, d) => sum + (Number(d.score) || 0), 0);
}

async function saveAll() {
	saving.value = true;
	try {
		const results = rows.value
			.filter((r) => !r.submitted)
			.map((r) => ({
				student: r.student,
				comment: r.comment,
				details: r.details.map((d) => ({ assessment_criteria: d.assessment_criteria, maximum_score: d.maximum_score, score: d.score })),
			}));
		await teacherApi.saveAssessmentResults({ assessment_plan: props.plan, results });
		notifySuccess("Notes enregistrées (brouillon).");
		await load();
	} catch (e) {
		notifyError(e);
	} finally {
		saving.value = false;
	}
}

async function submitRow(row) {
	try {
		await teacherApi.submitAssessmentResult({ name: row.result_name });
		notifySuccess(`Note de ${row.student_name} validée.`);
		await load();
	} catch (e) {
		notifyError(e);
	}
}

load();
</script>
