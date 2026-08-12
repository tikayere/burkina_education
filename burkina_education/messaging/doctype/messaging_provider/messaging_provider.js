// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Messaging Provider", {
	refresh(frm) {
		frm.page.set_indicator(
			frm.doc.is_active ? __("Actif") : __("Inactif"),
			frm.doc.is_active ? "green" : "gray"
		);

		if (frm.doc.sandbox_mode) {
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-info" style="margin-bottom: 0;">${__("Mode bac à sable actif : tout message est marqué comme envoyé sans appel réel au fournisseur.")}</div>`
			);
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Messages envoyés"), () => {
				frappe.set_route("List", "Message Log", { provider: frm.doc.name });
			}, __("Voir"));
		}

		if (frm.doc.is_active && !frm.doc.api_base_url && !frm.doc.sandbox_mode) {
			frappe.msgprint({
				message: __("Aucune URL d'API n'est configurée et le mode bac à sable est désactivé : les envois échoueront."),
				indicator: "orange",
			});
		}
	},
});
