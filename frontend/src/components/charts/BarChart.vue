<template>
	<div class="flex items-end gap-3 overflow-x-auto pb-1" :style="{ height: `${height}px` }">
		<div
			v-for="(d, i) in data"
			:key="d.label"
			class="group flex h-full min-w-[2.5rem] flex-1 flex-col items-center justify-end gap-1.5"
		>
			<p class="text-xs font-medium text-gray-700 opacity-0 transition group-hover:opacity-100">
				{{ formatValue(d.value) }}
			</p>
			<div class="relative flex w-full flex-1 items-end justify-center">
				<div
					class="w-full max-w-[2.25rem] rounded-t-md transition-[height] duration-300"
					:style="{ height: `${barHeight(d.value)}%`, backgroundColor: d.color || categoricalColor(i) }"
				/>
			</div>
			<p class="line-clamp-2 max-w-[4.5rem] text-center text-[11px] leading-tight text-gray-500">{{ d.label }}</p>
		</div>
	</div>
</template>

<script setup>
/* Vertical bar comparison across categories (dataviz: choosing-a-form -
 * "magnitude across categories"). Each bar is direct-labeled on the x-axis
 * (its category name) so no legend box is needed; the value itself only
 * appears on hover to keep the resting state uncluttered, per the
 * skill's "selective direct labels, never a number on every point" rule.
 */
import { categoricalColor } from "./chartPalette";

const props = defineProps({
	// [{ label, value, color? }]
	data: { type: Array, required: true },
	height: { type: Number, default: 180 },
	formatValue: { type: Function, default: (v) => String(v) },
});

const max = () => Math.max(...props.data.map((d) => d.value), 1);

function barHeight(value) {
	return Math.max(3, (value / max()) * 100);
}
</script>
