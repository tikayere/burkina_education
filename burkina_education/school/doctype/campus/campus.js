// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Campus", {
	refresh(frm) {
		frm.set_query("school", () => ({ filters: { is_active: 1 } }));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Élèves de ce campus"), () => {
				frappe.set_route("List", "Student", { campus: frm.doc.name });
			});
		}
	},
});
