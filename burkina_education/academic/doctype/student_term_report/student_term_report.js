// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Term Report", {
	refresh(frm) {
		frm.trigger("set_pass_fail_indicator");

		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.add_custom_button(__("Calculer les moyennes"), () => {
				frappe.dom.freeze(__("Calcul en cours..."));
				frm.call("compute")
					.then(() => frm.reload_doc())
					.finally(() => frappe.dom.unfreeze());
			});
		}

		if (!frm.is_new() && frm.doc.student_group && frm.doc.academic_term) {
			frm.add_custom_button(__("Classer la classe"), () => {
				frappe.confirm(
					__("Calculer le rang de tous les bulletins soumis de {0} pour {1} ?", [
						frm.doc.student_group,
						frm.doc.academic_term,
					]),
					() => {
						frappe.dom.freeze(__("Classement en cours..."));
						frappe.call({
							method: "burkina_education.academic.ranking.rank_term_reports",
							args: { student_group: frm.doc.student_group, academic_term: frm.doc.academic_term },
						}).then(() => {
							frappe.show_alert({ message: __("Classement terminé."), indicator: "green" });
							frm.reload_doc();
						}).finally(() => frappe.dom.unfreeze());
					}
				);
			}, __("Actions"));
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("Autres bulletins de cet élève"), () => {
				frappe.set_route("List", "Student Term Report", { student: frm.doc.student });
			}, __("Voir"));
			frm.add_custom_button(__("Bulletin annuel"), () => {
				frappe.set_route("List", "Student Annual Report", {
					student: frm.doc.student,
					academic_year: frm.doc.academic_year,
				});
			}, __("Voir"));
		}
	},

	term_average(frm) {
		frm.trigger("set_pass_fail_indicator");
	},

	set_pass_fail_indicator(frm) {
		if (frm.doc.term_average === null || frm.doc.term_average === undefined || !frm.doc.grading_scheme) {
			return;
		}
		frappe.db.get_value("Grading Scheme", frm.doc.grading_scheme, "passing_score").then((r) => {
			const passing = r.message && r.message.passing_score;
			if (passing === undefined || passing === null) return;
			const passed = frm.doc.term_average >= passing;
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-${passed ? "success" : "danger"}" style="margin-bottom: 0;">${
					passed ? __("Moyenne suffisante pour valider le trimestre.") : __("Moyenne inférieure à la note de passage ({0}).", [passing])
				}</div>`
			);
		});
	},
});
