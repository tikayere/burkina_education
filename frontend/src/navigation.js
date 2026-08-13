// Primary sidebar nav per role. Guardian's "child-scoped" section links are
// generated separately (AppShell.vue) once a child is selected, since they
// need the current :student route param baked into their `to`.

export const studentNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "student-dashboard" } },
	{ label: "Notes & bulletins", icon: "award", to: { name: "student-grades" } },
	{ label: "Présence", icon: "check-square", to: { name: "student-attendance" } },
	{ label: "Frais scolaires", icon: "credit-card", to: { name: "student-fees" } },
	{ label: "Emploi du temps", icon: "calendar", to: { name: "student-schedule" } },
	{ label: "Bibliothèque", icon: "book-open", to: { name: "student-library" } },
	{ label: "Transport", icon: "truck", to: { name: "student-transport" } },
	{ label: "Cantine", icon: "coffee", to: { name: "student-canteen" } },
	{ label: "Internat", icon: "moon", to: { name: "student-boarding" } },
	{ label: "Discipline", icon: "shield", to: { name: "student-discipline" } },
	{ label: "Annonces", icon: "bell", to: { name: "student-announcements" } },
	{ label: "Messages", icon: "mail", to: { name: "student-messages" } },
];

export const guardianNav = [
	{ label: "Mes enfants", icon: "home", to: { name: "guardian-dashboard" } },
	{ label: "Annonces", icon: "bell", to: { name: "guardian-announcements" } },
	{ label: "Messages", icon: "mail", to: { name: "guardian-messages" } },
];

// Sub-navigation shown once a specific child is selected
// (AppShell.vue reads route.params.student to build these).
export function childNav(student) {
	return [
		{ label: "Aperçu", icon: "grid", to: { name: "child-overview", params: { student } } },
		{ label: "Notes & bulletins", icon: "award", to: { name: "child-grades", params: { student } } },
		{ label: "Présence", icon: "check-square", to: { name: "child-attendance", params: { student } } },
		{ label: "Frais scolaires", icon: "credit-card", to: { name: "child-fees", params: { student } } },
		{ label: "Emploi du temps", icon: "calendar", to: { name: "child-schedule", params: { student } } },
		{ label: "Bibliothèque", icon: "book-open", to: { name: "child-library", params: { student } } },
		{ label: "Transport", icon: "truck", to: { name: "child-transport", params: { student } } },
		{ label: "Cantine", icon: "coffee", to: { name: "child-canteen", params: { student } } },
		{ label: "Internat", icon: "moon", to: { name: "child-boarding", params: { student } } },
		{ label: "Discipline", icon: "shield", to: { name: "child-discipline", params: { student } } },
		{ label: "Infirmerie", icon: "heart", to: { name: "child-clinic", params: { student } } },
	];
}

export function teacherNav(isClassTeacher) {
	return [
		{ label: "Tableau de bord", icon: "home", to: { name: "teacher-dashboard" } },
		{ label: "Mes classes", icon: "users", to: { name: "teacher-groups" } },
		{ label: "Cahier de notes", icon: "award", to: { name: "teacher-gradebook" } },
		{ label: "Emploi du temps", icon: "calendar", to: { name: "teacher-schedule" } },
		...(isClassTeacher
			? [{ label: "Discipline", icon: "shield", to: { name: "teacher-discipline" } }]
			: []),
		{ label: "Annonces", icon: "bell", to: { name: "teacher-announcements" } },
		{ label: "Messages", icon: "mail", to: { name: "teacher-messages" } },
	];
}

// Staff portals (docs/architecture.md section M) - one nav array per Role
// portal, same "declarative list of {label, icon, to}" shape as the three
// above.

export const librarianNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "librarian-dashboard" } },
	{ label: "Catalogue", icon: "book", to: { name: "librarian-catalogue" } },
	{ label: "Adhésions", icon: "user-check", to: { name: "librarian-members" } },
	{ label: "Emprunts", icon: "book-open", to: { name: "librarian-loans" } },
];

export const transportNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "transport-dashboard" } },
	{ label: "Itinéraires", icon: "map", to: { name: "transport-routes" } },
	{ label: "Affectations", icon: "users", to: { name: "transport-assignments" } },
];

export const canteenNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "canteen-dashboard" } },
	{ label: "Formules", icon: "clipboard", to: { name: "canteen-plans" } },
	{ label: "Abonnements", icon: "users", to: { name: "canteen-subscriptions" } },
];

export const boardingNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "boarding-dashboard" } },
	{ label: "Bâtiments", icon: "layers", to: { name: "boarding-buildings" } },
	{ label: "Affectations", icon: "users", to: { name: "boarding-assignments" } },
];

export const clinicNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "clinic-dashboard" } },
	{ label: "Visites", icon: "activity", to: { name: "clinic-visits" } },
];

export const financeNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "finance-dashboard" } },
	{ label: "Factures", icon: "file-text", to: { name: "finance-invoices" } },
	{ label: "Mobile Money", icon: "smartphone", to: { name: "finance-mobile-money" } },
	{ label: "Bourses", icon: "award", to: { name: "finance-scholarships" } },
];

export function academicNav({ hasStructure, hasExams, hasPedagogy, isDirector }) {
	return [
		{ label: "Tableau de bord", icon: "home", to: { name: "academic-dashboard" } },
		...(hasStructure ? [{ label: "Structure scolaire", icon: "layers", to: { name: "academic-structure" } }] : []),
		...(hasExams ? [{ label: "Examens", icon: "clipboard", to: { name: "academic-exams" } }] : []),
		// Department Head gets Pédagogie on its own (curriculum authoring,
		// same rights as Instructor); Discipline/Bourses/Annonces stay
		// Academic Director-only administrative tools.
		...(hasPedagogy ? [{ label: "Pédagogie", icon: "book", to: { name: "academic-pedagogy" } }] : []),
		...(isDirector
			? [
					{ label: "Discipline", icon: "shield", to: { name: "academic-discipline" } },
					{ label: "Bourses", icon: "award", to: { name: "academic-scholarships" } },
					{ label: "Annonces", icon: "bell", to: { name: "academic-announcements" } },
				]
			: []),
	];
}

export const commsNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "comms-dashboard" } },
	{ label: "Annonces", icon: "bell", to: { name: "comms-announcements" } },
	{ label: "Modèles", icon: "file-text", to: { name: "comms-templates" } },
];

export const leadershipNav = [
	{ label: "Tableau de bord", icon: "home", to: { name: "leadership-dashboard" } },
	{ label: "Discipline", icon: "shield", to: { name: "leadership-discipline" } },
];

export const frontdeskNav = [
	{ label: "Accueil", icon: "home", to: { name: "frontdesk-dashboard" } },
];
