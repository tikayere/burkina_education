// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Emprunté: "blue",
	"En retard": "red",
	Retourné: "green",
	Perdu: "gray",
};

frappe.ui.form.on("Library Transaction", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (frm.is_new() || !frappe.perm.has_perm(frm.doctype, 0, "write")) return;

		if (["Emprunté", "En retard"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Enregistrer le retour"), () => {
				frm.set_value("return_date", frappe.datetime.get_today());
				frm.save();
			});
			frm.add_custom_button(__("Marquer comme perdu"), () => {
				frm.set_value("status", "Perdu");
				frm.save();
			});
		}
	},
});
