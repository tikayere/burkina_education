<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<div v-else-if="error" class="rounded-lg bg-bf-red-50 p-4 text-sm text-bf-red-600">{{ error }}</div>
	<div v-else-if="data" class="space-y-6">
		<!-- Identity header -->
		<div class="flex flex-col gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
			<div class="flex items-center gap-4">
				<Avatar :label="data.student.student_name" :image="imageUrl(data.student.image)" size="2xl" />
				<div>
					<h2 class="text-lg font-semibold text-gray-900">{{ data.student.student_name }}</h2>
					<p class="text-sm text-gray-500">
						{{ data.student.grade_name || "—" }}
						<span v-if="data.student.matricule"> · {{ data.student.matricule }}</span>
					</p>
				</div>
			</div>
			<StatusBadge :text="data.student.status" :tone="data.student.status === 'Active' ? 'green' : 'gray'" />
		</div>

		<!-- KPI cards -->
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
			<StatCard
				label="Présence (30j)"
				:value="`${data.attendance.last_30_days.percentage}%`"
				icon="check-square"
				:tone="data.attendance.last_30_days.percentage >= 90 ? 'green' : 'gold'"
			/>
			<StatCard
				label="Solde dû"
				:value="formatCurrency(data.outstanding_balance)"
				icon="credit-card"
				:tone="data.outstanding_balance > 0 ? 'red' : 'green'"
			/>
			<StatCard
				label="Dernière moyenne"
				:value="data.latest_term_report ? data.latest_term_report.term_average : '—'"
				:hint="data.latest_term_report ? `sur ${data.latest_term_report.max_average}` : ''"
				icon="award"
				tone="gold"
			/>
			<StatCard label="Livres empruntés" :value="data.open_library_loans" icon="book-open" tone="gray" />
			<StatCard
				label="Discipline"
				:value="data.discipline_open"
				hint="dossier(s) ouvert(s)"
				icon="shield"
				:tone="data.discipline_open > 0 ? 'red' : 'green'"
			/>
		</div>

		<SectionCard title="Évolution des présences" subtitle="6 derniers mois">
			<EmptyState v-if="!hasAttendanceTrend" icon="trending-up" title="Pas encore de présence enregistrée" />
			<TrendChart
				v-else
				:labels="trendLabels"
				:values="trendValues"
				:format-value="(v) => (v === null ? '—' : `${v}%`)"
				:min="0"
				:height="180"
			/>
		</SectionCard>

		<div class="grid gap-6 lg:grid-cols-2">
			<SectionCard title="Prochains cours">
				<EmptyState v-if="!data.upcoming_schedule.length" icon="calendar" title="Aucun cours planifié" />
				<ul v-else class="divide-y divide-gray-100">
					<li v-for="s in data.upcoming_schedule" :key="s.name" class="flex items-center justify-between py-2.5 text-sm">
						<div>
							<p class="font-medium text-gray-800">{{ s.course }}</p>
							<p class="text-gray-500">{{ s.instructor_name }} · {{ s.room || "—" }}</p>
						</div>
						<div class="text-right text-gray-500">
							<p>{{ relativeDay(s.schedule_date) }}</p>
							<p>{{ formatTime(s.from_time) }} - {{ formatTime(s.to_time) }}</p>
						</div>
					</li>
				</ul>
			</SectionCard>

			<SectionCard title="Annonces récentes">
				<EmptyState v-if="!data.announcements.length" icon="bell" title="Aucune annonce" />
				<ul v-else class="divide-y divide-gray-100">
					<li v-for="a in data.announcements" :key="a.name" class="py-2.5">
						<div class="flex items-center gap-2">
							<StatusBadge
								:text="a.priority"
								:tone="a.priority === 'Urgente' ? 'red' : a.priority === 'Élevée' ? 'gold' : 'gray'"
							/>
							<p class="text-sm font-medium text-gray-800">{{ a.title }}</p>
						</div>
						<p class="mt-1 text-xs text-gray-500">{{ formatDate(a.published_on) }}</p>
					</li>
				</ul>
			</SectionCard>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { Avatar, LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatCurrency, formatDate, formatTime, relativeDay } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import TrendChart from "@/components/charts/TrendChart.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading, error } = useAsync(() => api.value.overview(), { watchSource: () => props.student });

function imageUrl(image) {
	return image || null;
}

// Months before the student's first ever attendance record come back with
// `percentage: null` (common.py::attendance_monthly_trend) - dropped from the
// front of the series rather than charted as 0%, which would misread as "no
// attendance" instead of "not enrolled/no data yet".
const attendanceTrend = computed(() => {
	const rows = data.value?.attendance?.monthly_trend || [];
	const firstWithData = rows.findIndex((r) => r.percentage !== null);
	return firstWithData === -1 ? [] : rows.slice(firstWithData);
});
const hasAttendanceTrend = computed(() => attendanceTrend.value.length > 0);
const trendLabels = computed(() => attendanceTrend.value.map((r) => r.label));
const trendValues = computed(() => attendanceTrend.value.map((r) => r.percentage ?? 0));
</script>
