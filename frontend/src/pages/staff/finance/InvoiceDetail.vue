<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else-if="data" class="space-y-6">
		<div class="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<div>
				<h2 class="text-lg font-semibold text-gray-900">{{ data.name }}</h2>
				<p class="text-sm text-gray-500">{{ data.customer_name }} · Échéance : {{ formatDate(data.due_date) }}</p>
			</div>
			<div class="flex items-center gap-4">
				<div class="text-right">
					<p class="text-xs uppercase tracking-wide text-gray-400">Solde dû</p>
					<p class="text-xl font-semibold text-gray-900">{{ formatCurrency(data.outstanding_amount, data.currency) }}</p>
				</div>
				<Button v-if="data.outstanding_amount > 0" variant="solid" theme="green" @click="openPayDialog">
					Enregistrer un paiement
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
				<EmptyState v-if="!data.payment_schedule?.length" icon="calendar" title="Aucun échéancier" />
				<ul v-else class="divide-y divide-gray-100 text-sm">
					<li v-for="(s, i) in data.payment_schedule" :key="i" class="flex justify-between py-2">
						<span>{{ formatDate(s.due_date) }}</span>
						<span>{{ formatCurrency(s.payment_amount, data.currency) }}</span>
					</li>
				</ul>
			</SectionCard>
			<SectionCard title="Paiements reçus">
				<EmptyState v-if="!payments.length" icon="check-circle" title="Aucun paiement enregistré" />
				<ul v-else class="divide-y divide-gray-100 text-sm">
					<li v-for="p in payments" :key="p.name" class="flex justify-between py-2">
						<div>
							<p class="font-medium text-gray-800">{{ formatCurrency(p.allocated_amount, data.currency) }}</p>
							<p class="text-xs text-gray-400">{{ p.mode_of_payment || "—" }} · {{ p.reference_no || "—" }}</p>
						</div>
						<span class="text-gray-500">{{ formatDate(p.posting_date) }}</span>
					</li>
				</ul>
			</SectionCard>
		</div>

		<Dialog v-model="payDialogOpen" :options="{ title: 'Enregistrer un paiement' }">
			<template #body-content>
				<div class="space-y-4">
					<FormControl type="select" label="Mode de paiement" v-model="payForm.mode_of_payment" :options="['Espèces', 'Virement bancaire', 'Chèque']" />
					<FormControl type="number" label="Montant" v-model="payForm.amount" :placeholder="String(data.outstanding_amount)" />
					<FormControl type="text" label="Référence (optionnel)" v-model="payForm.reference_no" />
					<p class="text-xs text-gray-400">Laissez le montant vide pour solder l'intégralité du solde dû.</p>
				</div>
			</template>
			<template #actions>
				<Button variant="solid" theme="green" :loading="paying" class="w-full" @click="submitPayment">Confirmer</Button>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { Button, Dialog, FormControl, LoadingIndicator, call } from "frappe-ui";
import { financeApi } from "@/api";
import { useAsync, notifyError, notifySuccess } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({ name: { type: String, required: true } });

const { data, loading, reload } = useAsync(
	() => call("frappe.client.get", { doctype: "Sales Invoice", name: props.name }),
	{ watchSource: () => props.name }
);
const payments = ref([]);

async function loadPayments() {
	const refs = await call("frappe.client.get_list", {
		doctype: "Payment Entry Reference",
		// "parent" (-> frappe.client.get_list's own `parent_doctype` arg) is
		// required to read a child-table doctype directly - Frappe checks
		// permission on the *parent* doctype for child rows (has_child_permission
		// in frappe/permissions.py), not on the child doctype's own DocPerm rows,
		// which Accountant doesn't have and can't usefully be granted.
		parent: "Payment Entry",
		filters: { reference_doctype: "Sales Invoice", reference_name: props.name, docstatus: 1 },
		fields: ["parent", "allocated_amount"],
		limit_page_length: 20,
	});
	payments.value = await Promise.all(
		refs.map(async (r) => {
			const pe = await call("frappe.client.get_list", {
				doctype: "Payment Entry",
				filters: { name: r.parent },
				fields: ["name", "posting_date", "mode_of_payment", "reference_no"],
				limit_page_length: 1,
			});
			return { ...pe[0], allocated_amount: r.allocated_amount };
		})
	);
}
loadPayments();

const payDialogOpen = ref(false);
const paying = ref(false);
const payForm = reactive({ mode_of_payment: "Espèces", amount: "", reference_no: "" });

function openPayDialog() {
	payForm.amount = "";
	payForm.reference_no = "";
	payDialogOpen.value = true;
}

async function submitPayment() {
	paying.value = true;
	try {
		await financeApi.recordPayment({
			invoice: props.name,
			amount: payForm.amount || undefined,
			mode_of_payment: payForm.mode_of_payment,
			reference_no: payForm.reference_no || undefined,
		});
		notifySuccess("Paiement enregistré.");
		payDialogOpen.value = false;
		reload();
		loadPayments();
	} catch (e) {
		notifyError(e);
	} finally {
		paying.value = false;
	}
}
</script>
