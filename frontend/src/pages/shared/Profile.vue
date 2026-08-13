<template>
	<div v-if="loading" class="flex justify-center py-20">
		<LoadingIndicator class="h-6 w-6 text-bf-red-500" />
	</div>
	<div v-else-if="data" class="space-y-6">
		<div class="flex items-center gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
			<Avatar :label="data.student_name" :image="data.image" size="2xl" />
			<div>
				<h2 class="text-lg font-semibold text-gray-900">{{ data.student_name }}</h2>
				<p class="text-sm text-gray-500">{{ data.grade_name }} · {{ data.school_name }}</p>
			</div>
		</div>

		<SectionCard title="Informations personnelles">
			<dl class="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
				<div v-for="f in fields" :key="f.label">
					<dt class="text-xs font-medium uppercase tracking-wide text-gray-400">{{ f.label }}</dt>
					<dd class="mt-0.5 text-sm text-gray-800">{{ f.value || "—" }}</dd>
				</div>
			</dl>
		</SectionCard>

		<SectionCard title="Tuteurs / Parents">
			<EmptyState v-if="!data.guardians?.length" icon="users" title="Aucun tuteur enregistré" />
			<ul v-else class="divide-y divide-gray-100">
				<li v-for="g in data.guardians" :key="g.name" class="flex items-center justify-between py-2.5 text-sm">
					<div>
						<p class="font-medium text-gray-800">{{ g.guardian_name }}</p>
						<p class="text-gray-500">{{ g.relation || "—" }}</p>
					</div>
					<div class="text-right text-gray-500">
						<p>{{ g.mobile_number || "—" }}</p>
						<p>{{ g.email_address || "—" }}</p>
					</div>
				</li>
			</ul>
		</SectionCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { Avatar, LoadingIndicator } from "frappe-ui";
import { selfApi, childApi } from "@/api";
import { useAsync } from "@/composables/useAsync";
import { formatDate } from "@/utils/format";
import SectionCard from "@/components/SectionCard.vue";
import EmptyState from "@/components/EmptyState.vue";

const props = defineProps({ student: { type: String, default: "" } });
const api = computed(() => (props.student ? childApi(props.student) : selfApi()));
const { data, loading } = useAsync(() => api.value.profile(), { watchSource: () => props.student });

const fields = computed(() => {
	if (!data.value) return [];
	const d = data.value;
	return [
		{ label: "Matricule", value: d.matricule },
		{ label: "Statut", value: d.status },
		{ label: "Genre", value: d.gender },
		{ label: "Date de naissance", value: d.date_of_birth ? formatDate(d.date_of_birth) : "" },
		{ label: "E-mail", value: d.student_email_id },
		{ label: "Téléphone", value: d.student_mobile_number },
	];
});
</script>
