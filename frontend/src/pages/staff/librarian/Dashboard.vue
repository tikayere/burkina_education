<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="flex justify-end">
			<Button variant="solid" theme="red" @click="issueDialogOpen = true">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Emprunter un livre
			</Button>
		</div>

		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
			<StatCard label="Titres" :value="data.books" icon="book" tone="gray" />
			<StatCard label="Exemplaires" :value="data.copies" icon="layers" tone="gray" />
			<StatCard label="Disponibles" :value="data.available" icon="check-circle" tone="green" />
			<StatCard label="Empruntés" :value="data.checked_out" icon="book-open" tone="gold" />
			<StatCard label="En retard" :value="data.overdue" icon="alert-triangle" :tone="data.overdue ? 'red' : 'gray'" />
			<StatCard label="Adhérents actifs" :value="data.active_members" icon="user-check" tone="gray" />
		</div>

		<div class="grid gap-6 lg:grid-cols-2">
			<SectionCard title="À rendre bientôt" no-padding>
				<EmptyState v-if="!data.due_soon.length" icon="check-circle" title="Rien à signaler" />
				<table v-else class="w-full text-sm">
					<tbody class="divide-y divide-gray-100">
						<tr v-for="l in data.due_soon" :key="l.name">
							<td class="px-5 py-3 font-medium text-gray-800">{{ l.book_title }}</td>
							<td class="px-5 py-3 text-gray-500">{{ l.student }}</td>
							<td class="px-5 py-3 text-right">{{ formatDate(l.due_date) }}</td>
						</tr>
					</tbody>
				</table>
			</SectionCard>

			<SectionCard title="En retard" no-padding>
				<EmptyState v-if="!data.overdue_list.length" icon="check-circle" title="Aucun retard" />
				<table v-else class="w-full text-sm">
					<tbody class="divide-y divide-gray-100">
						<tr v-for="l in data.overdue_list" :key="l.name">
							<td class="px-5 py-3 font-medium text-gray-800">{{ l.book_title }}</td>
							<td class="px-5 py-3 text-gray-500">{{ l.student }}</td>
							<td class="px-5 py-3 text-right text-bf-red-600">{{ formatDate(l.due_date) }}</td>
						</tr>
					</tbody>
				</table>
			</SectionCard>
		</div>

		<Dialog v-model="issueDialogOpen" :options="{ title: 'Emprunter un livre' }">
			<template #body-content>
				<div class="space-y-4">
					<LinkField v-model="issueForm.student" label="Élève" doctype="Student" search-field="student_name" required @update:model-value="lookupMember" />
					<div v-if="member" class="rounded-md border border-gray-100 bg-gray-50 p-3 text-sm">
						<p class="font-medium text-gray-700">{{ member.student_name }} - {{ member.status }}</p>
						<p class="text-gray-500">{{ member.open_loans.length }} / {{ member.max_books }} livre(s) emprunté(s)</p>
						<p v-if="!member.can_borrow" class="mt-1 font-medium text-bf-red-600">Cet élève ne peut pas emprunter de livre supplémentaire.</p>
					</div>
					<p v-else-if="issueForm.student" class="text-sm text-bf-red-600">Aucune adhésion à la bibliothèque pour cet élève.</p>
					<LinkField v-model="issueForm.book" label="Livre" doctype="Library Book" search-field="title" required />
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="red" class="w-full" :loading="issuing" :disabled="member && !member.can_borrow" @click="issue">
					Emprunter
				</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { Button, Dialog, FeatherIcon, LoadingIndicator } from "frappe-ui";
import { librarianApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import LinkField from "@/components/resource/LinkField.vue";

const { data, loading, reload } = useAsync(() => librarianApi.dashboard(), {
	initial: { books: 0, copies: 0, available: 0, checked_out: 0, overdue: 0, active_members: 0, due_soon: [], overdue_list: [] },
});

const issueDialogOpen = ref(false);
const issuing = ref(false);
const issueForm = reactive({ student: "", book: "" });
const member = ref(null);

async function lookupMember(student) {
	issueForm.student = student;
	member.value = student ? await librarianApi.findMember({ student }) : null;
}

async function issue() {
	if (!issueForm.student || !issueForm.book) {
		notifyError(null, "Veuillez choisir un élève et un livre.");
		return;
	}
	issuing.value = true;
	try {
		await librarianApi.issueBook({ student: issueForm.student, book: issueForm.book });
		notifySuccess("Livre emprunté avec succès.");
		issueDialogOpen.value = false;
		issueForm.student = "";
		issueForm.book = "";
		member.value = null;
		reload();
	} catch (e) {
		notifyError(e);
	} finally {
		issuing.value = false;
	}
}
</script>
