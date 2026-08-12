// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Learning Objective", {
	refresh(frm) {
		frm.trigger("suggest_sequence");
	},

	competency(frm) {
		frm.trigger("suggest_sequence");
	},

	suggest_sequence(frm) {
		if (!frm.doc.competency || frm.doc.sequence) return;
		frappe.db.get_list("Learning Objective", {
			filters: { competency: frm.doc.competency },
			fields: ["sequence"],
			order_by: "sequence desc",
			limit: 1,
		}).then((rows) => {
			frm.set_value("sequence", (rows.length ? (rows[0].sequence || 0) : 0) + 1);
		});
	},
});
