import { call } from "frappe-ui";

// Thin, explicit wrappers around the whitelisted Python endpoints
// (burkina_education/portal/*.py) - one function per backend method, no
// generic doctype CRUD here since every portal view is backed by a
// purpose-built, already-scoped aggregate endpoint (see
// docs/architecture.md section L). `call()` (from frappe-ui) POSTs to
// `/api/method/<path>` and attaches `X-Frappe-CSRF-Token` from
// `window.csrf_token` automatically (session.js documents where that comes
// from).

function endpoint(path) {
	return (args) => call(`burkina_education.portal.${path}`, args);
}

export const studentApi = {
	dashboard: endpoint("student_api.get_dashboard"),
	profile: endpoint("student_api.get_profile"),
	attendance: endpoint("student_api.get_attendance"),
	grades: endpoint("student_api.get_grades"),
	termReport: endpoint("student_api.get_term_report"),
	annualReport: endpoint("student_api.get_annual_report"),
	fees: endpoint("student_api.get_fees"),
	invoice: endpoint("student_api.get_invoice"),
	mobileMoneyProviders: endpoint("student_api.get_mobile_money_providers"),
	library: endpoint("student_api.get_library"),
	transport: endpoint("student_api.get_transport"),
	canteen: endpoint("student_api.get_canteen"),
	boarding: endpoint("student_api.get_boarding"),
	discipline: endpoint("student_api.get_discipline"),
	schedule: endpoint("student_api.get_schedule"),
	announcements: endpoint("student_api.get_announcements"),
	inbox: endpoint("student_api.get_inbox"),
};

const guardianRaw = {
	children: endpoint("guardian_api.get_children"),
	dashboard: endpoint("guardian_api.get_dashboard"),
	child: endpoint("guardian_api.get_child"),
	profile: endpoint("guardian_api.get_child_profile"),
	attendance: endpoint("guardian_api.get_child_attendance"),
	grades: endpoint("guardian_api.get_child_grades"),
	termReport: endpoint("guardian_api.get_child_term_report"),
	annualReport: endpoint("guardian_api.get_child_annual_report"),
	fees: endpoint("guardian_api.get_child_fees"),
	invoice: endpoint("guardian_api.get_child_invoice"),
	payInvoice: endpoint("guardian_api.pay_child_invoice"),
	mobileMoneyProviders: endpoint("guardian_api.get_mobile_money_providers"),
	library: endpoint("guardian_api.get_child_library"),
	transport: endpoint("guardian_api.get_child_transport"),
	canteen: endpoint("guardian_api.get_child_canteen"),
	boarding: endpoint("guardian_api.get_child_boarding"),
	discipline: endpoint("guardian_api.get_child_discipline"),
	clinic: endpoint("guardian_api.get_child_clinic"),
	schedule: endpoint("guardian_api.get_child_schedule"),
	inbox: endpoint("guardian_api.get_inbox"),
};

export const guardianApi = guardianRaw;

/**
 * A student-shaped API bound to one child, so the same read-only workspace
 * component (pages/shared/StudentWorkspace.vue) can render either "my own
 * record" (Student Portal) or "this specific child" (Guardian Portal)
 * without knowing which one it's looking at.
 */
export function childApi(student) {
	return {
		overview: () => guardianRaw.child({ student }),
		profile: () => guardianRaw.profile({ student }),
		attendance: (args) => guardianRaw.attendance({ student, ...args }),
		grades: () => guardianRaw.grades({ student }),
		termReport: (args) => guardianRaw.termReport({ student, ...args }),
		annualReport: (args) => guardianRaw.annualReport({ student, ...args }),
		fees: () => guardianRaw.fees({ student }),
		invoice: (args) => guardianRaw.invoice({ student, ...args }),
		payInvoice: (args) => guardianRaw.payInvoice({ student, ...args }),
		mobileMoneyProviders: () => guardianRaw.mobileMoneyProviders(),
		library: () => guardianRaw.library({ student }),
		transport: () => guardianRaw.transport({ student }),
		canteen: () => guardianRaw.canteen({ student }),
		boarding: () => guardianRaw.boarding({ student }),
		discipline: () => guardianRaw.discipline({ student }),
		clinic: () => guardianRaw.clinic({ student }),
		schedule: (args) => guardianRaw.schedule({ student, ...args }),
		hasClinic: true,
	};
}

export function selfApi() {
	return {
		overview: () => studentApi.dashboard(),
		profile: () => studentApi.profile(),
		attendance: (args) => studentApi.attendance(args),
		grades: () => studentApi.grades(),
		termReport: (args) => studentApi.termReport(args),
		annualReport: (args) => studentApi.annualReport(args),
		fees: () => studentApi.fees(),
		invoice: (args) => studentApi.invoice(args),
		payInvoice: () => Promise.reject(new Error("Le paiement se fait depuis l'espace parent.")),
		mobileMoneyProviders: () => studentApi.mobileMoneyProviders(),
		library: () => studentApi.library(),
		transport: () => studentApi.transport(),
		canteen: () => studentApi.canteen(),
		boarding: () => studentApi.boarding(),
		discipline: () => studentApi.discipline(),
		clinic: () => Promise.resolve([]),
		schedule: (args) => studentApi.schedule(args),
		hasClinic: false,
	};
}

export const teacherApi = {
	dashboard: endpoint("teacher_api.get_dashboard"),
	groups: endpoint("teacher_api.get_groups"),
	groupStudents: endpoint("teacher_api.get_group_students"),
	schedule: endpoint("teacher_api.get_schedule"),
	attendanceSheet: endpoint("teacher_api.get_attendance_sheet"),
	markAttendance: endpoint("teacher_api.mark_attendance"),
	assessmentPlans: endpoint("teacher_api.get_assessment_plans"),
	assessmentResultSheet: endpoint("teacher_api.get_assessment_result_sheet"),
	saveAssessmentResults: endpoint("teacher_api.save_assessment_results"),
	submitAssessmentResult: endpoint("teacher_api.submit_assessment_result"),
	disciplineCases: endpoint("teacher_api.get_discipline_cases"),
	createDisciplineCase: endpoint("teacher_api.create_discipline_case"),
	announcements: endpoint("teacher_api.get_announcements"),
	sendMessage: endpoint("teacher_api.send_message_to_guardian"),
	inbox: endpoint("teacher_api.get_inbox"),
};
