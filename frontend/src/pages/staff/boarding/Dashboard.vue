<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="flex justify-end">
			<Button variant="solid" theme="red" @click="openAssign">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Affecter un lit
			</Button>
		</div>

		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
			<StatCard label="Bâtiments" :value="data.buildings" icon="layers" tone="gray" />
			<StatCard label="Chambres" :value="data.rooms" icon="grid" tone="gray" />
			<StatCard label="Lits" :value="data.beds" icon="moon" tone="gray" />
			<StatCard label="Occupés" :value="data.occupied" icon="user-check" tone="gold" />
			<StatCard label="Disponibles" :value="data.available" icon="check-circle" tone="green" />
		</div>

		<SectionCard title="Occupation par bâtiment" no-padding>
			<EmptyState v-if="!data.buildings_detail.length" icon="layers" title="Aucun bâtiment" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Bâtiment</th>
						<th class="px-5 py-3">Surveillant</th>
						<th class="px-5 py-3">Chambres</th>
						<th class="px-5 py-3">Lits occupés</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="b in data.buildings_detail" :key="b.name">
						<td class="px-5 py-3 font-medium text-gray-800">{{ b.building_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ b.supervisor_name || "—" }}</td>
						<td class="px-5 py-3">{{ b.room_count }}</td>
						<td class="px-5 py-3">{{ b.occupied_count }} / {{ b.bed_count }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<Dialog v-model="assignDialogOpen" :options="{ title: 'Affecter un lit' }">
			<template #body-content>
				<div class="space-y-4">
					<LinkField v-model="assignForm.student" label="Élève" doctype="Student" search-field="student_name" required />
					<div>
						<label class="mb-1 block text-xs text-gray-500">Lit disponible</label>
						<select v-model="assignForm.bed" class="w-full rounded-md border-gray-200 text-sm">
							<option value="">Sélectionner un lit...</option>
							<option v-for="b in availableBeds" :key="b.name" :value="b.name">
								{{ b.building_name }} - Ch. {{ b.room_number }} - Lit {{ b.bed_number }}
							</option>
						</select>
					</div>
					<LinkField v-model="assignForm.academic_year" label="Année scolaire" doctype="Academic Year" search-field="academic_year_name" />
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="red" class="w-full" :loading="assigning" @click="assign">Affecter</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { Button, Dialog, FeatherIcon, LoadingIndicator } from "frappe-ui";
import { boardingApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import LinkField from "@/components/resource/LinkField.vue";

const { data, loading, reload } = useAsync(() => boardingApi.dashboard(), {
	initial: { buildings: 0, rooms: 0, beds: 0, occupied: 0, available: 0, active_assignments: 0, buildings_detail: [] },
});

const assignDialogOpen = ref(false);
const assigning = ref(false);
const assignForm = reactive({ student: "", bed: "", academic_year: "" });
const availableBeds = ref([]);

async function openAssign() {
	assignForm.student = "";
	assignForm.bed = "";
	availableBeds.value = await boardingApi.availableBeds();
	assignDialogOpen.value = true;
}

async function assign() {
	if (!assignForm.student || !assignForm.bed) {
		notifyError(null, "Veuillez choisir un élève et un lit.");
		return;
	}
	assigning.value = true;
	try {
		await boardingApi.assignBed({ ...assignForm });
		notifySuccess("Lit affecté avec succès.");
		assignDialogOpen.value = false;
		reload();
	} catch (e) {
		notifyError(e);
	} finally {
		assigning.value = false;
	}
}
</script>
