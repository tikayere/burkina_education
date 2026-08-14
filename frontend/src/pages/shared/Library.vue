<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else class="space-y-6">
		<EmptyState v-if="!data.membership" icon="book-open" title="Aucune adhésion à la bibliothèque" />
		<template v-else>
			<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
				<StatCard label="Statut" :value="data.membership.status" icon="user-check" :tone="data.membership.status === 'Active' ? 'green' : 'gray'" />
				<StatCard label="Livres empruntés" :value="data.open_loans.length" icon="book-open" tone="gold" />
				<StatCard label="Limite" :value="data.membership.max_books" icon="hash" tone="gray" />
				<StatCard label="Expire le" :value="formatDate(data.membership.expiry_date)" icon="calendar" tone="gray" />
			</div>

			<SectionCard title="Emprunts en cours" no-padding>
				<EmptyState v-if="!data.open_loans.length" icon="book" title="Aucun livre emprunté actuellement" />
				<table v-else class="w-full text-sm">
					<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
						<tr>
							<th class="px-5 py-3">Livre</th>
							<th class="px-5 py-3">Emprunté le</th>
							<th class="px-5 py-3">À rendre le</th>
							<th class="px-5 py-3">Statut</th>
							<th class="px-5 py-3">Amende</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="l in data.open_loans" :key="l.name">
							<td class="px-5 py-3 font-medium text-gray-800">{{ l.book_title }}</td>
							<td class="px-5 py-3">{{ formatDate(l.issue_date) }}</td>
							<td class="px-5 py-3">{{ formatDate(l.due_date) }}</td>
							<td class="px-5 py-3"><StatusBadge :text="l.status" :tone="l.status === 'En retard' ? 'red' : 'gold'" /></td>
							<td class="px-5 py-3">{{ l.fine_amount ? formatCurrency(l.fine_amount) : "—" }}</td>
						</tr>
					</tbody>
				</table>
			</SectionCard>

			<SectionCard title="Historique" no-padding>
				<EmptyState v-if="!data.history.length" icon="clock" title="Aucun emprunt précédent" />
				<table v-else class="w-full text-sm">
					<tbody class="divide-y divide-gray-100">
						<tr v-for="l in data.history" :key="l.name">
							<td class="px-5 py-3 font-medium text-gray-800">{{ l.book_title }}</td>
							<td class="px-5 py-3 text-gray-500">{{ formatDate(l.issue_date) }} → {{ formatDate(l.return_date) }}</td>
							<td class="px-5 py-3"><StatusBadge :text="l.status" :tone="l.status === 'Perdu' ? 'red' : 'gray'" /></td>
							<td class="px-5 py-3 text-right">{{ l.fine_amount ? formatCurrency(l.fine_amount) : "—" }}</td>
						</tr>
					</tbody>
				</table>
			</SectionCard>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.library(), {
	watchSource: () => props.student,
	initial: { membership: null, open_loans: [], history: [] },
});
</script>
