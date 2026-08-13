<template>
	<FrappeUIProvider>
		<router-view />
		<Dialogs />
	</FrappeUIProvider>
</template>

<script setup>
// The old `<Toast />` (singular) was a single toast item's own component,
// not a container - it rendered nothing since it isn't subscribed to the
// toast.create()/success()/error() state (composables/useAsync.js). The
// actual container (`Toasts`, plural) isn't part of frappe-ui's public
// package export - it's only reachable through `<FrappeUIProvider>`, which
// also supplies the swipe/viewport positioning Toasts needs (frappe-ui's
// own ToastProvider.vue wraps them the same way).
import { Dialogs, FrappeUIProvider } from "frappe-ui";
</script>
