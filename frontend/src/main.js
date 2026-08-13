import { createApp } from "vue";
import { FrappeUI } from "frappe-ui";
import App from "@/App.vue";
import { router } from "@/router";
import "@/style.css";

const app = createApp(App);
app.use(router);
app.use(FrappeUI);
app.mount("#app");
