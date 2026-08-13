// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

// Desk buttons for the Admissions pipeline (master.md §13) on top of
// Education's own Student Applicant form - delivered as a Client Script
// fixture (setup/install.py::CLIENT_SCRIPTS), the same non-invasive
// vendor-DocType-extension mechanism as the Sales Invoice mobile money
// button (docs/architecture.md section I). The actual transitions are
// whitelisted Document methods on the overridden controller
// (admissions/overrides.py), called here with frm.call() exactly like
// Announcement.publish()/Student Boarding Assignment.check_out() already do.

const STATUS_COLORS = {
	Brouillon: "gray",
	Soumise: "blue",
	"En cours d'examen": "orange",
	Acceptée: "green",
	Rejetée: "red",
	"Liste d'attente": "yellow",
	Inscrite: "green",
	Retirée: "dark grey",
};

frappe.ui.form.on("Student Applicant", {
	refresh(frm) {
		if (frm.doc.application_status) {
			frm.page.set_indicator(__(frm.doc.application_status), STATUS_COLORS[frm.doc.application_status] || "gray");
		}

		if (frm.is_new() || frm.is_dirty() || !frappe.perm.has_perm(frm.doctype, 0, "write")) return;

		const status = frm.doc.application_status;

		if (status === "Brouillon") {
			frm.add_custom_button(__("Soumettre"), () => {
				frm.call("submit_application").then(() => frm.reload_doc());
			}).addClass("btn-primary");
		}

		if (status === "Soumise") {
			frm.add_custom_button(__("Démarrer l'examen du dossier"), () => {
				frm.call("start_review").then(() => frm.reload_doc());
			}).addClass("btn-primary");
		}

		if (status === "En cours d'examen" || status === "Liste d'attente") {
			frm.add_custom_button(
				__("Accepter"),
				() => recordDecision(frm, "Acceptée"),
				__("Décision")
			);
			frm.add_custom_button(
				__("Liste d'attente"),
				() => recordDecision(frm, "Liste d'attente"),
				__("Décision")
			);
			frm.add_custom_button(
				__("Rejeter"),
				() => recordDecision(frm, "Rejetée"),
				__("Décision")
			);
		}

		if (status === "Acceptée" && frm.doc.admission_fee_required && !frm.doc.admission_fee_paid) {
			frm.add_custom_button(__("Encaisser les frais d'inscription"), () => {
				frappe.prompt(
					[
						{
							fieldname: "mode_of_payment",
							fieldtype: "Link",
							options: "Mode of Payment",
							label: __("Mode de paiement"),
						},
					],
					(values) => {
						frm.call("collect_admission_fee", values).then(() => frm.reload_doc());
					},
					__("Encaisser les frais d'inscription"),
					__("Encaisser")
				);
			});
		}

		if (status === "Acceptée" && (!frm.doc.admission_fee_required || frm.doc.admission_fee_paid)) {
			frm.add_custom_button(__("Enrôler"), () => {
				frappe.confirm(
					__("Créer l'élève et l'inscription (Program Enrollment) à partir de cette candidature ?"),
					() => {
						frm.call("enroll").then((r) => {
							frm.reload_doc();
							if (r.message && r.message.student) {
								frappe.msgprint({
									title: __("Candidature enrôlée"),
									message: __("Élève créé : {0}", [
										`<a href="/app/student/${r.message.student}">${r.message.student}</a>`,
									]),
									indicator: "green",
								});
							}
						});
					}
				);
			}).addClass("btn-primary");
		}

		if (frm.doc.enrolled_student) {
			frm.add_custom_button(__("Élève"), () => {
				frappe.set_route("Form", "Student", frm.doc.enrolled_student);
			}, __("Voir"));
		}
		if (frm.doc.enrolled_program_enrollment) {
			frm.add_custom_button(__("Inscription"), () => {
				frappe.set_route("Form", "Program Enrollment", frm.doc.enrolled_program_enrollment);
			}, __("Voir"));
		}

		if (status !== "Inscrite" && status !== "Retirée") {
			frm.add_custom_button(__("Retirer la candidature"), () => {
				frappe.prompt(
					[{ fieldname: "reason", fieldtype: "Small Text", label: __("Motif") }],
					(values) => {
						frm.call("withdraw", values).then(() => frm.reload_doc());
					},
					__("Retirer la candidature"),
					__("Retirer")
				);
			});
		}
	},
});

function recordDecision(frm, decision) {
	frappe.prompt(
		[{ fieldname: "notes", fieldtype: "Small Text", label: __("Motif de la décision") }],
		(values) => {
			frm.call("record_decision", { decision, notes: values.notes }).then(() => frm.reload_doc());
		},
		__("Décision : {0}", [__(decision)]),
		__("Confirmer")
	);
}
