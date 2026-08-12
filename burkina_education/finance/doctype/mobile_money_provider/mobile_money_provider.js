// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mobile Money Provider", {
	refresh(frm) {
		frm.dashboard.set_headline_alert(
			frm.doc.sandbox_mode
				? `<div class="alert alert-warning" style="margin-bottom: 0;">${__("Mode bac à sable (sandbox) actif - aucune transaction réelle ne sera envoyée à {0}.", [frm.doc.provider_code || __("ce fournisseur")])}</div>`
				: ""
		);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Transactions"), () => {
				frappe.set_route("List", "Mobile Money Transaction", { provider: frm.doc.name });
			}, __("Voir"));
		}
	},

	is_active(frm) {
		if (frm.doc.is_active && (!frm.doc.api_base_url || !frm.doc.mode_of_payment)) {
			frappe.show_alert({
				message: __("Configurez l'URL de l'API et le Mode de paiement avant d'activer ce fournisseur."),
				indicator: "orange",
			});
		}
	},
});
