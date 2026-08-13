// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Ouvert: "red",
	"En cours": "orange",
	Résolu: "green",
};

frappe.ui.form.on("Disciplinary Case", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (frm.is_new() || frm.doc.status === "Résolu" || !frappe.perm.has_perm(frm.doctype, 0, "write")) return;

		if (frm.doc.status === "Ouvert") {
			frm.add_custom_button(__("Prendre en charge"), () => {
				frm.set_value("status", "En cours");
				frm.save();
			});
		}

		frm.add_custom_button(__("Marquer résolu"), () => {
			frappe.prompt(
				{ fieldname: "resolution", fieldtype: "Small Text", label: __("Résolution"), reqd: 1 },
				(values) => {
					frm.set_value("status", "Résolu");
					frm.set_value("resolution", values.resolution);
					frm.save();
				},
				__("Résoudre le cas")
			);
		});
	},
});
