<template>
	<div class="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
		<div class="flex items-start justify-between">
			<div>
				<p class="text-sm text-gray-500">{{ label }}</p>
				<p class="mt-1 text-2xl font-semibold text-gray-900">{{ value }}</p>
				<p v-if="hint" class="mt-0.5 text-xs text-gray-400">{{ hint }}</p>
			</div>
			<div
				v-if="icon"
				class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
				:class="toneClasses"
			>
				<FeatherIcon :name="icon" class="h-5 w-5" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
	label: { type: String, required: true },
	value: { type: [String, Number], required: true },
	hint: { type: String, default: "" },
	icon: { type: String, default: "" },
	tone: { type: String, default: "red" }, // red | green | gold | gray
});

const toneClasses = computed(() => {
	return {
		red: "bg-bf-red-50 text-bf-red-600",
		green: "bg-bf-green-50 text-bf-green-600",
		gold: "bg-bf-gold-50 text-yellow-700",
		gray: "bg-gray-100 text-gray-600",
	}[props.tone];
});
</script>
