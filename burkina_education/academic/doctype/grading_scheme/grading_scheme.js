// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Grading Scheme", {
	refresh(frm) {
		frm.trigger("use_coefficients");
		frm.trigger("warn_other_default");

		if (!frm.is_new()) {
			frm.add_custom_button(__("Bulletins utilisant ce barème"), () => {
				frappe.set_route("List", "Student Term Report", { grading_scheme: frm.doc.name });
			});
		}
	},

	use_coefficients(frm) {
		// "Weighted by Coefficient" is meaningless once coefficients are
		// switched off - keep the two averaging methods consistent with it
		// instead of letting the form save a contradictory combination.
		frm.set_df_property("term_average_method", "read_only", !frm.doc.use_coefficients);
		if (!frm.doc.use_coefficients && frm.doc.term_average_method !== "Simple Average") {
			frm.set_value("term_average_method", "Simple Average");
		}
	},

	is_default(frm) {
		frm.trigger("warn_other_default");
	},

	education_level(frm) {
		frm.trigger("warn_other_default");
	},

	warn_other_default(frm) {
		frm.dashboard.clear_headline();
		if (!frm.doc.is_default) return;

		frappe.db.get_list("Grading Scheme", {
			filters: {
				is_default: 1,
				education_level: frm.doc.education_level || "",
				name: ["!=", frm.doc.name || ""],
			},
			fields: ["name"],
			limit: 1,
		}).then((rows) => {
			if (rows.length) {
				frm.dashboard.set_headline_alert(
					`<div class="alert alert-warning" style="margin-bottom: 0;">${__(
						"{0} est déjà le barème par défaut pour ce niveau - en enregistrer un second créera une ambiguïté.",
						[frappe.utils.get_form_link("Grading Scheme", rows[0].name, true)]
					)}</div>`
				);
			}
		});
	},
});
