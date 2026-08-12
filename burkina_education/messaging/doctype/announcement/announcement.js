// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Draft: "gray",
	Published: "green",
	Archived: "dark grey",
};

const REFERENCE_DOCTYPE_BY_AUDIENCE = {
	"Education Level": "Education Level",
	Grade: "Grade",
	"Student Group": "Student Group",
};

frappe.ui.form.on("Announcement", {
	refresh(frm) {
		if (frm.doc.publication_status) {
			frm.page.set_indicator(__(frm.doc.publication_status), STATUS_COLORS[frm.doc.publication_status] || "gray");
		}

		if (frm.doc.publication_status === "Draft" && !frm.is_new() && !frm.is_dirty()) {
			frm.add_custom_button(__("Aperçu de l'audience"), () => {
				frm.call("preview_audience").then((r) => {
					const c = r.message || {};
					frappe.msgprint({
						title: __("Audience estimée"),
						message: __("Tuteurs: {0} · Élèves: {1} · Enseignants: {2}", [
							c.guardians || 0,
							c.students || 0,
							c.users || 0,
						]),
					});
				});
			});

			frm.add_custom_button(__("Publier"), () => {
				const channels = [];
				if (frm.doc.notify_sms) channels.push(__("SMS"));
				if (frm.doc.notify_whatsapp) channels.push(__("WhatsApp"));
				if (frm.doc.notify_email) channels.push(__("E-mail"));
				if (frm.doc.notify_in_app) channels.push(__("dans l'application"));

				frappe.confirm(
					__("Publier cette annonce et notifier l'audience ({0}) ?", [channels.join(", ") || __("aucun canal sélectionné")]),
					() => {
						frm.call("publish").then(() => frm.reload_doc());
					}
				);
			}).addClass("btn-primary");
		}

		if (frm.doc.publication_status === "Published") {
			frm.add_custom_button(__("Archiver"), () => {
				frm.call("archive").then(() => frm.reload_doc());
			});
			frm.add_custom_button(__("Journal des envois"), () => {
				frappe.set_route("List", "Message Log", { reference_doctype: "Announcement", reference_name: frm.doc.name });
			}, __("Voir"));
		}
	},

	audience_type(frm) {
		frm.set_value("audience_reference_doctype", REFERENCE_DOCTYPE_BY_AUDIENCE[frm.doc.audience_type] || "");
		frm.set_value("audience_reference", "");
	},
});
