// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Transport Route", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Élèves affectés"), () => {
			frappe.set_route("List", "Student Transport Assignment", { route: frm.doc.name });
		});
	},
});
