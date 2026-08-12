// Adds a "Paiement Mobile Money" button to submitted, outstanding Sales
// Invoices. Installed as a Frappe "Client Script" record (see
// setup/install.py::create_client_scripts) rather than editing ERPNext's own
// Sales Invoice form - the sanctioned way to extend a vendor doctype's UI
// without touching its source (master.md, docs/architecture.md section H).
frappe.ui.form.on("Sales Invoice", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || flt(frm.doc.outstanding_amount) <= 0) return;

		frm.add_custom_button(__("Paiement Mobile Money"), () => {
			frappe.db.get_list("Mobile Money Provider", {
				filters: { is_active: 1 },
				fields: ["name", "provider_name", "currency"],
			}).then((providers) => {
				if (!providers.length) {
					frappe.msgprint(__("Aucun fournisseur Mobile Money actif n'est configuré."));
					return;
				}
				const dialog = new frappe.ui.Dialog({
					title: __("Initier un paiement Mobile Money"),
					fields: [
						{
							fieldname: "provider",
							fieldtype: "Link",
							options: "Mobile Money Provider",
							label: __("Fournisseur"),
							reqd: 1,
							get_query: () => ({ filters: { is_active: 1 } }),
						},
						{
							fieldname: "phone_number",
							fieldtype: "Data",
							label: __("Numéro de téléphone"),
							reqd: 1,
						},
						{
							fieldname: "amount",
							fieldtype: "Currency",
							label: __("Montant"),
							default: frm.doc.outstanding_amount,
							description: __("Solde impayé : {0}", [format_currency(frm.doc.outstanding_amount, frm.doc.currency)]),
						},
					],
					primary_action_label: __("Envoyer la demande de paiement"),
					primary_action(values) {
						dialog.hide();
						frappe.dom.freeze(__("Initiation du paiement..."));
						frappe.call({
							method: "burkina_education.finance.mobile_money.api.initiate_payment",
							args: {
								reference_doctype: "Sales Invoice",
								reference_name: frm.doc.name,
								provider: values.provider,
								phone_number: values.phone_number,
								amount: values.amount,
							},
						}).then((r) => {
							if (r.message) {
								frappe.show_alert({
									message: __("Paiement initié ({0}). En attente de confirmation du fournisseur.", [r.message.transaction]),
									indicator: "blue",
								});
								frappe.set_route("Form", "Mobile Money Transaction", r.message.transaction);
							}
						}).finally(() => frappe.dom.unfreeze());
					},
				});
				dialog.show();
			});
		}, __("Créer"));
	},
});
