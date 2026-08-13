<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<EmptyState v-if="!data.children.length" icon="users" title="Aucun élève associé à ce compte" />
		<div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			<router-link
				v-for="c in data.children"
				:key="c.name"
				:to="{ name: 'child-overview', params: { student: c.name } }"
				class="group rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition hover:border-bf-red-200 hover:shadow-md"
			>
				<div class="flex items-center gap-3">
					<Avatar :label="c.student_name" :image="c.image" size="xl" />
					<div class="min-w-0">
						<h3 class="truncate font-semibold text-gray-900 group-hover:text-bf-red-600">{{ c.student_name }}</h3>
						<p class="text-sm text-gray-500">{{ c.grade_name || "—" }}</p>
					</div>
				</div>
				<div class="mt-4 grid grid-cols-2 gap-3 text-sm">
					<div>
						<p class="text-xs uppercase tracking-wide text-gray-400">Présence</p>
						<p class="font-medium text-gray-800">{{ c.attendance_percentage }}%</p>
					</div>
					<div>
						<p class="text-xs uppercase tracking-wide text-gray-400">Solde</p>
						<p class="font-medium" :class="c.outstanding_balance > 0 ? 'text-bf-red-600' : 'text-bf-green-600'">
							{{ formatCurrency(c.outstanding_balance) }}
						</p>
					</div>
				</div>
				<div v-if="c.latest_term_report" class="mt-3 border-t border-gray-100 pt-3 text-sm text-gray-500">
					Dernière moyenne : <span class="font-medium text-gray-800">{{ c.latest_term_report.term_average }}</span>
				</div>
			</router-link>
		</div>

		<SectionCard title="Annonces récentes" no-padding>
			<EmptyState v-if="!data.announcements.length" icon="bell" title="Aucune annonce" />
			<ul v-else class="divide-y divide-gray-100">
				<li v-for="a in data.announcements" :key="a.name" class="flex items-center justify-between px-5 py-3">
					<div class="flex items-center gap-2">
						<StatusBadge :text="a.priority" :tone="a.priority === 'Urgente' ? 'red' : a.priority === 'Élevée' ? 'gold' : 'gray'" />
						<p class="text-sm font-medium text-gray-800">{{ a.title }}</p>
					</div>
					<span class="text-xs text-gray-400">{{ formatDate(a.published_on) }}</span>
				</li>
			</ul>
		</SectionCard>
	</div>
</template>

<script setup>
import { Avatar, LoadingIndicator } from "frappe-ui";
import { guardianApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatCurrency, formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const { data, loading } = useAsync(() => guardianApi.dashboard(), { initial: { children: [], announcements: [] } });
</script>
