<template>
	<div class="flex h-screen overflow-hidden bg-gray-50">
		<aside class="hidden w-64 shrink-0 flex-col border-r border-gray-100 bg-white lg:flex">
			<PortalSidebar />
		</aside>

		<div v-if="mobileNavOpen" class="fixed inset-0 z-40 lg:hidden">
			<div class="absolute inset-0 bg-black/30" @click="mobileNavOpen = false" />
			<aside class="relative flex h-full w-72 flex-col bg-white shadow-xl">
				<PortalSidebar @navigate="mobileNavOpen = false" />
			</aside>
		</div>

		<div class="flex min-w-0 flex-1 flex-col">
			<header class="flex h-16 shrink-0 items-center justify-between border-b border-gray-100 bg-white px-4 sm:px-6">
				<div class="flex items-center gap-3">
					<button class="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 lg:hidden" @click="mobileNavOpen = true">
						<FeatherIcon name="menu" class="h-5 w-5" />
					</button>
					<h1 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h1>
				</div>
				<Dropdown :options="userMenuOptions" placement="right">
					<template #default>
						<button class="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 hover:bg-gray-100">
							<Avatar :label="session.fullName" :image="session.userImage" size="md" />
							<span class="hidden text-sm font-medium text-gray-700 sm:inline">{{ session.fullName }}</span>
							<FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-400" />
						</button>
					</template>
				</Dropdown>
			</header>

			<main class="flex-1 overflow-y-auto">
				<div class="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
					<router-view />
				</div>
			</main>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Avatar, Dropdown, FeatherIcon, call } from "frappe-ui";
import { session, PORTAL_LABELS, setHomePortal } from "@/session";
import PortalSidebar from "@/components/PortalSidebar.vue";

const route = useRoute();
const router = useRouter();
const mobileNavOpen = ref(false);
const pageTitle = computed(() => route.meta?.title || PORTAL_LABELS[route.meta?.portal || session.homePortal]);

async function logout() {
	// frappe.whitelist(methods=["POST"]) - a plain navigation (GET) 404s/403s,
	// hence call() (POST, CSRF-token attached) rather than window.location.
	await call("logout");
	window.location.href = "/login";
}

// A user holding more than one portal Role (e.g. a Guardian who's also a
// Secretary) already sees every portal's section in the sidebar
// (PortalSidebar.vue) - this menu only lets them change which one opens by
// default on the bare "/" the next time they land here, it is not an
// access gate. Single-role users (the common case) just don't see it.
const otherPortals = computed(() =>
	session.availablePortals.filter((p) => p !== session.homePortal).map((p) => ({
		label: `Ouvrir par défaut : ${PORTAL_LABELS[p]}`,
		icon: "star",
		onClick: () => setHomePortal(p, router),
	}))
);

const userMenuOptions = computed(() => [
	...otherPortals.value,
	{ label: "Espace Frappe (Desk)", icon: "grid", onClick: () => (window.location.href = "/app") },
	{ label: "Se déconnecter", icon: "log-out", onClick: logout },
]);
</script>
