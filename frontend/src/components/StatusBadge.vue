<template>
	<span class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium" :class="classes">
		<span class="h-1.5 w-1.5 rounded-full" :class="dotClasses" />
		{{ text }}
	</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	text: { type: String, required: true },
	tone: { type: String, default: "gray" }, // green | red | gold | gray | blue
});

const palette = {
	green: { bg: "bg-bf-green-50", text: "text-bf-green-600", dot: "bg-bf-green-500" },
	red: { bg: "bg-bf-red-50", text: "text-bf-red-600", dot: "bg-bf-red-500" },
	gold: { bg: "bg-bf-gold-50", text: "text-yellow-700", dot: "bg-bf-gold-500" },
	blue: { bg: "bg-blue-50", text: "text-blue-600", dot: "bg-blue-500" },
	gray: { bg: "bg-gray-100", text: "text-gray-600", dot: "bg-gray-400" },
};

const classes = computed(() => `${palette[props.tone].bg} ${palette[props.tone].text}`);
const dotClasses = computed(() => palette[props.tone].dot);
</script>
