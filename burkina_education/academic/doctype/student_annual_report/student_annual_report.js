// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const DECISION_COLORS = {
	"En attente": "orange",
	Admis: "green",
	Redouble: "red",
};

frappe.ui.form.on("Student Annual Report", {
	refresh(frm) {
		if (frm.doc.decision) {
			frm.page.set_indicator(__(frm.doc.decision), DECISION_COLORS[frm.doc.decision] || "gray");
		}

		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.add_custom_button(__("Calculer la moyenne annuelle"), () => {
				frappe.dom.freeze(__("Calcul en cours..."));
				frm.call("compute")
					.then(() => frm.reload_doc())
					.finally(() => frappe.dom.unfreeze());
			});
		}

		if (!frm.is_new() && frm.doc.grade && frm.doc.academic_year) {
			frm.add_custom_button(__("Classer la promotion"), () => {
				frappe.confirm(
					__("Calculer le rang annuel de tous les bulletins soumis de {0} pour {1} ?", [
						frm.doc.grade,
						frm.doc.academic_year,
					]),
					() => {
						frappe.dom.freeze(__("Classement en cours..."));
						frappe.call({
							method: "burkina_education.academic.ranking.rank_annual_reports",
							args: { grade: frm.doc.grade, academic_year: frm.doc.academic_year },
						}).then(() => {
							frappe.show_alert({ message: __("Classement terminé."), indicator: "green" });
							frm.reload_doc();
						}).finally(() => frappe.dom.unfreeze());
					}
				);
			}, __("Actions"));
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Bulletins trimestriels"), () => {
				frappe.set_route("List", "Student Term Report", {
					student: frm.doc.student,
					academic_year: frm.doc.academic_year,
				});
			}, __("Voir"));
		}
	},

	decision(frm) {
		if (frm.doc.decision) {
			frm.page.set_indicator(__(frm.doc.decision), DECISION_COLORS[frm.doc.decision] || "gray");
		}
	},
});
