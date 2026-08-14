<template>
	<Dialog v-model="open" :options="{ title, size: size }">
		<template #body-content>
			<div class="space-y-4">
				<DynamicField
					v-for="f in fields"
					:key="f.fieldname"
					:field="f"
					:model-value="form[f.fieldname]"
					@update:model-value="(v) => (form[f.fieldname] = v)"
				/>
			</div>
		</template>
		<template #actions>
			<Button variant="solid" theme="green" class="w-full" :loading="saving" @click="save">
				{{ record ? "Enregistrer" : "Créer" }}
			</Button>
		</template>
	</Dialog>
</template>

<script setup>
/* Generic create/edit dialog for the plain-CRUD doctypes the staff portals
 * expose directly (docs/architecture.md section M) - a Librarian's Library
 * Author, a Boarding Manager's Boarding Room, ... Talks straight to Frappe's
 * own whitelisted `frappe.client.insert`/`set_value` (permission-checked
 * exactly like Desk), the same way frappe-ui's own createDocumentResource
 * does - no bespoke Python endpoint per doctype (see api.js).
 */
import { computed, reactive, ref, watch } from "vue";
import { Button, Dialog, call } from "frappe-ui";
import { notifyError, notifySuccess } from "@/composables/useAsync";
import DynamicField from "@/components/resource/DynamicField.vue";

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	doctype: { type: String, required: true },
	title: { type: String, required: true },
	fields: { type: Array, required: true },
	record: { type: Object, default: null }, // null => create
	defaults: { type: Object, default: () => ({}) },
	size: { type: String, default: "md" },
});
const emit = defineEmits(["update:modelValue", "saved"]);

const open = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
});

const saving = ref(false);
const form = reactive({});

function resetForm() {
	for (const key of Object.keys(form)) delete form[key];
	const source = props.record || props.defaults;
	for (const f of props.fields) {
		form[f.fieldname] = source?.[f.fieldname] ?? (f.type === "Check" ? 0 : "");
	}
}

watch(() => [props.modelValue, props.record], resetForm, { immediate: true });

async function save() {
	for (const f of props.fields) {
		if (f.required && !form[f.fieldname] && form[f.fieldname] !== 0) {
			notifyError(null, `Le champ « ${f.label} » est obligatoire.`);
			return;
		}
	}

	saving.value = true;
	try {
		if (props.record) {
			await call("frappe.client.set_value", {
				doctype: props.doctype,
				name: props.record.name,
				fieldname: { ...form },
			});
			notifySuccess("Modifications enregistrées.");
		} else {
			await call("frappe.client.insert", { doc: { doctype: props.doctype, ...form } });
			notifySuccess("Créé avec succès.");
		}
		open.value = false;
		emit("saved");
	} catch (e) {
		notifyError(e);
	} finally {
		saving.value = false;
	}
}
</script>
