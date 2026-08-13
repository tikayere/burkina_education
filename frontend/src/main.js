import { createApp } from "vue";
import { FrappeUI, frappeRequest, setConfig } from "frappe-ui";
import App from "@/App.vue";
import { router } from "@/router";
import "@/style.css";

// frappe-ui's createResource/createListResource/createDocumentResource (used
// throughout components/resource/*.vue for the generic-CRUD staff portals -
// docs/architecture.md section M) fetch through `getConfig('resourceFetcher')`,
// which otherwise defaults to a bare fetch with no `/api/method/` prefix and
// no CSRF header - every request 404s against the current SPA route instead
// of the backend. `call()` (used by api.js) builds its own absolute path and
// doesn't need this, which is why the Dashboard pages worked before this was
// wired up but the generic list/form pages didn't.
setConfig("resourceFetcher", frappeRequest);

const app = createApp(App);
app.use(router);
app.use(FrappeUI);
app.mount("#app");
