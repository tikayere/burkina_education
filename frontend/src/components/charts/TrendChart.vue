<template>
	<div class="relative" @mouseleave="hoverIndex = null">
		<svg
			:viewBox="`0 0 ${W} ${H}`"
			preserveAspectRatio="none"
			class="h-full w-full"
			:style="{ height: `${height}px` }"
			@mousemove="onMouseMove"
		>
			<!-- Recessive gridlines - never a data color (dataviz: marks-and-anatomy). -->
			<line v-for="y in gridLines" :key="y" x1="0" :x2="W" :y1="y" :y2="y" stroke="#e5e7eb" stroke-width="1" />

			<path :d="areaPath" :fill="areaFill" stroke="none" />
			<path :d="linePath" fill="none" :stroke="color" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />

			<!-- Hover crosshair + point (dataviz: interaction - a line chart ships hover by default). -->
			<g v-if="hoverIndex !== null">
				<line :x1="pointX(hoverIndex)" :x2="pointX(hoverIndex)" y1="0" :y2="H" stroke="#9ca3af" stroke-width="1" stroke-dasharray="3 3" />
				<circle :cx="pointX(hoverIndex)" :cy="pointY(hoverIndex)" r="4" :fill="color" stroke="white" stroke-width="1.5" />
			</g>

			<!-- Wide invisible hit target, bigger than the mark (dataviz: interaction). -->
			<rect x="0" y="0" :width="W" :height="H" fill="transparent" />
		</svg>

		<div
			v-if="hoverIndex !== null"
			class="pointer-events-none absolute top-0 -translate-x-1/2 rounded-md border border-gray-100 bg-white px-2.5 py-1.5 text-xs shadow-md"
			:style="{ left: `${Math.min(92, Math.max(8, (pointX(hoverIndex) / W) * 100))}%` }"
		>
			<p class="font-medium text-gray-800">{{ formatValue(values[hoverIndex]) }}</p>
			<p class="text-gray-400">{{ labels[hoverIndex] }}</p>
		</div>

		<div class="mt-1.5 flex justify-between text-[11px] text-gray-400">
			<span v-for="(l, i) in visibleLabels" :key="i">{{ l }}</span>
		</div>
	</div>
</template>

<script setup>
/* Single-series line/area trend (dataviz: choosing-a-form - "change over
 * time" for one measure). One hue, no legend needed (the chart's own title
 * names the series - dataviz §6). Used for things like attendance evolution
 * or monthly fee collections - see docs/architecture.md's dashboard sections.
 */
import { computed, ref } from "vue";
import { BRAND } from "./chartPalette";

const props = defineProps({
	labels: { type: Array, required: true },
	values: { type: Array, required: true },
	color: { type: String, default: BRAND },
	height: { type: Number, default: 180 },
	formatValue: { type: Function, default: (v) => String(v) },
	// Value the area's baseline anchors to (0 for currency/counts, but an
	// attendance-% chart usually reads better anchored near its own min).
	min: { type: Number, default: null },
});

const hoverIndex = ref(null);
const W = 600;
const H = props.height;
const PAD = 6;

const range = computed(() => {
	const vals = props.values.length ? props.values : [0];
	const max = Math.max(...vals, 1);
	const min = props.min !== null ? props.min : Math.min(0, ...vals);
	return { min, max: max === min ? min + 1 : max };
});

function pointX(i) {
	const n = props.values.length;
	if (n <= 1) return W / 2;
	return (i / (n - 1)) * W;
}
function pointY(i) {
	const { min, max } = range.value;
	const v = props.values[i] ?? min;
	const t = (v - min) / (max - min);
	return H - PAD - t * (H - PAD * 2);
}

const linePath = computed(() =>
	props.values.map((_, i) => `${i === 0 ? "M" : "L"} ${pointX(i).toFixed(1)} ${pointY(i).toFixed(1)}`).join(" ")
);
const areaPath = computed(() => {
	if (!props.values.length) return "";
	const last = props.values.length - 1;
	return `${linePath.value} L ${pointX(last).toFixed(1)} ${H} L ${pointX(0).toFixed(1)} ${H} Z`;
});
const areaFill = computed(() => `${props.color}1f`); // ~12% opacity fill, matches dataviz's soft-area guidance

const gridLines = computed(() => [0.25, 0.5, 0.75].map((t) => H * t));

// Labels: show a handful (first/mid/last-ish) rather than one per point,
// which crowds on a 12-month series (dataviz: selective direct labels).
const visibleLabels = computed(() => {
	const n = props.labels.length;
	if (n <= 6) return props.labels;
	const step = Math.ceil(n / 6);
	return props.labels.filter((_, i) => i % step === 0 || i === n - 1);
});

function onMouseMove(e) {
	const rect = e.currentTarget.getBoundingClientRect();
	const ratio = (e.clientX - rect.left) / rect.width;
	const n = props.values.length;
	if (!n) return;
	hoverIndex.value = Math.min(n - 1, Math.max(0, Math.round(ratio * (n - 1))));
}
</script>
