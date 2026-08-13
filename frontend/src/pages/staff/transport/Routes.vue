<template>
	<div class="space-y-4">
		<div class="flex justify-end">
			<Button variant="solid" theme="red" @click="openCreate">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Nouvel itinéraire
			</Button>
		</div>

		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
		</div>
		<SectionCard v-else no-padding>
			<EmptyState v-if="!list.data?.length" icon="map" title="Aucun itinéraire" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Itinéraire</th>
						<th class="px-5 py-3">Véhicule</th>
						<th class="px-5 py-3">Chauffeur</th>
						<th class="px-5 py-3">Distance</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="r in list.data" :key="r.name" class="cursor-pointer hover:bg-gray-50" @click="openEdit(r)">
						<td class="px-5 py-3 font-medium text-gray-800">{{ r.route_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ r.vehicle || "—" }}</td>
						<td class="px-5 py-3 text-gray-500">{{ r.driver || "—" }}</td>
						<td class="px-5 py-3">{{ r.distance_km ? `${r.distance_km} km` : "—" }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<Dialog v-model="dialogOpen" :options="{ title: editing ? 'Modifier l’itinéraire' : 'Nouvel itinéraire', size: 'lg' }">
			<template #body-content>
				<div class="space-y-4">
					<FormControl type="text" label="Nom de l'itinéraire" v-model="form.route_name" required />
					<div class="grid grid-cols-2 gap-4">
						<LinkField v-model="form.vehicle" label="Véhicule" doctype="Vehicle" />
						<LinkField v-model="form.driver" label="Chauffeur" doctype="Driver" search-field="full_name" />
					</div>
					<FormControl type="number" label="Distance (km)" v-model="form.distance_km" step="any" />
					<FormControl type="textarea" label="Description" v-model="form.description" />

					<div>
						<div class="mb-2 flex items-center justify-between">
							<label class="text-xs text-gray-500">Arrêts</label>
							<Button size="sm" variant="ghost" @click="form.stops.push({ stop_name: '', pickup_time: '', drop_time: '' })">
								<template #prefix><FeatherIcon name="plus" class="h-3.5 w-3.5" /></template>
								Ajouter un arrêt
							</Button>
						</div>
						<div v-for="(stop, i) in form.stops" :key="i" class="mb-2 grid grid-cols-[1fr_auto_auto_auto] items-end gap-2">
							<FormControl type="text" placeholder="Nom de l'arrêt" v-model="stop.stop_name" />
							<FormControl type="time" v-model="stop.pickup_time" />
							<FormControl type="time" v-model="stop.drop_time" />
							<button class="p-1.5 text-gray-400 hover:text-bf-red-500" @click="form.stops.splice(i, 1)">
								<FeatherIcon name="x" class="h-4 w-4" />
							</button>
						</div>
						<p v-if="!form.stops.length" class="text-sm text-gray-400">Aucun arrêt défini.</p>
					</div>
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="red" class="w-full" :loading="saving" @click="save">Enregistrer</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
/* Transport Route is the one doctype whose form ResourceFormDialog can't
 * cover generically - it has a child table (stops) - so it gets its own
 * page rather than a config object (docs/architecture.md section M). */
import { reactive, ref } from "vue";
import { Button, Dialog, FeatherIcon, FormControl, LoadingIndicator, call, createListResource } from "frappe-ui";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import LinkField from "@/components/resource/LinkField.vue";

const list = createListResource({
	doctype: "Transport Route",
	fields: ["name", "route_name", "vehicle", "driver", "distance_km"],
	orderBy: "route_name asc",
	pageLength: 100,
	auto: true,
	onError: (e) => notifyError(e),
});

const dialogOpen = ref(false);
const saving = ref(false);
const editing = ref(null);
const form = reactive({ route_name: "", vehicle: "", driver: "", distance_km: "", description: "", stops: [] });

function resetForm() {
	Object.assign(form, { route_name: "", vehicle: "", driver: "", distance_km: "", description: "", stops: [] });
}

function openCreate() {
	editing.value = null;
	resetForm();
	dialogOpen.value = true;
}

async function openEdit(row) {
	editing.value = row;
	const doc = await call("frappe.client.get", { doctype: "Transport Route", name: row.name });
	Object.assign(form, {
		route_name: doc.route_name,
		vehicle: doc.vehicle,
		driver: doc.driver,
		distance_km: doc.distance_km,
		description: doc.description,
		stops: (doc.stops || []).map((s) => ({ stop_name: s.stop_name, pickup_time: s.pickup_time, drop_time: s.drop_time })),
	});
	dialogOpen.value = true;
}

async function save() {
	if (!form.route_name) {
		notifyError(null, "Le nom de l'itinéraire est obligatoire.");
		return;
	}
	saving.value = true;
	try {
		// A child table (stops) needs the full-document `save`/`insert`
		// endpoints, not `set_value` (which only reliably updates plain
		// fields) - see docs/architecture.md section M.
		const payload = { ...form, stops: form.stops.filter((s) => s.stop_name) };
		if (editing.value) {
			await call("frappe.client.save", { doc: { doctype: "Transport Route", name: editing.value.name, ...payload } });
			notifySuccess("Itinéraire modifié.");
		} else {
			await call("frappe.client.insert", { doc: { doctype: "Transport Route", ...payload } });
			notifySuccess("Itinéraire créé.");
		}
		dialogOpen.value = false;
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		saving.value = false;
	}
}
</script>
