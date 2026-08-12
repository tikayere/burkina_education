// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Learning Unit", {
	refresh(frm) {
		frm.trigger("suggest_sequence");

		if (!frm.is_new()) {
			frm.add_custom_button(__("Leçon"), () => {
				frappe.new_doc("Lesson", { learning_unit: frm.doc.name });
			}, __("Nouveau"));
			frm.add_custom_button(__("Leçons"), () => {
				frappe.set_route("List", "Lesson", { learning_unit: frm.doc.name });
			}, __("Voir"));
		}
	},

	curriculum(frm) {
		frm.trigger("suggest_sequence");
	},

	suggest_sequence(frm) {
		if (!frm.doc.curriculum || frm.doc.sequence) return;
		frappe.db.get_list("Learning Unit", {
			filters: { curriculum: frm.doc.curriculum },
			fields: ["sequence"],
			order_by: "sequence desc",
			limit: 1,
		}).then((rows) => {
			frm.set_value("sequence", (rows.length ? (rows[0].sequence || 0) : 0) + 1);
		});
	},
});
