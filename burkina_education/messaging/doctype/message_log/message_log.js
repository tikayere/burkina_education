// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Queued: "blue",
	Sent: "green",
	Delivered: "green",
	Failed: "red",
	Skipped: "gray",
};

frappe.ui.form.on("Message Log", {
	refresh(frm) {
		if (frm.doc.status) {
			frm.page.set_indicator(__(frm.doc.status), STATUS_COLORS[frm.doc.status] || "gray");
		}

		// Server-driven audit log (messaging/notify.py) - never editable
		// by hand, matches the same server-only-audit-log pattern as Mobile
		// Money Transaction (master.md §33: "every outgoing SMS should have
		// ... status, timestamp, provider response").
		frm.disable_save();

		if (frm.doc.reference_doctype && frm.doc.reference_name) {
			frm.add_custom_button(__("Document lié"), () => {
				frappe.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_name);
			}, __("Voir"));
		}
		if (frm.doc.recipient_doctype && frm.doc.recipient) {
			frm.add_custom_button(__("Destinataire"), () => {
				frappe.set_route("Form", frm.doc.recipient_doctype, frm.doc.recipient);
			}, __("Voir"));
		}

		if (frm.doc.status === "Failed") {
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-danger" style="margin-bottom: 0;">${__("Échec d'envoi - voir le champ Erreur ci-dessous.")}</div>`
			);
		}
	},
});
