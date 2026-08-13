<template>
	<router-view />
	<Dialogs />
	<Toast />
</template>

<script setup>
import { Dialogs, Toast } from "frappe-ui";
</script>
