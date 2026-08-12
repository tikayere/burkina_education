// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Assessment Type", {
	refresh(frm) {
		frm.dashboard.set_headline_alert(
			frm.doc.is_active
				? ""
				: `<div class="alert alert-warning" style="margin-bottom: 0;">${__("Ce type d'évaluation est inactif et n'apparaîtra plus dans les nouveaux Plans d'évaluation.")}</div>`
		);
	},
});
