// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	New: "red",
	Acknowledged: "orange",
	Notified: "green",
};

frappe.ui.form.on("Attendance Alert", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (frm.is_new()) return;

		if (frm.doc.status === "New") {
			frm.add_custom_button(__("Marquer comme pris en compte"), () => {
				frm.set_value("status", "Acknowledged");
				frm.save();
			});
		}
		if (frm.doc.status === "Acknowledged") {
			frm.add_custom_button(__("Marquer comme notifié au tuteur"), () => {
				frm.set_value("status", "Notified");
				frm.save();
			});
		}

		if (frm.doc.student && frm.doc.from_date && frm.doc.to_date) {
			frm.add_custom_button(__("Voir les présences"), () => {
				frappe.set_route("List", "Student Attendance", {
					student: frm.doc.student,
					date: ["between", [frm.doc.from_date, frm.doc.to_date]],
				});
			}, __("Voir"));
		}
	},
});
