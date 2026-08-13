<template>
	<div class="flex h-full flex-col">
		<div class="flex items-center gap-2 border-b border-gray-100 px-5 py-5">
			<img
				:src="logoUrl"
				class="h-8 w-8"
				@error="(e) => (e.target.style.display = 'none')"
			/>
			<div>
				<p class="text-sm font-semibold leading-tight text-gray-900">Burkina Éducation</p>
				<p class="text-xs leading-tight text-gray-500">{{ portalLabel }}</p>
			</div>
		</div>

		<router-link
			v-if="session.portal === 'guardian' && route.params.student"
			:to="{ name: 'guardian-dashboard' }"
			class="mx-3 mt-3 flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-100"
			@click="$emit('navigate')"
		>
			<FeatherIcon name="arrow-left" class="h-3.5 w-3.5" />
			Mes enfants
		</router-link>

		<nav class="flex-1 space-y-0.5 overflow-y-auto px-3 py-3">
			<router-link
				v-for="item in navItems"
				:key="item.label"
				:to="item.to"
				class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900"
				active-class="!bg-bf-red-50 !text-bf-red-600"
				@click="$emit('navigate')"
			>
				<FeatherIcon :name="item.icon" class="h-4 w-4" />
				{{ item.label }}
			</router-link>
		</nav>

		<div class="border-t border-gray-100 px-5 py-3 text-xs text-gray-400">École Pilote Burkina</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { FeatherIcon } from "frappe-ui";
import { session, portalLabel } from "@/session";
import {
	studentNav,
	guardianNav,
	childNav,
	teacherNav,
	librarianNav,
	transportNav,
	canteenNav,
	boardingNav,
	clinicNav,
	financeNav,
	academicNav,
	commsNav,
	leadershipNav,
} from "@/navigation";

defineEmits(["navigate"]);
const route = useRoute();
const logoUrl = "/assets/burkina_education/images/logo.svg";

// Academic portal nav is role-aware (Registrar/Examination Coordinator only
// see their own slice, Academic Director sees everything - see
// portal/roles/academic_api.py) - derived straight from session.roles
// rather than waiting on the dashboard's own API call, so the sidebar is
// correct on first paint.
const academicFlags = computed(() => ({
	isDirector: session.roles.includes("Academic Director"),
	hasStructure: session.roles.includes("Academic Director") || session.roles.includes("Registrar"),
	hasExams: session.roles.includes("Academic Director") || session.roles.includes("Examination Coordinator"),
}));

const navItems = computed(() => {
	if (session.portal === "guardian" && route.params.student) {
		return childNav(route.params.student);
	}
	switch (session.portal) {
		case "guardian":
			return guardianNav;
		case "teacher":
			return teacherNav(session.isClassTeacher);
		case "librarian":
			return librarianNav;
		case "transport":
			return transportNav;
		case "canteen":
			return canteenNav;
		case "boarding":
			return boardingNav;
		case "clinic":
			return clinicNav;
		case "finance":
			return financeNav;
		case "academic":
			return academicNav(academicFlags.value);
		case "comms":
			return commsNav;
		case "leadership":
			return leadershipNav;
		default:
			return studentNav;
	}
});
</script>
