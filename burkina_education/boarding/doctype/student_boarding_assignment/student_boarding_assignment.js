// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Boarding Assignment", {
	refresh(frm) {
		frm.page.set_indicator(__(frm.doc.status), frm.doc.status === "Actif" ? "green" : "gray");

		if (frm.is_new() || frm.doc.status !== "Actif" || !frappe.perm.has_perm(frm.doctype, 0, "write")) return;

		frm.add_custom_button(__("Enregistrer la sortie"), () => {
			frm.call("check_out").then(() => frm.reload_doc());
		});
	},
});
