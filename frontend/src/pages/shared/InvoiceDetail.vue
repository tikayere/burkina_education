<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else-if="data" class="space-y-6">
		<div class="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<div>
				<h2 class="text-lg font-semibold text-gray-900">{{ data.name }}</h2>
				<p class="text-sm text-gray-500">Échéance : {{ formatDate(data.due_date) }}</p>
			</div>
			<div class="flex items-center gap-4">
				<div class="text-right">
					<p class="text-xs uppercase tracking-wide text-gray-400">Solde dû</p>
					<p class="text-xl font-semibold text-gray-900">{{ formatCurrency(data.outstanding_amount, data.currency) }}</p>
				</div>
				<Button v-if="student && data.outstanding_amount > 0" variant="solid" theme="red" @click="openPayDialog">
					Payer par Mobile Money
				</Button>
			</div>
		</div>

		<SectionCard title="Détail" no-padding>
			<table class="w-full text-sm">
				<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
					<tr>
						<th class="px-5 py-3">Article</th>
						<th class="px-5 py-3">Description</th>
						<th class="px-5 py-3 text-right">Montant</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-100">
					<tr v-for="(item, i) in data.items" :key="i">
						<td class="px-5 py-3 font-medium text-gray-800">{{ item.item_name }}</td>
						<td class="px-5 py-3 text-gray-500">{{ item.description || "—" }}</td>
						<td class="px-5 py-3 text-right">{{ formatCurrency(item.amount, data.currency) }}</td>
					</tr>
				</tbody>
			</table>
		</SectionCard>

		<div class="grid gap-6 sm:grid-cols-2">
			<SectionCard title="Échéancier">
				<EmptyState v-if="!data.payment_schedule.length" icon="calendar" title="Aucun échéancier" />
				<ul v-else class="divide-y divide-gray-100 text-sm">
					<li v-for="(s, i) in data.payment_schedule" :key="i" class="flex justify-between py-2">
						<span>{{ formatDate(s.due_date) }}</span>
						<span>{{ formatCurrency(s.payment_amount, data.currency) }}</span>
					</li>
				</ul>
			</SectionCard>
			<SectionCard title="Paiements reçus">
				<EmptyState v-if="!data.payments.length" icon="check-circle" title="Aucun paiement enregistré" />
				<ul v-else class="divide-y divide-gray-100 text-sm">
					<li v-for="p in data.payments" :key="p.payment_entry" class="py-2">
						<div class="flex justify-between">
							<span class="font-medium text-gray-800">{{ formatCurrency(p.allocated_amount, data.currency) }}</span>
							<span class="text-gray-500">{{ formatDate(p.posting_date) }}</span>
						</div>
						<p class="text-xs text-gray-400">{{ p.mode_of_payment || "—" }}</p>
					</li>
				</ul>
			</SectionCard>
		</div>

		<Dialog v-model="payDialogOpen" :options="{ title: 'Paiement Mobile Money' }">
			<template #body-content>
				<div class="space-y-4">
					<FormControl
						type="select"
						label="Opérateur"
						v-model="payForm.provider"
						:options="providerOptions"
					/>
					<FormControl type="text" label="Numéro de téléphone" v-model="payForm.phone_number" placeholder="70 00 00 00" />
					<FormControl
						type="number"
						label="Montant"
						v-model="payForm.amount"
						:placeholder="String(data.outstanding_amount)"
					/>
					<p class="text-xs text-gray-400">Laissez le montant vide pour payer le solde total dû.</p>
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="red" :loading="paying" class="w-full" @click="submitPayment">
					Confirmer le paiement
				</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { Button, Dialog, FormControl, LoadingIndicator } from "frappe-ui";
import { childApi, selfApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({ student: { type: String, default: "" }, name: { type: String, required: true } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading, reload } = useAsync(() => api.value.invoice({ name: props.name }), {
	watchSource: () => [props.student, props.name],
});

const payDialogOpen = ref(false);
const paying = ref(false);
const providers = ref([]);
const payForm = reactive({ provider: "", phone_number: "", amount: "" });

const providerOptions = computed(() => [
	{ label: "Sélectionner...", value: "" },
	...providers.value.map((p) => ({ label: `${p.provider_name} (${p.provider_code})`, value: p.name })),
]);

async function openPayDialog() {
	payDialogOpen.value = true;
	if (!providers.value.length) {
		providers.value = await api.value.mobileMoneyProviders();
	}
}

async function submitPayment() {
	if (!payForm.provider || !payForm.phone_number) {
		notifyError(null, "Veuillez choisir un opérateur et un numéro de téléphone.");
		return;
	}
	paying.value = true;
	try {
		await api.value.payInvoice({
			invoice: props.name,
			provider: payForm.provider,
			phone_number: payForm.phone_number,
			amount: payForm.amount || undefined,
		});
		notifySuccess("Paiement initié. Confirmez l'opération sur votre téléphone.");
		payDialogOpen.value = false;
		reload();
	} catch (e) {
		notifyError(e);
	} finally {
		paying.value = false;
	}
}
</script>
