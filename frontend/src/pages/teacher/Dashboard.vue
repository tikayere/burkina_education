<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="space-y-6">
		<div class="flex items-center gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<Avatar :label="data.instructor.instructor_name" :image="data.instructor.image" size="2xl" />
			<div>
				<h2 class="text-lg font-semibold text-gray-900">{{ data.instructor.instructor_name }}</h2>
				<p class="text-sm text-gray-500">
					{{ data.instructor.department || "—" }}
					<StatusBadge v-if="data.is_class_teacher" text="Professeur principal" tone="gold" class="ml-2" />
				</p>
			</div>
		</div>

		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<StatCard label="Classes" :value="data.groups_count" icon="users" tone="red" />
			<StatCard label="Élèves" :value="data.students_count" icon="user" tone="gray" />
			<StatCard label="Cours aujourd'hui" :value="data.today_schedule.length" icon="calendar" tone="gold" />
			<StatCard
				v-if="data.is_class_teacher"
				label="Discipline ouverte"
				:value="data.open_discipline_cases"
				icon="shield"
				:tone="data.open_discipline_cases > 0 ? 'red' : 'green'"
			/>
		</div>

		<div class="grid gap-6 lg:grid-cols-2">
			<SectionCard title="Aujourd'hui">
				<EmptyState v-if="!data.today_schedule.length" icon="calendar" title="Aucun cours aujourd'hui" />
				<ul v-else class="divide-y divide-gray-100">
					<li v-for="s in data.today_schedule" :key="s.name" class="flex items-center justify-between py-2.5 text-sm">
						<div>
							<p class="font-medium text-gray-800">{{ s.course }}</p>
							<p class="text-gray-500">{{ s.student_group }} · Salle {{ s.room || "—" }}</p>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-gray-500">{{ formatTime(s.from_time) }} - {{ formatTime(s.to_time) }}</span>
							<router-link
								:to="{ name: 'teacher-attendance', params: { group: s.student_group } }"
								class="text-bf-red-600 hover:underline"
							>
								Appel
							</router-link>
						</div>
					</li>
				</ul>
			</SectionCard>

			<SectionCard title="Annonces récentes">
				<EmptyState v-if="!data.announcements.length" icon="bell" title="Aucune annonce" />
				<ul v-else class="divide-y divide-gray-100">
					<li v-for="a in data.announcements" :key="a.name" class="py-2.5">
						<p class="text-sm font-medium text-gray-800">{{ a.title }}</p>
						<p class="mt-0.5 text-xs text-gray-500">{{ formatDate(a.published_on) }}</p>
					</li>
				</ul>
			</SectionCard>
		</div>
	</div>
</template>

<script setup>
import { Avatar, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate, formatTime } from "@/utils/format";
import StatCard from "@/components/StatCard.vue";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const { data, loading } = useAsync(() => teacherApi.dashboard(), {
	initial: { instructor: {}, today_schedule: [], announcements: [], groups_count: 0, students_count: 0, open_discipline_cases: 0 },
});
</script>
