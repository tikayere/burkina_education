// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Planned: "orange",
	Delivered: "green",
	Cancelled: "red",
};

frappe.ui.form.on("Lesson", {
	refresh(frm) {
		frm.trigger("suggest_sequence");
		frm.trigger("filter_objectives");

		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (!frm.is_new() && frm.doc.status === "Planned") {
			frm.add_custom_button(__("Marquer comme dispensée"), () => {
				frm.set_value("status", "Delivered");
				frm.save();
			});
		}
	},

	learning_unit(frm) {
		frm.trigger("suggest_sequence");
		frm.trigger("filter_objectives");
	},

	suggest_sequence(frm) {
		if (!frm.doc.learning_unit || frm.doc.sequence) return;
		frappe.db.get_list("Lesson", {
			filters: { learning_unit: frm.doc.learning_unit },
			fields: ["sequence"],
			order_by: "sequence desc",
			limit: 1,
		}).then((rows) => {
			frm.set_value("sequence", (rows.length ? (rows[0].sequence || 0) : 0) + 1);
		});
	},

	filter_objectives(frm) {
		// The Lesson Objective grid should only offer Learning Objectives
		// whose Competency belongs to this Lesson's own Learning Unit ->
		// Curriculum, not the whole site's objectives. Learning Objective has
		// no direct curriculum field, so resolve it via Competency first.
		if (!frm.doc.learning_unit) {
			frm.set_query("learning_objective", "objectives", () => ({ filters: { name: ["in", []] } }));
			return;
		}
		frappe.db.get_value("Learning Unit", frm.doc.learning_unit, "curriculum").then((r) => {
			const curriculum = r.message && r.message.curriculum;
			if (!curriculum) return;
			frappe.db.get_list("Competency", { filters: { curriculum }, pluck: "name", limit: 500 }).then((names) => {
				frm.set_query("learning_objective", "objectives", () => ({
					filters: { competency: ["in", names.length ? names : [""]] },
				}));
			});
		});
	},
});
