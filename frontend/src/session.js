import { computed, reactive } from "vue";

// Populated server-side by www/portal.py::get_context() -> context.boot, and
// flattened onto `window` by frappe-ui's vite "jinjaBootData" plugin
// (`window["{{ key }}"] = {{ boot[key] | tojson }}` for every key in
// `boot`) - see docs/architecture.md section L. `frappe-ui`'s own `call()`
// utility reads `window.csrf_token` directly, so this is also what makes
// every POST call in api.js authenticated.
const boot = {
	user: window.user || "Guest",
	fullName: window.full_name || window.user || "",
	roles: window.roles || [],
	userImage: window.user_image || null,
	sitename: window.sitename || "",
};

// One entry per Role this app has a portal for - mirrors (by hand, see that
// module's own docstring) portal/roles/__init__.py::ROLE_PORTAL on the
// backend. Order here is priority order: a user holding more than one of
// these roles lands on the first match, but every match they hold is still
// offered in the "changer d'espace" switcher (AppShell.vue).
const ROLE_PORTAL = [
	["Guardian", "guardian"],
	["Student", "student"],
	["Instructor", "teacher"],
	["School Director", "leadership"],
	["Academic Director", "academic"],
	["Examination Coordinator", "academic"],
	["Registrar", "academic"],
	["Accountant", "finance"],
	["Librarian", "librarian"],
	["Transport Manager", "transport"],
	["Canteen Manager", "canteen"],
	["Boarding Manager", "boarding"],
	["Clinic Staff", "clinic"],
	["Secretary", "comms"],
];

export const PORTAL_LABELS = {
	student: "Espace Élève",
	guardian: "Espace Parent",
	teacher: "Espace Enseignant",
	librarian: "Espace Bibliothèque",
	transport: "Espace Transport",
	canteen: "Espace Cantine",
	boarding: "Espace Internat",
	clinic: "Espace Infirmerie",
	finance: "Espace Comptabilité",
	academic: "Espace Scolarité",
	comms: "Espace Communication",
	leadership: "Tableau de bord Direction",
};

function resolveAvailablePortals(roles) {
	const seen = new Set();
	const portals = [];
	for (const [role, portal] of ROLE_PORTAL) {
		if (roles.includes(role) && !seen.has(portal)) {
			seen.add(portal);
			portals.push(portal);
		}
	}
	return portals;
}

const STORAGE_KEY = "burkina-education:portal";

function resolvePortal(roles) {
	const available = resolveAvailablePortals(roles);
	if (!available.length) return null;

	// A user with more than one portal (rare - e.g. a Guardian who's also
	// staff) keeps whichever they last chose (AppShell.vue's "changer
	// d'espace" switcher writes this), falling back to priority order the
	// very first time.
	const remembered = window.localStorage?.getItem(STORAGE_KEY);
	if (remembered && available.includes(remembered)) return remembered;
	return available[0];
}

export const session = reactive({
	...boot,
	isGuest: boot.user === "Guest",
	availablePortals: resolveAvailablePortals(boot.roles),
	portal: resolvePortal(boot.roles),
	isClassTeacher: boot.roles.includes("Class Teacher"),
});

export function switchPortal(portal) {
	if (!session.availablePortals.includes(portal)) return;
	window.localStorage?.setItem(STORAGE_KEY, portal);
	window.location.href = "/portal";
}

export const portalLabel = computed(() => PORTAL_LABELS[session.portal] || "");
