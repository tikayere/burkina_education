// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Actif: "green",
	Suspendu: "orange",
	Terminé: "gray",
};

frappe.ui.form.on("Student Transport Assignment", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}
	},

	route(frm) {
		frm.set_value("stop_name", "");
		if (!frm.doc.route) return;
		frappe.db.get_doc("Transport Route", frm.doc.route).then((route) => {
			frm.set_df_property(
				"stop_name",
				"description",
				(route.stops || []).map((s) => s.stop_name).join(", ")
			);
		});
	},
});
