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

function resolvePortal(roles) {
	// Priority: a Guardian who's also somehow staff still lands on the
	// Guardian portal by default (the common real case: a parent who is
	// also a teacher at the same school still opens the app as a parent
	// first) - Teacher takes priority only when there's no Guardian/Student
	// role at all, since Instructor accounts are otherwise exclusively staff.
	if (roles.includes("Guardian")) return "guardian";
	if (roles.includes("Student")) return "student";
	if (roles.includes("Instructor")) return "teacher";
	return null;
}

export const session = reactive({
	...boot,
	isGuest: boot.user === "Guest",
	portal: resolvePortal(boot.roles),
	isClassTeacher: boot.roles.includes("Class Teacher"),
});

export const portalLabel = computed(() => {
	return { student: "Espace Élève", guardian: "Espace Parent", teacher: "Espace Enseignant" }[session.portal] || "";
});
