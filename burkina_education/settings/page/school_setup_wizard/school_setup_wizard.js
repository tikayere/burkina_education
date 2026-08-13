// Copyright (c) 2026, Burkina Education Project and contributors
// For license information, please see license.txt

/* Guided School Setup Wizard (master.md §7) - see setup/wizard.py for why
 * this is a Desk Page rather than a slide onto Frappe's own core Setup
 * Wizard (which only ever runs once, before the site's first login, and a
 * School Director configuring their school is not the same moment as
 * Administrator creating the site - see docs/installation.md) or a route in
 * the Vue Portal SPA (whoever runs this is *creating* the School/roles the
 * Portal's own routing depends on, so it has to work before any of that
 * exists - see docs/architecture.md section N).
 *
 * Each step is a plain object {key, label, render(container)} pushed into
 * `this.steps`; `render()` builds its fields with frappe.ui.form.make_control
 * (proper Link/Date/Select/Attach widgets, not raw <input>s) and returns
 * nothing - the step reads its own controls back on save via `this.controls`.
 */

frappe.pages["school-setup-wizard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Assistant de configuration de l'école"),
		single_column: true,
	});
	wrapper.setup_wizard = new burkina_education.SchoolSetupWizard(page);
};

frappe.provide("burkina_education");

burkina_education.SchoolSetupWizard = class SchoolSetupWizard {
	// frappe.utils has no generic deep-clone helper - JSON round-trip is
	// enough here (the structure selection is plain strings/arrays, no
	// dates/functions to lose).
	static deep_clone(obj) {
		return JSON.parse(JSON.stringify(obj));
	}

	constructor(page) {
		this.page = page;
		this.status = {};
		this.controls = {};
		this.currentStepIndex = 0;

		this.steps = [
			{ key: "school", label: __("École"), fn: "save_school", finish_label: __("Enregistrer et continuer") },
			{ key: "academic_year", label: __("Année scolaire"), fn: "save_academic_year", finish_label: __("Enregistrer et continuer") },
			{ key: "terms", label: __("Trimestres"), finish_label: __("Générer les trimestres") },
			{ key: "structure", label: __("Structure scolaire"), finish_label: __("Créer la structure sélectionnée") },
			{ key: "grading", label: __("Barème de notation"), fn: "save_grading_scheme", finish_label: __("Enregistrer et continuer") },
			{ key: "users", label: __("Utilisateurs"), finish_label: __("Envoyer les invitations") },
			{ key: "done", label: __("Terminé"), finish_label: __("Terminer") },
		];

		this.build_shell();
		this.load();
	}

	build_shell() {
		$(this.page.body).empty().append(`
			<div class="setup-wizard-shell row">
				<div class="col-md-3">
					<ul class="nav nav-pills flex-column setup-wizard-steps"></ul>
				</div>
				<div class="col-md-9">
					<div class="setup-wizard-step-body"></div>
					<div class="setup-wizard-actions" style="margin-top: 20px;"></div>
				</div>
			</div>
		`);
		this.$steps = $(this.page.body).find(".setup-wizard-steps");
		this.$body = $(this.page.body).find(".setup-wizard-step-body");
		this.$actions = $(this.page.body).find(".setup-wizard-actions");
	}

	async load() {
		this.status = await this.call("get_status");
		this.render_step_list();
		this.goto_step(this.first_incomplete_step_index());
	}

	first_incomplete_step_index() {
		if (!this.status.school) return 0;
		if (!this.status.academic_year) return 1;
		if (!this.status.terms || !this.status.terms.length) return 2;
		if (!this.status.structure || !this.status.structure.grades) return 3;
		if (!this.status.grading_scheme) return 4;
		return this.status.completed ? 6 : 5;
	}

	render_step_list() {
		this.$steps.empty();
		this.steps.forEach((step, i) => {
			const done = this.is_step_done(step.key);
			const $li = $(`
				<li class="setup-wizard-step-nav" data-idx="${i}" style="cursor:pointer;">
					<a>
						<span class="indicator ${done ? "green" : "gray"}"></span>
						${step.label}
					</a>
				</li>
			`);
			$li.on("click", () => this.goto_step(i));
			this.$steps.append($li);
		});
	}

	is_step_done(key) {
		switch (key) {
			case "school":
				return !!this.status.school;
			case "academic_year":
				return !!this.status.academic_year;
			case "terms":
				return !!(this.status.terms && this.status.terms.length);
			case "structure":
				return !!(this.status.structure && this.status.structure.grades);
			case "grading":
				return !!this.status.grading_scheme;
			case "users":
				return this.usersInvited || false;
			case "done":
				return !!this.status.completed;
			default:
				return false;
		}
	}

	goto_step(idx) {
		this.currentStepIndex = idx;
		this.$steps.find("li").removeClass("active");
		this.$steps.find(`li[data-idx="${idx}"]`).addClass("active");
		this.render_current_step();
	}

	render_current_step() {
		const step = this.steps[this.currentStepIndex];
		this.$body.empty();
		this.$actions.empty();
		this.controls = {};

		const renderers = {
			school: () => this.render_school_step(),
			academic_year: () => this.render_academic_year_step(),
			terms: () => this.render_terms_step(),
			structure: () => this.render_structure_step(),
			grading: () => this.render_grading_step(),
			users: () => this.render_users_step(),
			done: () => this.render_done_step(),
		};
		renderers[step.key]();
	}

	// -- field helper --------------------------------------------------

	make_field(df, value) {
		const $wrapper = $(`<div class="setup-wizard-field frappe-control" style="margin-bottom: 12px;"></div>`).appendTo(this.$fieldset);
		const control = frappe.ui.form.make_control({
			parent: $wrapper,
			df: Object.assign({ fieldtype: "Data" }, df),
			render_input: true,
		});
		if (value !== undefined && value !== null) control.set_value(value);
		this.controls[df.fieldname] = control;
		return control;
	}

	start_fieldset(description) {
		this.$fieldset = $(`<div></div>`).appendTo(this.$body);
		if (description) {
			$(`<p class="text-muted">${description}</p>`).appendTo(this.$body).insertBefore(this.$fieldset);
		}
	}

	add_action(label, handler, opts = {}) {
		const $btn = $(`<button class="btn btn-primary btn-sm">${label}</button>`);
		$btn.on("click", async () => {
			$btn.prop("disabled", true);
			try {
				await handler();
			} finally {
				$btn.prop("disabled", false);
			}
		});
		this.$actions.append($btn);
		if (opts.secondary_label) {
			const $skip = $(`<button class="btn btn-default btn-sm" style="margin-left: 8px;">${opts.secondary_label}</button>`);
			$skip.on("click", opts.secondary_handler);
			this.$actions.append($skip);
		}
	}

	call(method, args) {
		return frappe.call({ method: `burkina_education.setup.wizard.${method}`, args, freeze: true }).then((r) => r.message);
	}

	next_step() {
		if (this.currentStepIndex < this.steps.length - 1) this.goto_step(this.currentStepIndex + 1);
	}

	// -- steps -----------------------------------------------------------

	render_school_step() {
		const s = this.status.school || {};
		this.start_fieldset(
			__("Identité de l'école - nom, code, coordonnées et logo. Ces informations apparaissent sur les bulletins, reçus et documents officiels.")
		);
		this.make_field({ fieldname: "school_name", label: __("Nom de l'école"), reqd: 1 }, s.school_name);
		this.make_field({ fieldname: "school_code", label: __("Code établissement"), reqd: 1 }, s.school_code);
		this.make_field({ fieldname: "official_name", label: __("Dénomination officielle") }, s.official_name);
		this.make_field(
			{ fieldname: "school_type", label: __("Type d'école"), fieldtype: "Select", options: "\nPublic\nPrivé\nConfessionnel\nCommunautaire\nAutre" },
			s.school_type
		);
		this.make_field({ fieldname: "logo", label: __("Logo"), fieldtype: "Attach Image" }, s.logo);
		this.make_field({ fieldname: "address_line1", label: __("Adresse") }, s.address_line1);
		this.make_field({ fieldname: "city", label: __("Ville") }, s.city);
		this.make_field({ fieldname: "province", label: __("Province / Région") }, s.province);
		this.make_field({ fieldname: "country", label: __("Pays"), fieldtype: "Link", options: "Country" }, s.country || "Burkina Faso");
		this.make_field({ fieldname: "phone", label: __("Téléphone") }, s.phone);
		this.make_field({ fieldname: "email", label: __("E-mail") }, s.email);

		this.add_action(this.steps[0].finish_label, async () => {
			const data = {};
			Object.keys(this.controls).forEach((f) => (data[f] = this.controls[f].get_value()));
			if (!data.school_name || !data.school_code) {
				frappe.msgprint(__("Le nom et le code de l'école sont obligatoires."));
				return;
			}
			this.status.school = await this.call("save_school", { data });
			frappe.show_alert({ message: __("École enregistrée."), indicator: "green" });
			this.render_step_list();
			this.next_step();
		});
	}

	render_academic_year_step() {
		const y = this.status.academic_year || {};
		this.start_fieldset(__("L'année scolaire en cours (par ex. 2026-2027) - point de départ pour les trimestres, classes et frais."));
		this.make_field({ fieldname: "academic_year_name", label: __("Nom de l'année scolaire"), reqd: 1, description: __("Exemple : 2026-2027") }, y.academic_year_name);
		this.make_field({ fieldname: "year_start_date", label: __("Date de début"), fieldtype: "Date", reqd: 1 }, y.year_start_date);
		this.make_field({ fieldname: "year_end_date", label: __("Date de fin"), fieldtype: "Date", reqd: 1 }, y.year_end_date);

		this.add_action(this.steps[1].finish_label, async () => {
			const data = {};
			Object.keys(this.controls).forEach((f) => (data[f] = this.controls[f].get_value()));
			if (!data.academic_year_name || !data.year_start_date || !data.year_end_date) {
				frappe.msgprint(__("L'année scolaire et ses dates sont obligatoires."));
				return;
			}
			this.status.academic_year = await this.call("save_academic_year", { data });
			frappe.show_alert({ message: __("Année scolaire enregistrée."), indicator: "green" });
			this.render_step_list();
			this.next_step();
		});
	}

	render_terms_step() {
		if (!this.status.academic_year) {
			this.start_fieldset();
			$(`<p>${__("Configurez d'abord l'année scolaire (étape précédente).")}</p>`).appendTo(this.$body);
			return;
		}
		this.start_fieldset(
			__("Génère automatiquement des trimestres répartis sur l'année scolaire (modifiables ensuite comme n'importe quel Trimestre académique).")
		);
		this.make_field(
			{ fieldname: "term_count", label: __("Nombre de trimestres/semestres"), fieldtype: "Int" },
			this.status.terms_per_year || 3
		);

		const $existing = $(`<div class="setup-wizard-terms" style="margin-top: 16px;"></div>`).appendTo(this.$body);
		this.render_terms_list($existing, this.status.terms);

		this.add_action(this.steps[2].finish_label, async () => {
			const term_count = this.controls.term_count.get_value();
			const result = await this.call("save_terms", { academic_year: this.status.academic_year.name, term_count });
			this.status.terms = result.terms;
			this.render_terms_list($existing, result.terms);
			frappe.show_alert({ message: __("Trimestres générés."), indicator: "green" });
			this.render_step_list();
			this.next_step();
		});
	}

	render_terms_list($container, terms) {
		$container.empty();
		if (!terms || !terms.length) return;
		const rows = terms
			.map((t) => `<tr><td>${frappe.utils.escape_html(t.term_name)}</td><td>${frappe.datetime.str_to_user(t.term_start_date)}</td><td>${frappe.datetime.str_to_user(t.term_end_date)}</td></tr>`)
			.join("");
		$container.append(`<table class="table table-bordered"><thead><tr><th>${__("Trimestre")}</th><th>${__("Début")}</th><th>${__("Fin")}</th></tr></thead><tbody>${rows}</tbody></table>`);
	}

	async render_structure_step() {
		if (!this.status.school) {
			this.start_fieldset();
			$(`<p>${__("Configurez d'abord l'école (étape 1).")}</p>`).appendTo(this.$body);
			return;
		}
		this.start_fieldset(
			__("Structure standard d'une école au Burkina Faso (préscolaire, primaire, collège, lycée) - décochez ce qui ne s'applique pas à votre établissement, ou ajustez plus tard depuis Structure scolaire.")
		);
		if (!this.defaultStructure) {
			this.defaultStructure = await this.call("get_default_structure");
		}
		this.structureSelection = burkina_education.SchoolSetupWizard.deep_clone(this.defaultStructure);

		const $tree = $(`<div class="setup-wizard-structure"></div>`).appendTo(this.$body);
		this.structureSelection.forEach((level, li) => {
			const $level = $(`
				<div style="margin-bottom: 10px;">
					<label><input type="checkbox" checked data-level="${li}" class="level-check"> <b>${frappe.utils.escape_html(level.education_level)}</b></label>
					<div style="margin-left: 24px;"></div>
				</div>
			`);
			const $cycles = $level.find("div");
			level.cycles.forEach((cycle, ci) => {
				const gradeChecks = cycle.grades
					.map(
						(g, gi) =>
							`<label style="margin-right: 12px;"><input type="checkbox" checked data-level="${li}" data-cycle="${ci}" data-grade="${gi}" class="grade-check"> ${frappe.utils.escape_html(g)}</label>`
					)
					.join("");
				$cycles.append(`<div style="margin: 4px 0;"><i>${frappe.utils.escape_html(cycle.cycle)}</i><br>${gradeChecks}</div>`);
			});
			$tree.append($level);
		});

		$tree.on("change", ".level-check", (e) => {
			const li = $(e.target).data("level");
			$tree.find(`.grade-check[data-level="${li}"]`).prop("checked", e.target.checked);
		});

		this.add_action(this.steps[3].finish_label, async () => {
			const selection = burkina_education.SchoolSetupWizard.deep_clone(this.structureSelection);
			$tree.find(".grade-check:not(:checked)").each((_i, el) => {
				const $el = $(el);
				const li = $el.data("level"),
					ci = $el.data("cycle"),
					gi = $el.data("grade");
				selection[li].cycles[ci].grades[gi] = null;
			});
			selection.forEach((level) => {
				level.cycles.forEach((cycle) => {
					cycle.grades = cycle.grades.filter(Boolean);
				});
				level.cycles = level.cycles.filter((c) => c.grades.length);
			});
			const finalSelection = selection.filter((l) => l.cycles.length);
			const created = await this.call("save_structure", { selection: finalSelection });
			frappe.show_alert({
				message: __("Structure créée : {0} niveaux, {1} cycles, {2} classes.", [created.education_levels, created.cycles, created.grades]),
				indicator: "green",
			});
			this.status.structure = { education_levels: 1, cycles: 1, grades: 1 };
			this.render_step_list();
			this.next_step();
		});
	}

	render_grading_step() {
		const g = this.status.grading_scheme || {};
		this.start_fieldset(__("Barème de notation par défaut, appliqué à toute l'école sauf configuration spécifique par niveau (voir Pédagogie)."));
		this.make_field({ fieldname: "scheme_name", label: __("Nom du barème") }, g.name || __("Barème standard"));
		this.make_field({ fieldname: "score_max", label: __("Note maximale"), fieldtype: "Float" }, g.score_max || 20);
		this.make_field({ fieldname: "passing_score", label: __("Note de passage"), fieldtype: "Float" }, g.passing_score || 10);

		this.add_action(this.steps[4].finish_label, async () => {
			const data = {};
			Object.keys(this.controls).forEach((f) => (data[f] = this.controls[f].get_value()));
			this.status.grading_scheme = await this.call("save_grading_scheme", { data });
			frappe.show_alert({ message: __("Barème de notation enregistré."), indicator: "green" });
			this.render_step_list();
			this.next_step();
		});
	}

	render_users_step() {
		this.start_fieldset(
			__("Invitez le personnel clé - chacun reçoit un e-mail pour définir son mot de passe. Vous pourrez ajouter d'autres utilisateurs plus tard depuis Utilisateurs (Desk) ou l'école.")
		);
		const roles = ["School Director", "Academic Director", "Secretary", "Accountant", "Registrar"];
		this.userRows = [];
		const $rows = $(`<div class="setup-wizard-user-rows"></div>`).appendTo(this.$body);

		const addRow = (role) => {
			const rowIdx = this.userRows.length;
			this.userRows.push({});
			const $row = $(`
				<div class="row" style="margin-bottom: 8px;">
					<div class="col-md-4"><input type="text" class="form-control input-sm user-name" placeholder="${__("Nom complet")}"></div>
					<div class="col-md-4"><input type="email" class="form-control input-sm user-email" placeholder="${__("E-mail")}"></div>
					<div class="col-md-4"><select class="form-control input-sm user-role">${roles.map((r) => `<option value="${r}" ${r === role ? "selected" : ""}>${__(r)}</option>`).join("")}</select></div>
				</div>
			`);
			$row.data("idx", rowIdx);
			$rows.append($row);
		};
		roles.slice(0, 3).forEach((r) => addRow(r));

		this.$body.append(`<button class="btn btn-default btn-xs setup-wizard-add-row" style="margin-bottom: 16px;">+ ${__("Ajouter une ligne")}</button>`);
		this.$body.find(".setup-wizard-add-row").on("click", () => addRow(roles[0]));

		this.add_action(this.steps[5].finish_label, async () => {
			const users = [];
			$rows.find(".row").each((_i, el) => {
				const $el = $(el);
				const email = $el.find(".user-email").val();
				const full_name = $el.find(".user-name").val();
				const role = $el.find(".user-role").val();
				if (email) users.push({ email, full_name, role });
			});
			if (!users.length) {
				this.usersInvited = true;
				this.render_step_list();
				this.next_step();
				return;
			}
			const result = await this.call("invite_users", { users });
			frappe.show_alert({ message: __("{0} invitation(s) envoyée(s).", [result.length]), indicator: "green" });
			this.usersInvited = true;
			this.render_step_list();
			this.next_step();
		}, {
			secondary_label: __("Passer cette étape"),
			secondary_handler: () => {
				this.usersInvited = true;
				this.render_step_list();
				this.next_step();
			},
		});
	}

	render_done_step() {
		this.start_fieldset();
		this.$body.append(`
			<div class="text-center" style="padding: 40px 0;">
				<h4>${this.status.completed ? __("Configuration terminée !") : __("Presque terminé")}</h4>
				<p class="text-muted">${__("L'école est configurée. Le personnel invité peut se connecter, et vous pouvez continuer la configuration (frais, moyens de paiement, communication) depuis le Bureau (Desk).")}</p>
			</div>
		`);
		if (!this.status.completed) {
			this.add_action(this.steps[6].finish_label, async () => {
				await this.call("finish");
				this.status.completed = true;
				this.render_step_list();
				this.render_current_step();
				frappe.show_alert({ message: __("Configuration marquée comme terminée."), indicator: "green" });
			});
		} else {
			this.$actions.append(`<a class="btn btn-default btn-sm" href="/app/school">${__("Voir l'école")}</a>`);
			this.$actions.append(`<a class="btn btn-default btn-sm" href="/portal" style="margin-left: 8px;">${__("Ouvrir le portail")}</a>`);
		}
	}
};
