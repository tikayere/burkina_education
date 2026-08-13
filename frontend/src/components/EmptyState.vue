<template>
	<div class="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
		<div class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-400">
			<FeatherIcon :name="icon" class="h-6 w-6" />
		</div>
		<p class="text-sm font-medium text-gray-700">{{ title }}</p>
		<p v-if="description" class="max-w-sm text-sm text-gray-500">{{ description }}</p>
		<slot />
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui";

defineProps({
	icon: { type: String, default: "inbox" },
	title: { type: String, required: true },
	description: { type: String, default: "" },
});
</script>
