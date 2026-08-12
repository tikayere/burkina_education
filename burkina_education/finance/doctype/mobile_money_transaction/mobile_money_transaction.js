// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Initiated: "blue",
	Pending: "orange",
	Success: "green",
	Failed: "red",
	Cancelled: "gray",
};

frappe.ui.form.on("Mobile Money Transaction", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		// Server-driven audit log (finance/mobile_money/api.py) - never
		// editable by hand, matches master.md §28 (verified callbacks only).
		frm.disable_save();

		if (frm.doc.reference_doctype && frm.doc.reference_name) {
			frm.add_custom_button(__("Facture"), () => {
				frappe.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_name);
			}, __("Voir"));
		}
		if (frm.doc.payment_entry) {
			frm.add_custom_button(__("Paiement"), () => {
				frappe.set_route("Form", "Payment Entry", frm.doc.payment_entry);
			}, __("Voir"));
		}
		if (["Pending", "Initiated"].includes(frm.doc.status)) {
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-info" style="margin-bottom: 0;">${__("En attente de la confirmation du fournisseur (webhook serveur-à-serveur). Le statut se met à jour automatiquement, aucune action requise ici.")}</div>`
			);
		}
	},
});
