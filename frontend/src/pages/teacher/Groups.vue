<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		<EmptyState v-if="!data.length" icon="users" class="col-span-full" title="Aucune classe assignée" />
		<router-link
			v-for="g in data"
			:key="g.name"
			:to="{ name: 'teacher-group-detail', params: { group: g.name } }"
			class="group rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition hover:border-bf-red-200 hover:shadow-md"
		>
			<div class="flex items-center justify-between">
				<h3 class="font-semibold text-gray-900 group-hover:text-bf-red-600">{{ g.student_group_name }}</h3>
				<StatusBadge v-if="g.disabled" text="Inactive" tone="gray" />
			</div>
			<p class="mt-1 text-sm text-gray-500">{{ g.grade_name || "—" }} · {{ g.academic_year }}</p>
			<div class="mt-3 flex items-center gap-1.5 text-sm text-gray-600">
				<FeatherIcon name="users" class="h-4 w-4" />
				{{ g.student_count }} élève(s)
			</div>
		</router-link>
	</div>
</template>

<script setup>
import { FeatherIcon, LoadingIndicator } from "frappe-ui";
import { teacherApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

const { data, loading } = useAsync(() => teacherApi.groups(), { initial: [] });
</script>
