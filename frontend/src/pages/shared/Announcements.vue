<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<SectionCard v-else title="Annonces" no-padding>
		<EmptyState v-if="!data.length" icon="bell" title="Aucune annonce" />
		<ul v-else class="divide-y divide-gray-100">
			<li v-for="a in data" :key="a.name" class="p-5">
				<div class="flex items-center justify-between">
					<h3 class="text-sm font-semibold text-gray-900">{{ a.title }}</h3>
					<div class="flex items-center gap-2">
						<span class="text-xs text-gray-400">{{ formatDate(a.published_on) }}</span>
						<StatusBadge :text="a.priority" :tone="a.priority === 'Urgente' ? 'red' : a.priority === 'Élevée' ? 'gold' : 'gray'" />
					</div>
				</div>
				<div class="prose prose-sm mt-2 max-w-none text-gray-600" v-html="a.content" />
			</li>
		</ul>
	</SectionCard>
</template>

<script setup>
import { useRoute } from "vue-router";
import { LoadingIndicator } from "frappe-ui";
import { studentApi, teacherApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";
import StatusBadge from "@/components/StatusBadge.vue";

// Shared by both "student-announcements" and "teacher-announcements"
// (router.js) - which API to call has to come from *this route*, not a
// global "current portal", since a multi-role user can hold both at once
// (docs/architecture.md section N).
const route = useRoute();
const fetcher = route.meta?.portal === "teacher" ? () => teacherApi.announcements({ limit: 30 }) : () => studentApi.announcements({ limit: 30 });
const { data, loading } = useAsync(fetcher, { initial: [] });
</script>
