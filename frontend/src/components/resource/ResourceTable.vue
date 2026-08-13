<template>
	<table class="w-full text-sm">
		<thead class="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
			<tr>
				<th v-for="c in columns" :key="c.fieldname" class="px-5 py-3">{{ c.label }}</th>
				<th v-if="$slots.actions" class="px-5 py-3 text-right">Actions</th>
			</tr>
		</thead>
		<tbody class="divide-y divide-gray-100">
			<tr
				v-for="row in rows"
				:key="row.name"
				class="transition"
				:class="onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''"
				@click="onRowClick && onRowClick(row)"
			>
				<td v-for="c in columns" :key="c.fieldname" class="px-5 py-3" :class="c.class">
					<StatusBadge v-if="c.format === 'badge'" :text="row[c.fieldname]" :tone="c.tone ? c.tone(row) : 'gray'" />
					<span v-else-if="c.format === 'currency'" class="tabular-nums">{{ formatCurrency(row[c.fieldname]) }}</span>
					<span v-else-if="c.format === 'date'">{{ formatDate(row[c.fieldname]) }}</span>
					<span v-else-if="c.format === 'datetime'">{{ formatDateTime(row[c.fieldname]) }}</span>
					<span v-else-if="c.format === 'check'">
						<FeatherIcon :name="row[c.fieldname] ? 'check-circle' : 'circle'" class="h-4 w-4" :class="row[c.fieldname] ? 'text-bf-green-500' : 'text-gray-300'" />
					</span>
					<span v-else :class="c.emphasize ? 'font-medium text-gray-800' : 'text-gray-600'">
						{{ c.render ? c.render(row) : (row[c.fieldname] ?? "—") }}
					</span>
				</td>
				<td v-if="$slots.actions" class="px-5 py-3 text-right" @click.stop>
					<slot name="actions" :row="row" />
				</td>
			</tr>
		</tbody>
	</table>
</template>

<script setup>
/* Generic list rendering for the staff portals' plain-CRUD resources
 * (docs/architecture.md section M) - columns are declarative
 * ({ fieldname, label, format?, tone?, render? }), matching the by-hand
 * table markup every Student/Guardian/Teacher portal page already uses
 * (see pages/shared/Library.vue) so this doesn't introduce a visually
 * different table style, just avoids repeating the <table> boilerplate
 * once per doctype.
 */
import { FeatherIcon } from "frappe-ui";
import StatusBadge from "@/components/StatusBadge.vue";
import { formatCurrency, formatDate, formatDateTime } from "@/utils/format";

defineProps({
	columns: { type: Array, required: true },
	rows: { type: Array, required: true },
	onRowClick: { type: Function, default: null },
});
</script>
