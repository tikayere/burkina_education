// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Education Level", {
	refresh(frm) {
		frm.set_query("school", () => ({ filters: { is_active: 1 } }));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Cycles"), () => {
				frappe.set_route("List", "Cycle", { education_level: frm.doc.name });
			});
			frm.add_custom_button(__("Barèmes de notation"), () => {
				frappe.set_route("List", "Grading Scheme", { education_level: frm.doc.name });
			});
		}
	},
});
