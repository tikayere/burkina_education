<template>
	<div class="space-y-4">
		<div v-if="list.loading && !list.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
		</div>
		<SectionCard v-else title="Transactions Mobile Money" no-padding>
			<EmptyState v-if="!list.data?.length" icon="smartphone" title="Aucune transaction" />
			<table v-else class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Référence</th>
						<th class="px-5 py-3">Élève</th>
						<th class="px-5 py-3">Opérateur</th>
						<th class="px-5 py-3">Montant</th>
						<th class="px-5 py-3">Statut</th>
						<th class="px-5 py-3">Initiée le</th>
						<th class="px-5 py-3 text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="t in list.data" :key="t.name">
						<td class="px-5 py-3 font-medium text-gray-800">{{ t.reference_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ t.student }}</td>
						<td class="px-5 py-3 text-gray-500">{{ t.provider }}</td>
						<td class="px-5 py-3">{{ formatCurrency(t.amount, t.currency) }}</td>
						<td class="px-5 py-3">
							<StatusBadge :text="t.status" :tone="t.status === 'Success' ? 'green' : t.status === 'Failed' ? 'red' : 'gold'" />
						</td>
						<td class="px-5 py-3 text-gray-500">{{ formatDateTime(t.initiated_on) }}</td>
						<td class="px-5 py-3 text-right">
							<Button v-if="['Initiated', 'Pending', 'Failed'].includes(t.status)" size="sm" variant="outline" :loading="retrying === t.name" @click="retry(t)">
								Revérifier
							</Button>
						</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { Button, LoadingIndicator, createListResource } from "frappe-ui";
import { financeApi } from "@/api";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import { formatCurrency, formatDateTime } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const retrying = ref("");

const list = createListResource({
	doctype: "Mobile Money Transaction",
	fields: ["name", "provider", "status", "reference_name", "student", "amount", "currency", "initiated_on"],
	orderBy: "initiated_on desc",
	pageLength: 50,
	auto: true,
	onError: (e) => notifyError(e),
});

async function retry(txn) {
	retrying.value = txn.name;
	try {
		const result = await financeApi.retryMobileMoneyVerification({ transaction: txn.name });
		notifySuccess(result.status === "Success" ? "Paiement confirmé." : "Vérification effectuée : toujours en échec.");
		list.reload();
	} catch (e) {
		notifyError(e);
	} finally {
		retrying.value = "";
	}
}
</script>
