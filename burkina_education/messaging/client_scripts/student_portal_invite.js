// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.user) {
			frm.dashboard.add_indicator(__("Accès au portail élève activé"), "green");
			return;
		}

		frm.add_custom_button(__("Inviter au portail élève"), () => {
			if (!frm.doc.student_email_id) {
				frappe.msgprint(__("Veuillez d'abord renseigner l'adresse e-mail de l'élève."));
				return;
			}
			frappe.confirm(
				__("Créer un compte portail pour {0} et envoyer un e-mail de bienvenue à {1} ?", [frm.doc.student_name, frm.doc.student_email_id]),
				() => {
					frappe.call({
						method: "burkina_education.messaging.portal.invite_student",
						args: { student: frm.doc.name },
						callback: () => frm.reload_doc(),
					});
				}
			);
		});
	},
});
