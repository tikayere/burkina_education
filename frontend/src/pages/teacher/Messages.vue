<template>
	<div class="space-y-6">
		<SectionCard title="Écrire aux parents" subtitle="Message envoyé sur l'espace parent de l'élève choisi (notification dans l'application).">
			<div class="space-y-4">
				<FormControl type="select" label="Classe" v-model="form.student_group" :options="groupOptions" @update:modelValue="onGroupChange" />
				<FormControl type="select" label="Élève" v-model="form.student" :options="studentOptions" />
				<FormControl type="textarea" label="Message" v-model="form.message" placeholder="Votre message aux parents..." />
				<Button variant="solid" theme="green" :loading="sending" @click="send">Envoyer</Button>
			</div>
		</SectionCard>

		<SectionCard title="Messages reçus" no-padding>
			<div v-if="loading" class="flex justify-center py-10">
				<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
			</div>
			<EmptyState v-else-if="!inbox.length" icon="mail" title="Aucun message" />
			<ul v-else class="divide-y divide-gray-100">
				<li v-for="m in inbox" :key="m.name" class="p-5">
					<div class="flex items-center justify-between">
						<h3 class="text-sm font-semibold text-gray-900">{{ m.subject }}</h3>
						<span class="text-xs text-gray-400">{{ formatDateTime(m.queued_on) }}</span>
					</div>
					<p class="mt-1 text-sm text-gray-600">{{ m.message }}</p>
				</li>
			</ul>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Button, FormControl, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import { formatDateTime } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const { data: inbox, loading } = useAsync(() => teacherApi.inbox({ limit: 50 }), { initial: [] });

const groups = ref([]);
const students = ref([]);
const sending = ref(false);
const form = reactive({ student_group: "", student: "", message: "" });

const groupOptions = computed(() => [{ label: "Sélectionner une classe...", value: "" }, ...groups.value.map((g) => ({ label: g.student_group_name, value: g.name }))]);
const studentOptions = computed(() => [{ label: "Sélectionner un élève...", value: "" }, ...students.value.map((s) => ({ label: s.student_name, value: s.student }))]);

teacherApi.groups().then((g) => (groups.value = g));

async function onGroupChange(value) {
	form.student = "";
	students.value = value ? await teacherApi.groupStudents({ student_group: value }) : [];
}

async function send() {
	if (!form.student || !form.message) {
		notifyError(null, "Veuillez choisir un élève et rédiger un message.");
		return;
	}
	sending.value = true;
	try {
		const result = await teacherApi.sendMessage({ student: form.student, message: form.message });
		if (result.sent) {
			notifySuccess(`Message envoyé (${result.sent} destinataire(s)).`);
		} else {
			notifyError(null, "Aucun tuteur n'a accès au portail pour recevoir ce message.");
		}
		form.message = "";
	} catch (e) {
		notifyError(e);
	} finally {
		sending.value = false;
	}
}
</script>
