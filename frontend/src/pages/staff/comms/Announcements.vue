<template>
	<div class="space-y-4">
		<div class="flex justify-end">
			<Button variant="solid" theme="red" @click="openCreate">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Nouvelle annonce
			</Button>
		</div>

		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
		</div>
		<SectionCard v-else no-padding>
			<EmptyState v-if="!list.data?.length" icon="bell" title="Aucune annonce" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Titre</th>
						<th class="px-5 py-3">Audience</th>
						<th class="px-5 py-3">Priorité</th>
						<th class="px-5 py-3">Statut</th>
						<th class="px-5 py-3 text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="a in list.data" :key="a.name">
						<td class="px-5 py-3 font-medium text-gray-800">{{ a.title }}</td>
						<td class="px-5 py-3 text-gray-500">{{ a.audience_type }}{{ a.audience_reference ? ` · ${a.audience_reference}` : "" }}</td>
						<td class="px-5 py-3">
							<StatusBadge :text="a.priority" :tone="a.priority === 'Urgente' ? 'red' : a.priority === 'Élevée' ? 'gold' : 'gray'" />
						</td>
						<td class="px-5 py-3">
							<StatusBadge :text="a.publication_status" :tone="a.publication_status === 'Published' ? 'green' : a.publication_status === 'Archived' ? 'gray' : 'gold'" />
						</td>
						<td class="px-5 py-3 text-right">
							<div class="flex justify-end gap-2">
								<Button v-if="a.publication_status === 'Draft'" size="sm" variant="outline" :loading="acting === a.name" @click="publish(a)">Publier</Button>
								<Button v-if="a.publication_status === 'Published'" size="sm" variant="outline" theme="gray" :loading="acting === a.name" @click="archive(a)">Archiver</Button>
							</div>
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<Dialog v-model="dialogOpen" :options="{ title: 'Nouvelle annonce', size: 'lg' }">
			<template #body-content>
				<div class="space-y-4">
					<FormControl type="text" label="Titre" v-model="form.title" required />
					<FormControl type="textarea" label="Contenu" v-model="form.content" required />
					<div class="grid grid-cols-2 gap-4">
						<FormControl type="select" label="Priorité" v-model="form.priority" :options="['Normal', 'Élevée', 'Urgente']" />
						<FormControl
							type="select"
							label="Audience"
							v-model="form.audience_type"
							:options="['All', 'All Guardians', 'All Students', 'All Teachers', 'Education Level', 'Grade', 'Student Group']"
						/>
					</div>
					<LinkField
						v-if="form.audience_type === 'Education Level'"
						v-model="form.audience_reference"
						label="Niveau"
						doctype="Education Level"
						search-field="education_level_name"
					/>
					<LinkField v-if="form.audience_type === 'Grade'" v-model="form.audience_reference" label="Classe" doctype="Grade" search-field="grade_name" />
					<LinkField
						v-if="form.audience_type === 'Student Group'"
						v-model="form.audience_reference"
						label="Groupe d'élèves"
						doctype="Student Group"
						search-field="student_group_name"
					/>
					<div class="grid grid-cols-2 gap-4">
						<FormControl type="date" label="Date de début" v-model="form.start_date" required />
						<FormControl type="date" label="Date de fin (optionnel)" v-model="form.end_date" />
					</div>
					<div>
						<label class="mb-2 block text-xs text-gray-500">Canaux de notification</label>
						<div class="flex flex-wrap gap-4">
							<FormControl type="checkbox" label="Application" v-model="form.notify_in_app" />
							<FormControl type="checkbox" label="SMS" v-model="form.notify_sms" />
							<FormControl type="checkbox" label="WhatsApp" v-model="form.notify_whatsapp" />
							<FormControl type="checkbox" label="Email" v-model="form.notify_email" />
						</div>
					</div>
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="red" class="w-full" :loading="saving" @click="save">Créer le brouillon</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
/* Announcement is the one doctype whose create form has a Dynamic Link
 * (audience_reference, whose target doctype depends on audience_type) -
 * ResourceFormDialog's declarative fields can't express that, so this page
 * is bespoke (docs/architecture.md section M). Publish/archive call the
 * doctype's own existing whitelisted methods via runDocMethod rather than a
 * new Python wrapper - see comms_api.py's module docstring. */
import { reactive, ref } from "vue";
import { Button, Dialog, FeatherIcon, FormControl, LoadingIndicator, call, createListResource } from "frappe-ui";
import { runDocMethod } from "@/api";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import LinkField from "@/components/resource/LinkField.vue";

const list = createListResource({
	doctype: "Announcement",
	fields: ["name", "title", "audience_type", "audience_reference", "priority", "publication_status"],
	orderBy: "modified desc",
	pageLength: 50,
	auto: true,
	onError: (e) => notifyError(e),
});

const dialogOpen = ref(false);
const saving = ref(false);
const acting = ref("");
const form = reactive({
	title: "",
	content: "",
	priority: "Normal",
	audience_type: "All",
	audience_reference: "",
	start_date: new Date().toISOString().slice(0, 10),
	end_date: "",
	notify_in_app: 1,
	notify_sms: 0,
	notify_whatsapp: 0,
	notify_email: 0,
});

function openCreate() {
	Object.assign(form, {
		title: "",
		content: "",
		priority: "Normal",
		audience_type: "All",
		audience_reference: "",
		start_date: new Date().toISOString().slice(0, 10),
		end_date: "",
		notify_in_app: 1,
		notify_sms: 0,
		notify_whatsapp: 0,
		notify_email: 0,
	});
	dialogOpen.value = true;
}

async function save() {
	if (!form.title || !form.content || !form.start_date) {
		notifyError(null, "Le titre, le contenu et la date de début sont obligatoires.");
		return;
	}
	saving.value = true;
	try {
		const audienceRefDoctype = { "Education Level": "Education Level", Grade: "Grade", "Student Group": "Student Group" }[form.audience_type];
		await call("frappe.client.insert", {
			doc: {
				doctype: "Announcement",
				...form,
				audience_reference_doctype: audienceRefDoctype,
				audience_reference: audienceRefDoctype ? form.audience_reference : "",
			},
		});
		notifySuccess("Brouillon d'annonce créé.");
		dialogOpen.value = false;
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		saving.value = false;
	}
}

async function publish(row) {
	acting.value = row.name;
	try {
		// Announcement.publish() always fans out through a background job
		// (large audiences shouldn't block the "Publier" click) - so there's
		// no synchronous recipient count to report here, just confirmation
		// the job was queued.
		await runDocMethod("Announcement", row.name, "publish");
		notifySuccess("Annonce publiée - l'envoi aux destinataires est en cours.");
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		acting.value = "";
	}
}

async function archive(row) {
	acting.value = row.name;
	try {
		await runDocMethod("Announcement", row.name, "archive");
		notifySuccess("Annonce archivée.");
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		acting.value = "";
	}
}
</script>
