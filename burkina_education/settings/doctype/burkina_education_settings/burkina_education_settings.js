// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

frappe.ui.form.on("Burkina Education Settings", {
	refresh(frm) {
		frm.trigger("check_duplicate_ranks");
	},

	sibling_discount_rules_add(frm) {
		frm.trigger("check_duplicate_ranks");
	},
	sibling_discount_rules_remove(frm) {
		frm.trigger("check_duplicate_ranks");
	},

	check_duplicate_ranks(frm) {
		frm.dashboard.clear_headline();
		const ranks = (frm.doc.sibling_discount_rules || []).map((r) => r.sibling_rank).filter(Boolean);
		const duplicates = ranks.filter((rank, i) => ranks.indexOf(rank) !== i);
		if (duplicates.length) {
			frm.dashboard.set_headline_alert(
				`<div class="alert alert-warning" style="margin-bottom: 0;">${__(
					"Plusieurs règles de réduction fratrie utilisent le même rang ({0}) - seule la première rencontrée sera appliquée.",
					[[...new Set(duplicates)].join(", ")]
				)}</div>`
			);
		}
	},
});

frappe.ui.form.on("Sibling Discount Rule", {
	sibling_rank(frm) {
		frm.trigger("check_duplicate_ranks");
	},
});
