import { createRouter, createWebHistory } from "vue-router";
import { session } from "@/session";

// Shared, role-agnostic workspace pages (pages/shared/) - each accepts an
// optional `student` route param; present -> Guardian viewing one child,
// absent -> Student viewing themselves. See src/api.js (`selfApi`/`childApi`).
const Overview = () => import("@/pages/shared/Overview.vue");
const Profile = () => import("@/pages/shared/Profile.vue");
const Grades = () => import("@/pages/shared/Grades.vue");
const TermReport = () => import("@/pages/shared/TermReport.vue");
const AnnualReport = () => import("@/pages/shared/AnnualReport.vue");
const Attendance = () => import("@/pages/shared/Attendance.vue");
const Fees = () => import("@/pages/shared/Fees.vue");
const InvoiceDetail = () => import("@/pages/shared/InvoiceDetail.vue");
const Library = () => import("@/pages/shared/Library.vue");
const Transport = () => import("@/pages/shared/Transport.vue");
const Canteen = () => import("@/pages/shared/Canteen.vue");
const Boarding = () => import("@/pages/shared/Boarding.vue");
const Discipline = () => import("@/pages/shared/Discipline.vue");
const Clinic = () => import("@/pages/shared/Clinic.vue");
const Schedule = () => import("@/pages/shared/Schedule.vue");

const studentRoutes = [
	{ path: "/", name: "student-dashboard", component: Overview, meta: { title: "Tableau de bord" } },
	{ path: "/profil", name: "student-profile", component: Profile, meta: { title: "Mon profil" } },
	{ path: "/notes", name: "student-grades", component: Grades, meta: { title: "Notes & bulletins" } },
	{ path: "/bulletin/:name", name: "student-bulletin", component: TermReport, props: true, meta: { title: "Bulletin trimestriel" } },
	{ path: "/bulletin-annuel/:name", name: "student-bulletin-annuel", component: AnnualReport, props: true, meta: { title: "Bulletin annuel" } },
	{ path: "/presence", name: "student-attendance", component: Attendance, meta: { title: "Présence" } },
	{ path: "/frais", name: "student-fees", component: Fees, meta: { title: "Frais scolaires" } },
	{ path: "/frais/:name", name: "student-invoice", component: InvoiceDetail, props: true, meta: { title: "Facture" } },
	{ path: "/bibliotheque", name: "student-library", component: Library, meta: { title: "Bibliothèque" } },
	{ path: "/transport", name: "student-transport", component: Transport, meta: { title: "Transport" } },
	{ path: "/cantine", name: "student-canteen", component: Canteen, meta: { title: "Cantine" } },
	{ path: "/internat", name: "student-boarding", component: Boarding, meta: { title: "Internat" } },
	{ path: "/discipline", name: "student-discipline", component: Discipline, meta: { title: "Discipline" } },
	{ path: "/emploi-du-temps", name: "student-schedule", component: Schedule, meta: { title: "Emploi du temps" } },
	{ path: "/annonces", name: "student-announcements", component: () => import("@/pages/shared/Announcements.vue"), meta: { title: "Annonces" } },
	{ path: "/messages", name: "student-messages", component: () => import("@/pages/shared/Inbox.vue"), meta: { title: "Messages" } },
];

const childProps = (route) => ({ student: route.params.student });

