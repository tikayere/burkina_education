// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Competency", {
	refresh(frm) {
		if (frm.is_new() && frm.doc.curriculum) {
			frm.trigger("suggest_sequence");
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Objectif d'apprentissage"), () => {
				frappe.new_doc("Learning Objective", { competency: frm.doc.name });
			}, __("Nouveau"));
			frm.add_custom_button(__("Objectifs d'apprentissage"), () => {
				frappe.set_route("List", "Learning Objective", { competency: frm.doc.name });
			}, __("Voir"));
		}
	},

	curriculum(frm) {
		frm.trigger("suggest_sequence");
	},

	suggest_sequence(frm) {
		if (!frm.doc.curriculum || frm.doc.sequence) return;
		frappe.db.get_list("Competency", {
			filters: { curriculum: frm.doc.curriculum },
			fields: ["sequence"],
			order_by: "sequence desc",
			limit: 1,
		}).then((rows) => {
			frm.set_value("sequence", (rows.length ? (rows[0].sequence || 0) : 0) + 1);
		});
	},
});
