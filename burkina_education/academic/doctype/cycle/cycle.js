// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cycle", {
	refresh(frm) {
		frm.set_query("education_level", () => ({
			filters: frm.doc.school ? { school: frm.doc.school } : {},
		}));

		if (!frm.is_new()) {
			frm.add_custom_button(__("Classes (Grades)"), () => {
				frappe.set_route("List", "Grade", { cycle: frm.doc.name });
			});
		}
	},

	school(frm) {
		// A Cycle's Education Level must belong to the same School - clear a
		// stale selection instead of letting the two fall out of sync.
		if (frm.doc.education_level) {
			frappe.db.get_value("Education Level", frm.doc.education_level, "school").then((r) => {
				if (r.message && r.message.school && r.message.school !== frm.doc.school) {
					frm.set_value("education_level", "");
				}
			});
		}
	},
});