const guardianRoutes = [
	{ path: "/", name: "guardian-dashboard", component: () => import("@/pages/guardian/Dashboard.vue"), meta: { title: "Mes enfants" } },
	{ path: "/enfant/:student", name: "child-overview", component: Overview, props: childProps, meta: { title: "Aperçu" } },
	{ path: "/enfant/:student/profil", name: "child-profile", component: Profile, props: childProps, meta: { title: "Profil" } },
	{ path: "/enfant/:student/notes", name: "child-grades", component: Grades, props: childProps, meta: { title: "Notes & bulletins" } },
	{ path: "/enfant/:student/bulletin/:name", name: "child-bulletin", component: TermReport, props: (r) => ({ student: r.params.student, name: r.params.name }), meta: { title: "Bulletin trimestriel" } },
	{ path: "/enfant/:student/bulletin-annuel/:name", name: "child-bulletin-annuel", component: AnnualReport, props: (r) => ({ student: r.params.student, name: r.params.name }), meta: { title: "Bulletin annuel" } },
	{ path: "/enfant/:student/presence", name: "child-attendance", component: Attendance, props: childProps, meta: { title: "Présence" } },
	{ path: "/enfant/:student/frais", name: "child-fees", component: Fees, props: childProps, meta: { title: "Frais scolaires" } },
	{ path: "/enfant/:student/frais/:name", name: "child-invoice", component: InvoiceDetail, props: (r) => ({ student: r.params.student, name: r.params.name }), meta: { title: "Facture" } },
	{ path: "/enfant/:student/bibliotheque", name: "child-library", component: Library, props: childProps, meta: { title: "Bibliothèque" } },
	{ path: "/enfant/:student/transport", name: "child-transport", component: Transport, props: childProps, meta: { title: "Transport" } },
	{ path: "/enfant/:student/cantine", name: "child-canteen", component: Canteen, props: childProps, meta: { title: "Cantine" } },
	{ path: "/enfant/:student/internat", name: "child-boarding", component: Boarding, props: childProps, meta: { title: "Internat" } },
	{ path: "/enfant/:student/discipline", name: "child-discipline", component: Discipline, props: childProps, meta: { title: "Discipline" } },
	{ path: "/enfant/:student/clinique", name: "child-clinic", component: Clinic, props: childProps, meta: { title: "Infirmerie" } },
	{ path: "/enfant/:student/emploi-du-temps", name: "child-schedule", component: Schedule, props: childProps, meta: { title: "Emploi du temps" } },
	{ path: "/annonces", name: "guardian-announcements", component: () => import("@/pages/guardian/Announcements.vue"), meta: { title: "Annonces" } },
	{ path: "/messages", name: "guardian-messages", component: () => import("@/pages/shared/Inbox.vue"), meta: { title: "Messages" } },
];

const teacherRoutes = [
	{ path: "/", name: "teacher-dashboard", component: () => import("@/pages/teacher/Dashboard.vue"), meta: { title: "Tableau de bord" } },
	{ path: "/classes", name: "teacher-groups", component: () => import("@/pages/teacher/Groups.vue"), meta: { title: "Mes classes" } },
	{ path: "/classes/:group", name: "teacher-group-detail", component: () => import("@/pages/teacher/GroupDetail.vue"), props: true, meta: { title: "Classe" } },
	{ path: "/classes/:group/presence", name: "teacher-attendance", component: () => import("@/pages/teacher/MarkAttendance.vue"), props: true, meta: { title: "Faire l'appel" } },
	{ path: "/notation", name: "teacher-gradebook", component: () => import("@/pages/teacher/Gradebook.vue"), meta: { title: "Cahier de notes" } },
	{ path: "/notation/:plan", name: "teacher-gradebook-plan", component: () => import("@/pages/teacher/GradebookEntry.vue"), props: true, meta: { title: "Saisie des notes" } },
	{ path: "/discipline", name: "teacher-discipline", component: () => import("@/pages/teacher/Discipline.vue"), meta: { title: "Discipline" } },
	{ path: "/emploi-du-temps", name: "teacher-schedule", component: () => import("@/pages/teacher/Schedule.vue"), meta: { title: "Emploi du temps" } },
	{ path: "/annonces", name: "teacher-announcements", component: () => import("@/pages/shared/Announcements.vue"), meta: { title: "Annonces" } },
	{ path: "/messages", name: "teacher-messages", component: () => import("@/pages/teacher/Messages.vue"), meta: { title: "Messages" } },
];

function routesForRole() {
	if (session.portal === "guardian") return guardianRoutes;
	if (session.portal === "teacher") return teacherRoutes;
	if (session.portal === "student") return studentRoutes;
	return [];
}

const AppShell = () => import("@/components/AppShell.vue");
const NotAuthorized = () => import("@/pages/NotAuthorized.vue");

export const router = createRouter({
	history: createWebHistory("/portal"),
	routes: [
		{
			path: "/",
			component: session.portal ? AppShell : NotAuthorized,
			children: session.portal ? routesForRole() : [],
		},
		{ path: "/:pathMatch(.*)*", redirect: "/" },
	],
});
