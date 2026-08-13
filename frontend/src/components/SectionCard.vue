<template>
	<section class="rounded-xl border border-gray-100 bg-white shadow-sm">
		<header v-if="title || $slots.actions" class="flex items-center justify-between border-b border-gray-100 px-5 py-4">
			<div>
				<h2 class="text-base font-semibold text-gray-900">{{ title }}</h2>
				<p v-if="subtitle" class="text-sm text-gray-500">{{ subtitle }}</p>
			</div>
			<div v-if="$slots.actions" class="flex items-center gap-2">
				<slot name="actions" />
			</div>
		</header>
		<div :class="noPadding ? '' : 'p-5'">
			<slot />
		</div>
	</section>
</template>

<script setup>
defineProps({
	title: { type: String, default: "" },
	subtitle: { type: String, default: "" },
	noPadding: { type: Boolean, default: false },
});
</script>
