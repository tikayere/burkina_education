<template>
	<LinkField
		v-if="field.type === 'Link'"
		:model-value="modelValue"
		:label="field.label"
		:doctype="field.doctype"
		:search-field="field.searchField || 'name'"
		:filters="field.filters || {}"
		:required="field.required"
		@update:model-value="(v) => emit('update:modelValue', v)"
	/>
	<FormControl
		v-else-if="field.type === 'Select'"
		type="select"
		:label="field.label"
		:options="selectOptions"
		:model-value="modelValue ?? ''"
		:required="field.required"
		@update:model-value="(v) => emit('update:modelValue', v)"
	/>
	<FormControl
		v-else-if="field.type === 'Check'"
		type="checkbox"
		:label="field.label"
		:model-value="!!modelValue"
		@update:model-value="(v) => emit('update:modelValue', v ? 1 : 0)"
	/>
	<FormControl
		v-else-if="['Small Text', 'Text', 'Long Text', 'Text Editor', 'Code'].includes(field.type)"
		type="textarea"
		:label="field.label"
		:model-value="modelValue ?? ''"
		:required="field.required"
		@update:model-value="(v) => emit('update:modelValue', v)"
	/>
	<FormControl
		v-else
		:type="nativeInputType"
		:label="field.label"
		:model-value="modelValue ?? ''"
		:required="field.required"
		:step="['Float', 'Currency', 'Percent'].includes(field.type) ? 'any' : undefined"
		@update:model-value="(v) => emit('update:modelValue', v)"
	/>
</template>

<script setup>
/* Renders the right control for one field descriptor
 * ({ fieldname, label, type, doctype, options, required }) - the building
 * block ResourceFormDialog.vue loops over. `type` mirrors Frappe fieldtypes
 * (Data/Select/Link/Int/Float/Currency/Percent/Date/Time/Datetime/Check/
 * Small Text) narrowed to the ones the staff portals' doctypes actually use
 * (docs/architecture.md section M) - not a full DocType-meta-driven form
 * builder, just enough to avoid a bespoke <template> per doctype.
 */
import { computed } from "vue";
import { FormControl } from "frappe-ui";
import LinkField from "@/components/resource/LinkField.vue";

const props = defineProps({
	field: { type: Object, required: true },
	modelValue: { type: [String, Number, Boolean], default: "" },
});
const emit = defineEmits(["update:modelValue"]);

const selectOptions = computed(() =>
	(props.field.options || []).map((o) => (typeof o === "string" ? { label: o, value: o } : o))
);

const nativeInputType = computed(() => {
	return (
		{
			Int: "number",
			Float: "number",
			Currency: "number",
			Percent: "number",
			Date: "date",
			Time: "time",
			Datetime: "datetime-local",
		}[props.field.type] || "text"
	);
});
</script>
