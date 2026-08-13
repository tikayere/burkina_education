<template>
	<div class="space-y-4">
		<div class="relative w-full max-w-xs">
			<FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
			<input
				v-model="query"
				type="text"
				placeholder="Rechercher un livre ou un élève..."
				class="w-full rounded-md border-gray-200 py-1.5 pl-8 text-sm focus:border-bf-red-400 focus:ring-bf-red-400"
				@input="onSearch"
			/>
		</div>

		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
		</div>
		<SectionCard v-else no-padding>
			<EmptyState v-if="!list.data?.length" icon="book-open" title="Aucun emprunt" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Livre</th>
						<th class="px-5 py-3">Élève</th>
						<th class="px-5 py-3">Emprunté le</th>
						<th class="px-5 py-3">À rendre le</th>
						<th class="px-5 py-3">Statut</th>
						<th class="px-5 py-3">Amende</th>
						<th class="px-5 py-3 text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="l in list.data" :key="l.name">
						<td class="px-5 py-3 font-medium text-gray-800">{{ l.book_title }}</td>
						<td class="px-5 py-3 text-gray-500">{{ l.student }}</td>
						<td class="px-5 py-3">{{ formatDate(l.issue_date) }}</td>
						<td class="px-5 py-3">{{ formatDate(l.due_date) }}</td>
						<td class="px-5 py-3">
							<StatusBadge :text="l.status" :tone="l.status === 'En retard' ? 'red' : l.status === 'Retourné' ? 'green' : l.status === 'Perdu' ? 'red' : 'gold'" />
						</td>
						<td class="px-5 py-3">{{ l.fine_amount ? formatCurrency(l.fine_amount) : "—" }}</td>
						<td class="px-5 py-3 text-right">
							<div v-if="['Emprunté', 'En retard'].includes(l.status)" class="flex justify-end gap-2">
								<Button size="sm" variant="outline" :loading="acting === l.name" @click="doReturn(l, false)">Retourner</Button>
								<Button size="sm" variant="outline" theme="red" :loading="acting === l.name" @click="doReturn(l, true)">Perdu</Button>
							</div>
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Button, FeatherIcon, LoadingIndicator, createListResource } from "frappe-ui";
import { librarianApi } from "@/api";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const query = ref("");
const acting = ref("");
let searchDebounce = null;

const list = createListResource({
	doctype: "Library Transaction",
	fields: ["name", "book_title", "student", "issue_date", "due_date", "return_date", "status", "fine_amount"],
	orderBy: "issue_date desc",
	pageLength: 50,
	auto: true,
	onError: (e) => notifyError(e),
});

function onSearch() {
	clearTimeout(searchDebounce);
	searchDebounce = setTimeout(() => {
		list.filters = query.value ? { book_title: ["like", `%${query.value}%`] } : {};
		list.reload();
	}, 250);
}

async function doReturn(loan, lost) {
	acting.value = loan.name;
	try {
		await librarianApi.returnBook({ transaction: loan.name, lost });
		notifySuccess(lost ? "Livre marqué comme perdu." : "Livre retourné avec succès.");
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		acting.value = "";
	}
}
</script>
