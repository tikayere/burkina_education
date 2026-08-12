// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Curriculum", {
	refresh(frm) {
		frm.set_query("course", () => ({
			filters: frm.doc.grade ? { grade: frm.doc.grade } : {},
		}));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Compétence"), () => {
				frappe.new_doc("Competency", { curriculum: frm.doc.name });
			}, __("Nouveau"));
			frm.add_custom_button(__("Unité d'apprentissage"), () => {
				frappe.new_doc("Learning Unit", { curriculum: frm.doc.name });
			}, __("Nouveau"));

			frm.add_custom_button(__("Compétences"), () => {
				frappe.set_route("List", "Competency", { curriculum: frm.doc.name });
			}, __("Voir"));
			frm.add_custom_button(__("Unités d'apprentissage"), () => {
				frappe.set_route("List", "Learning Unit", { curriculum: frm.doc.name });
			}, __("Voir"));
		}
	},

	grade(frm) {
		if (frm.doc.grade && !frm.doc.school) {
			frappe.db.get_value("Grade", frm.doc.grade, "school").then((r) => {
				if (r.message && r.message.school) {
					frm.set_value("school", r.message.school);
				}
			});
		}
	},
});
