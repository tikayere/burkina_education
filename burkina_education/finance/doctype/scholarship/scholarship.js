// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Brouillon: "gray",
	Approuvée: "green",
	Rejetée: "red",
};

frappe.ui.form.on("Scholarship", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}
		frm.trigger("toggle_percent");

		if (frm.is_new() || frm.doc.status === "Approuvée") return;

		// Only the roles that can actually write this doctype (Accountant /
		// System Manager, see setup/install.py) get to approve or reject it -
		// mirrors the server-side permission model, doesn't replace it.
		if (frappe.perm.has_perm(frm.doctype, 0, "write")) {
			frm.add_custom_button(__("Approuver"), () => {
				frm.set_value("status", "Approuvée");
				frm.save();
			});
			frm.add_custom_button(__("Rejeter"), () => {
				frappe.prompt(
					{ fieldname: "reason", fieldtype: "Small Text", label: __("Motif du refus") },
					(values) => {
						frm.set_value("status", "Rejetée");
						frm.set_value("reason", values.reason || frm.doc.reason);
						frm.save();
					},
					__("Rejeter la bourse")
				);
			});
		}
	},

	scholarship_type(frm) {
		frm.trigger("toggle_percent");
		if (frm.doc.scholarship_type === "Bourse Totale") {
			frm.set_value("discount_percent", 100);
		}
	},

	toggle_percent(frm) {
		// Mirrors Scholarship.validate_percent() server-side, just for
		// immediate feedback - the server remains the source of truth.
		frm.set_df_property("discount_percent", "read_only", frm.doc.scholarship_type === "Bourse Totale");
	},
});
