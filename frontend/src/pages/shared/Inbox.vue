<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-green-500" />
	</div>
	<SectionCard v-else title="Messages" subtitle="Notifications reçues (paiements, résultats, rappels, annonces...)." no-padding>
		<EmptyState v-if="!data.length" icon="mail" title="Aucun message" />
		<ul v-else class="divide-y divide-gray-100">
			<li v-for="m in data" :key="m.name" class="p-5">
				<div class="flex items-center justify-between">
					<h3 class="text-sm font-semibold text-gray-900">{{ m.subject || eventLabel(m.event_key) }}</h3>
					<span class="text-xs text-gray-400">{{ formatDateTime(m.queued_on) }}</span>
				</div>
				<p class="mt-1 text-sm text-gray-600">{{ m.message }}</p>
			</li>
		</ul>
	</SectionCard>
</template>

<script setup>
import { useRoute } from "vue-router";
import { LoadingIndicator } from "frappe-ui";
import { studentApi, guardianApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDateTime } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

// Shared by both "student-messages" and "guardian-messages" (router.js) - a
// multi-role user can hold both at once, so which API to call has to come
// from *this route*, not a global "current portal" (docs/architecture.md
// section N).
const route = useRoute();
const fetcher = route.meta?.portal === "guardian" ? () => guardianApi.inbox({ limit: 50 }) : () => studentApi.inbox({ limit: 50 });
const { data, loading } = useAsync(fetcher, { initial: [] });

const LABELS = {
	"Absence Notification": "Notification d'absence",
	"Payment Confirmation": "Confirmation de paiement",
	"Fee Reminder": "Rappel de frais",
	"Result Available": "Résultats disponibles",
	"School Announcement": "Annonce de l'école",
	"Emergency Message": "Message urgent",
	"Parent Meeting": "Réunion de parents",
	"Timetable Change": "Changement d'emploi du temps",
	"Library Book Overdue": "Retard de livre",
	Other: "Message",
};
function eventLabel(key) {
	return LABELS[key] || key;
}
</script>
