// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Draft: "gray",
	Scheduled: "blue",
	Ongoing: "orange",
	Completed: "green",
	Cancelled: "red",
};

// Forward transitions offered as one-click buttons, in order - mirrors the
// options list on Examination Schedule.status (docs/architecture.md section G).
const NEXT_STATUS = {
	Draft: "Scheduled",
	Scheduled: "Ongoing",
	Ongoing: "Completed",
};

frappe.ui.form.on("Examination", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		if (frm.is_new()) return;

		frm.add_custom_button(__("Créneau d'examen"), () => {
			frappe.new_doc("Examination Schedule", {
				examination: frm.doc.name,
				academic_year: frm.doc.academic_year,
			});
		}, __("Nouveau"));

		frm.add_custom_button(__("Créneaux"), () => {
			frappe.set_route("List", "Examination Schedule", { examination: frm.doc.name });
		}, __("Voir"));

		const next = NEXT_STATUS[frm.doc.status];
		if (next) {
			frm.add_custom_button(__("Marquer {0}", [__(next)]), () => {
				frm.set_value("status", next);
				frm.save();
			});
		}
		if (frm.doc.status !== "Cancelled" && frm.doc.status !== "Completed") {
			frm.add_custom_button(__("Annuler"), () => {
				frappe.confirm(__("Annuler cette session d'examen ?"), () => {
					frm.set_value("status", "Cancelled");
					frm.save();
				});
			});
		}
	},
});
