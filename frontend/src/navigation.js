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
