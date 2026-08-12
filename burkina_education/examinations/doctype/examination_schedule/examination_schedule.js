// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Draft: "gray",
	Scheduled: "blue",
	Ongoing: "orange",
	Completed: "green",
	Cancelled: "red",
};

frappe.ui.form.on("Examination Schedule", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (frm.doc.room && frm.doc.exam_date) {
			frm.add_custom_button(__("Occupation de la salle ce jour"), () => {
				frappe.set_route("List", "Examination Schedule", {
					room: frm.doc.room,
					exam_date: frm.doc.exam_date,
				});
			}, __("Voir"));
		}

		if (frm.doc.assessment_plan) {
			frm.add_custom_button(__("Saisir les notes"), () => {
				frappe.set_route("List", "Assessment Result", { assessment_plan: frm.doc.assessment_plan });
			}, __("Voir"));
		}
	},

	grade(frm) {
		frm.set_value("student_group", "");
		frm.set_value("course", "");
	},

	student_group(frm) {
		frm.set_query("course", () => ({
			filters: frm.doc.grade ? { grade: frm.doc.grade } : {},
		}));
	},
});
