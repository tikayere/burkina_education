import { reactive } from "vue";

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
// backend. Order here is priority order: it decides which portal owns the
// bare "/" path (see router.js) when a user holds more than one - every
// portal a user holds is mounted and reachable from the sidebar regardless
// of this order (docs/architecture.md section M/N: a multi-role user gets
// the union of every role's information, not just one at a time).
const ROLE_PORTAL = [
	["Guardian", "guardian"],
	["Student", "student"],
	["Instructor", "teacher"],
	["School Director", "leadership"],
	["Academic Director", "academic"],
	["Examination Coordinator", "academic"],
	["Registrar", "academic"],
	["Department Head", "academic"],
	["Accountant", "finance"],
	["Librarian", "librarian"],
	["Transport Manager", "transport"],
	["Canteen Manager", "canteen"],
	["Boarding Manager", "boarding"],
	["Clinic Staff", "clinic"],
	["Secretary", "comms"],
	["Receptionist", "frontdesk"],
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
	frontdesk: "Espace Accueil",
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

const STORAGE_KEY = "burkina-education:home-portal";

// Which portal owns the bare "/" path (router.js) - purely a landing-page
// preference, not an access boundary. A user holding several portal Roles
// (e.g. a Guardian who's also a Secretary) can always reach every one of
// them from the sidebar (PortalSidebar.vue); this only decides which one
// they see first when opening "/portal" itself.
function resolveHomePortal(available) {
	if (!available.length) return null;
	const remembered = window.localStorage?.getItem(STORAGE_KEY);
	if (remembered && available.includes(remembered)) return remembered;
	return available[0];
}

const availablePortals = resolveAvailablePortals(boot.roles);

export const session = reactive({
	...boot,
	isGuest: boot.user === "Guest",
	availablePortals,
	homePortal: resolveHomePortal(availablePortals),
	isClassTeacher: boot.roles.includes("Class Teacher"),
});

// Persists which portal should own "/" on the *next* load (route
// registration happens once, at router creation - see router.js) and
// immediately navigates there via the named "<portal>-dashboard" route,
// which resolves correctly whether that portal is mounted at the root or
// nested under "/<portal>" (AppShell.vue's user menu is the only caller).
export function setHomePortal(portal, router) {
	if (!session.availablePortals.includes(portal)) return;
	window.localStorage?.setItem(STORAGE_KEY, portal);
	session.homePortal = portal;
	router?.push({ name: `${portal}-dashboard` });
}
