// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Ouvert: "orange",
	"Suivi requis": "red",
	Clos: "green",
};

frappe.ui.form.on("Clinic Visit", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (frm.is_new() || frm.doc.status === "Clos" || !frappe.perm.has_perm(frm.doctype, 0, "write")) return;

		frm.add_custom_button(__("Clôturer"), () => {
			frm.set_value("status", "Clos");
			frm.save();
		});
	},

	referral(frm) {
		if (frm.doc.referral === "Aucun") frm.set_value("referral_details", "");
	},
});
