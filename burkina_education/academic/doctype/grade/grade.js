// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Grade", {
	refresh(frm) {
		frm.set_query("cycle", () => ({
			filters: frm.doc.school ? { school: frm.doc.school } : {},
		}));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Élèves"), () => {
				frappe.set_route("List", "Student", { grade: frm.doc.name });
			}, __("Voir"));
			frm.add_custom_button(__("Curriculum"), () => {
				frappe.set_route("List", "Curriculum", { grade: frm.doc.name });
			}, __("Voir"));
			if (frm.doc.program) {
				frm.add_custom_button(__("Programme (Education)"), () => {
					frappe.set_route("Form", "Program", frm.doc.program);
				}, __("Voir"));
			}
		}
	},

	cycle(frm) {
		if (frm.doc.cycle && !frm.doc.school) {
			frappe.db.get_value("Cycle", frm.doc.cycle, "school").then((r) => {
				if (r.message && r.message.school) {
					frm.set_value("school", r.message.school);
				}
			});
		}
	},
});
