<template>
	<div class="flex h-screen items-center justify-center bg-gray-50 px-4">
		<div class="max-w-sm text-center">
			<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-bf-red-50 text-bf-red-500">
				<FeatherIcon name="shield-off" class="h-7 w-7" />
			</div>
			<h1 class="text-lg font-semibold text-gray-900">Accès non disponible</h1>
			<p class="mt-2 text-sm text-gray-500">
				Ce compte ({{ session.user }}) n'a accès à aucun espace élève, parent ou enseignant. Contactez
				l'administration de l'école, ou rendez-vous sur l'interface Frappe si vous êtes membre du personnel.
			</p>
			<a href="/app" class="mt-5 inline-block text-sm font-medium text-bf-red-600 hover:underline">
				Aller vers l'espace Frappe →
			</a>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui";
import { session } from "@/session";
</script>
