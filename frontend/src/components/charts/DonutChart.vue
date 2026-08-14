<template>
	<div class="flex items-center gap-5">
		<svg viewBox="0 0 100 100" class="h-28 w-28 shrink-0 -rotate-90">
			<circle cx="50" cy="50" r="40" fill="none" stroke="#f3f4f6" stroke-width="14" />
			<circle
				v-for="(seg, i) in segments"
				:key="seg.label"
				cx="50"
				cy="50"
				r="40"
				fill="none"
				:stroke="seg.color"
				stroke-width="14"
				:stroke-dasharray="`${seg.length} ${CIRCUMFERENCE - seg.length}`"
				:stroke-dashoffset="-seg.offset"
				stroke-linecap="butt"
			>
				<title>{{ seg.label }} — {{ formatValue(seg.value) }} ({{ seg.percent }}%)</title>
			</circle>
		</svg>

		<ul class="min-w-0 flex-1 space-y-1.5 text-sm">
			<li v-for="seg in segments" :key="seg.label" class="flex items-center gap-2">
				<span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ backgroundColor: seg.color }" />
				<span class="min-w-0 flex-1 truncate text-gray-600">{{ seg.label }}</span>
				<span class="shrink-0 font-medium text-gray-800">{{ seg.percent }}%</span>
			</li>
		</ul>
	</div>
</template>

<script setup>
/* Proportion-of-whole donut (dataviz: choosing-a-form - "share of total"
 * across a handful of categories, e.g. boarding-bed occupancy or fee status
 * split). A legend is always present for >=2 series and doubles as the
 * value readout - each ring segment also carries a native tooltip so hover
 * still surfaces the exact figure (dataviz: interaction - hover by default).
 */
import { computed } from "vue";
import { categoricalColor } from "./chartPalette";

const props = defineProps({
	// [{ label, value, color? }]
	data: { type: Array, required: true },
	formatValue: { type: Function, default: (v) => String(v) },
});

const CIRCUMFERENCE = 2 * Math.PI * 40;

const segments = computed(() => {
	const total = props.data.reduce((sum, d) => sum + d.value, 0) || 1;
	let offset = 0;
	return props.data.map((d, i) => {
		const length = (d.value / total) * CIRCUMFERENCE;
		const seg = {
			...d,
			color: d.color || categoricalColor(i),
			length,
			offset,
			percent: Math.round((d.value / total) * 100),
		};
		offset += length;
		return seg;
	});
});
</script>
