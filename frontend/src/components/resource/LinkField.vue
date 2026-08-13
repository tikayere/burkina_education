<template>
	<div class="space-y-1.5">
		<label v-if="label" class="block text-xs text-gray-500">{{ label }}<span v-if="required" class="text-bf-red-500"> *</span></label>
		<Autocomplete
			:options="options"
			:model-value="modelValue ? { label: displayLabel || modelValue, value: modelValue } : null"
			:loading="loading"
			placeholder="Rechercher..."
			@update:query="onQuery"
			@update:model-value="(v) => emit('update:modelValue', v?.value || '')"
		/>
	</div>
</template>

<script setup>
/* A Link field the rest of the app's generic forms (ResourceFormDialog) use
 * for any "Link" doctype field - frappe-ui ships Autocomplete (a plain
 * static-options combobox) but no server-search-as-you-type Link control of
 * its own, so this is the one small piece of new reusable infrastructure
 * the staff portals (docs/architecture.md section M) needed on top of it.
 * Search is server-side (frappe.client.get_list, permission-checked exactly
 * like any other list read) rather than loading every row of what could be
 * a large doctype (Student, Sales Invoice, ...) up front.
 */
import { ref, watch } from "vue";
import { Autocomplete, call } from "frappe-ui";

const props = defineProps({
	modelValue: { type: String, default: "" },
	label: { type: String, default: "" },
	doctype: { type: String, required: true },
	searchField: { type: String, default: "name" },
	filters: { type: Object, default: () => ({}) },
	required: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const options = ref([]);
const loading = ref(false);
const displayLabel = ref("");
let debounceHandle = null;

async function search(query) {
	loading.value = true;
	try {
		const filters = { ...props.filters };
		if (query) filters[props.searchField] = ["like", `%${query}%`];
		const rows = await call("frappe.client.get_list", {
			doctype: props.doctype,
			filters,
			fields: ["name", props.searchField],
			limit_page_length: 20,
			order_by: `${props.searchField} asc`,
		});
		options.value = rows.map((r) => ({ label: r[props.searchField] || r.name, value: r.name }));
	} finally {
		loading.value = false;
	}
}

function onQuery(query) {
	clearTimeout(debounceHandle);
	debounceHandle = setTimeout(() => search(query), 250);
}

async function resolveLabel() {
	if (!props.modelValue) {
		displayLabel.value = "";
		return;
	}
	const cached = options.value.find((o) => o.value === props.modelValue);
	if (cached) {
		displayLabel.value = cached.label;
		return;
	}
	const rows = await call("frappe.client.get_list", {
		doctype: props.doctype,
		filters: { name: props.modelValue },
		fields: ["name", props.searchField],
		limit_page_length: 1,
	});
	displayLabel.value = rows[0]?.[props.searchField] || props.modelValue;
}

watch(() => props.modelValue, resolveLabel, { immediate: true });
search("");
</script>
