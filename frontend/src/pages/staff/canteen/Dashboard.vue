<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
			<StatCard label="Formules actives" :value="data.plans" icon="clipboard" tone="gray" />
			<StatCard label="Abonnements actifs" :value="data.active_subscriptions" icon="users" tone="gold" />
			<StatCard label="Repas pris aujourd'hui" :value="data.consumed_today" icon="check-circle" tone="green" />
		</div>

		<SectionCard v-if="plansBreakdown.length" title="Abonnements par formule">
			<DonutChart :data="plansBreakdown" />
		</SectionCard>

		<SectionCard title="Faire l'appel du repas">
			<div class="flex flex-wrap items-end gap-3">
				<div>
					<label class="mb-1 block text-xs text-gray-500">Formule</label>
					<select v-model="rosterForm.meal_plan" class="rounded-md border-gray-200 text-sm" @change="loadRoster">
						<option value="">Toutes les formules</option>
						<option v-for="p in data.by_plan" :key="p.meal_plan" :value="p.meal_plan">{{ p.plan_name }} ({{ p.n }})</option>
					</select>
				</div>
				<div>
					<label class="mb-1 block text-xs text-gray-500">Repas</label>
					<select v-model="rosterForm.meal_type" class="rounded-md border-gray-200 text-sm" @change="loadRoster">
						<option v-for="t in mealTypes" :key="t" :value="t">{{ t }}</option>
					</select>
				</div>
				<div>
					<label class="mb-1 block text-xs text-gray-500">Date</label>
					<input v-model="rosterForm.date" type="date" class="rounded-md border-gray-200 text-sm" @change="loadRoster" />
				</div>
				<Button variant="outline" :loading="rosterLoading" @click="loadRoster">Actualiser</Button>
			</div>

			<div v-if="roster.length" class="mt-4 space-y-2">
				<div class="flex items-center justify-between">
					<label class="flex items-center gap-2 text-sm text-gray-600">
						<input type="checkbox" :checked="allChecked" @change="toggleAll($event.target.checked)" />
						Tout sélectionner
					</label>
					<Button variant="solid" theme="green" size="sm" :loading="marking" @click="markSelected">
						Marquer présent ({{ selected.length }})
					</Button>
				</div>
				<ul class="divide-y divide-gray-100 rounded-lg border border-gray-100">
					<li v-for="row in roster" :key="row.name" class="flex items-center justify-between px-4 py-2.5">
						<label class="flex items-center gap-3">
							<input type="checkbox" :checked="isSelected(row)" :disabled="row.consumed" @change="toggle(row)" />
							<span class="text-sm" :class="row.consumed ? 'text-gray-400 line-through' : 'text-gray-800'">{{ row.student_name }}</span>
						</label>
						<FeatherIcon v-if="row.consumed" name="check-circle" class="h-4 w-4 text-bf-green-500" />
					</li>
				</ul>
			</div>
			<EmptyState v-else-if="rosterLoaded" icon="coffee" title="Aucun abonné pour cette sélection" />
		</SectionCard>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Button, FeatherIcon, LoadingIndicator } from "frappe-ui";
import { canteenApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import DonutChart from "@/components/charts/DonutChart.vue";

const mealTypes = ["Petit-déjeuner", "Déjeuner", "Goûter"];

const { data, loading } = useAsync(() => canteenApi.dashboard(), {
	initial: { plans: 0, active_subscriptions: 0, consumed_today: 0, by_plan: [] },
});

const plansBreakdown = computed(() =>
	data.value.by_plan.filter((p) => p.n > 0).map((p) => ({ label: p.plan_name || "—", value: p.n })),
);

const rosterForm = reactive({ meal_plan: "", meal_type: "Déjeuner", date: new Date().toISOString().slice(0, 10) });
const roster = ref([]);
const rosterLoading = ref(false);
const rosterLoaded = ref(false);
const selected = ref([]);
const marking = ref(false);

async function loadRoster() {
	rosterLoading.value = true;
	try {
		roster.value = await canteenApi.roster({ ...rosterForm, meal_plan: rosterForm.meal_plan || undefined });
		selected.value = [];
		rosterLoaded.value = true;
	} catch (e) {
		notifyError(e);
	} finally {
		rosterLoading.value = false;
	}
}

const isSelected = (row) => selected.value.includes(row.name);
function toggle(row) {
	selected.value = isSelected(row) ? selected.value.filter((n) => n !== row.name) : [...selected.value, row.name];
}
const allChecked = computed(() => {
	const eligible = roster.value.filter((r) => !r.consumed);
	return eligible.length > 0 && eligible.every((r) => isSelected(r));
});
function toggleAll(checked) {
	selected.value = checked ? roster.value.filter((r) => !r.consumed).map((r) => r.name) : [];
}

async function markSelected() {
	if (!selected.value.length) {
		notifyError(null, "Sélectionnez au moins un élève.");
		return;
	}
	marking.value = true;
	try {
		const result = await canteenApi.markConsumption({
			subscriptions: selected.value,
			date: rosterForm.date,
			meal_type: rosterForm.meal_type,
		});
		notifySuccess(`${result.created} élève(s) marqué(s) présent(s).`);
		loadRoster();
	} catch (e) {
		notifyError(e);
	} finally {
		marking.value = false;
	}
}

loadRoster();
</script>
