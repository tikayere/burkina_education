// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Guardian", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.user) {
			frm.dashboard.add_indicator(__("Accès au portail parent activé"), "green");
			return;
		}

		frm.add_custom_button(__("Inviter au portail parent"), () => {
			if (!frm.doc.email_address) {
				frappe.msgprint(__("Veuillez d'abord renseigner l'adresse e-mail du tuteur."));
				return;
			}
			frappe.confirm(
				__("Créer un compte portail pour {0} et envoyer un e-mail de bienvenue à {1} ?", [frm.doc.guardian_name, frm.doc.email_address]),
				() => {
					frappe.call({
						method: "burkina_education.messaging.portal.invite_guardian",
						args: { guardian: frm.doc.name },
						callback: () => frm.reload_doc(),
					});
				}
			);
		});
	},
});
