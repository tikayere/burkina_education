// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("School", {
	refresh(frm) {
		frm.dashboard.set_headline_alert(
			frm.doc.is_active
				? ""
				: `<div class="alert alert-warning" style="margin-bottom: 0;">${__("Cet établissement est marqué comme inactif.")}</div>`
		);

		if (!frm.is_new()) {
			frm.add_custom_button(__("Campus"), () => {
				frappe.set_route("List", "Campus", { school: frm.doc.name });
			}, __("Voir"));
			frm.add_custom_button(__("Classes (Grades)"), () => {
				frappe.set_route("List", "Grade", { school: frm.doc.name });
			}, __("Voir"));
			frm.add_custom_button(__("Élèves"), () => {
				frappe.set_route("List", "Student", { school: frm.doc.name });
			}, __("Voir"));

			frm.add_custom_button(__("Nouveau campus"), () => {
				frappe.new_doc("Campus", { school: frm.doc.name });
			}, __("Créer"));
		}
	},

	company(frm) {
		// Keep the school's default currency in step with its linked
		// accounting Company, since Sales Invoices generated from Fee
		// Schedules are created in the Company's currency (docs/architecture.md
		// section H).
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency").then((r) => {
				if (r.message && r.message.default_currency && !frm.doc.default_currency) {
					frm.set_value("default_currency", r.message.default_currency);
				}
			});
		}
	},
});
