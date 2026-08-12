// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Notification Template", {
	refresh(frm) {
		if (!frm.doc.is_active) {
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-warning" style="margin-bottom: 0;">${__("Ce modèle est inactif : aucun message ne sera envoyé pour cet événement/canal tant qu'il n'est pas réactivé.")}</div>`
			);
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Journal des envois"), () => {
				frappe.set_route("List", "Message Log", { template: frm.doc.name });
			}, __("Voir"));
		}
	},

	event_key(frm) {
		// Re-trigger the server-side placeholder hint recompute on save by
		// nudging the field dirty; the actual list lives in
		// notification_template.py::PLACEHOLDER_HINTS.
		frm.dirty();
	},
});
