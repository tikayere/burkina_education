# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Guided School Setup Wizard (master.md §7).

``after_install`` (install.py) only ever creates *technical* scaffolding -
roles, custom fields, permissions - deliberately no School/Academic
Year/Grade data, since none of that is known until a real school configures
itself. Left as-is, a School Director would have to hand-create a School,
an Academic Year, every Education Level/Cycle/Grade, and a Grading Scheme
one Desk form at a time before the system is usable at all - exactly what
§7 says not to require.

This module is the backend for the Desk Page that walks through that setup
(``settings/page/school_setup_wizard``): one whitelisted "save this step"
function per step, each create-or-update (idempotent - safe to revisit and
correct any step later, not a one-shot install-time script), plus
``get_status()`` so the page can show what is already configured and
pre-fill it. Every step re-uses the same DocTypes the rest of the app (and
the Desk forms under Structure scolaire/Pédagogie) already reads and
writes - the wizard is a guided *front door* to that data, not a parallel
data model.
"""

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate

# ---------------------------------------------------------------------------
# Status (drives the Desk Page's step list + pre-fill)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_status():
	require_setup_role()
	settings = frappe.get_single("Burkina Education Settings")
	school = frappe.get_doc("School", settings.default_school) if settings.default_school else None
	academic_year = frappe.get_doc("Academic Year", school.default_academic_year) if school and school.default_academic_year else None
	terms = (
		frappe.get_all(
			"Academic Term",
			filters={"academic_year": academic_year.name},
			fields=["name", "term_name", "term_start_date", "term_end_date"],
			order_by="term_start_date asc",
		)
		if academic_year
		else []
	)
	structure_counts = {
		"education_levels": frappe.db.count("Education Level", {"school": school.name}) if school else 0,
		"cycles": frappe.db.count("Cycle", {"school": school.name}) if school else 0,
		"grades": frappe.db.count("Grade", {"school": school.name}) if school else 0,
	}
	# Scoped the same way save_grading_scheme() manages it (school-wide, no
	# education_level) - a school might separately have per-education-level
	# defaults (set from Pédagogie), which aren't what this step configures.
	grading_scheme = frappe.db.get_value(
		"Grading Scheme",
		{"is_default": 1, "education_level": ["is", "not set"]},
		["name", "score_max", "passing_score"],
		as_dict=True,
	)

	return {
		"completed": cint(settings.setup_wizard_completed),
		"school": school.as_dict() if school else None,
		"academic_year": academic_year.as_dict() if academic_year else None,
		"terms": terms,
		"structure": structure_counts,
		"grading_scheme": grading_scheme,
		"terms_per_year": cint(settings.academic_terms_per_year) or 3,
	}


def require_setup_role():
	if not set(frappe.get_roles()) & {"System Manager", "School Director"}:
		frappe.throw(
			_("Seuls le Directeur d'école et les administrateurs système peuvent utiliser cet assistant."),
			frappe.PermissionError,
		)


# ---------------------------------------------------------------------------
# Step 1 - School identity
# ---------------------------------------------------------------------------


@frappe.whitelist()
def save_school(data):
	require_setup_role()
	data = frappe.parse_json(data)
	if not data.get("school_code") or not data.get("school_name"):
		frappe.throw(_("Le nom et le code de l'école sont obligatoires."))

	if frappe.db.exists("School", data["school_code"]):
		school = frappe.get_doc("School", data["school_code"])
	else:
		school = frappe.new_doc("School")

	for field in (
		"school_name",
		"school_code",
		"official_name",
		"school_type",
		"ownership_type",
		"address_line1",
		"address_line2",
		"city",
		"province",
		"commune",
		"country",
		"phone",
		"email",
		"website",
		"logo",
		"timezone",
	):
		if field in data:
			school.set(field, data[field])
	school.default_currency = school.default_currency or "XOF"
	school.default_language = school.default_language or "fr"
	school.is_active = 1
	school.save(ignore_permissions=True)

	# A school needs at least one Campus before Students/Grades can point at
	# one (master.md §53) - a first "Campus principal" is created for free
	# rather than making that its own wizard step, editable/extendable later
	# from Structure scolaire like any other Campus.
	if not frappe.db.exists("Campus", {"school": school.name}):
		frappe.get_doc(
			{"doctype": "Campus", "campus_name": school.school_name, "school": school.name, "is_active": 1}
		).insert(ignore_permissions=True)

	settings = frappe.get_single("Burkina Education Settings")
	if not settings.default_school:
		settings.default_school = school.name
		settings.default_currency = school.default_currency
		settings.save(ignore_permissions=True)

	return school.as_dict()


# ---------------------------------------------------------------------------
# Step 2 - Academic year + terms
# ---------------------------------------------------------------------------


@frappe.whitelist()
def save_academic_year(data):
	require_setup_role()
	data = frappe.parse_json(data)
	for field in ("academic_year_name", "year_start_date", "year_end_date"):
		if not data.get(field):
			frappe.throw(_("L'année scolaire, sa date de début et sa date de fin sont obligatoires."))

	if frappe.db.exists("Academic Year", data["academic_year_name"]):
		year = frappe.get_doc("Academic Year", data["academic_year_name"])
	else:
		year = frappe.new_doc("Academic Year")
		year.academic_year_name = data["academic_year_name"]
	year.year_start_date = data["year_start_date"]
	year.year_end_date = data["year_end_date"]
	year.save(ignore_permissions=True)

	settings = frappe.get_single("Burkina Education Settings")
	if settings.default_school:
		frappe.db.set_value("School", settings.default_school, "default_academic_year", year.name)

	return year.as_dict()


@frappe.whitelist()
def save_terms(academic_year, term_count=None):
	"""Idempotent: splits the Academic Year's own date range into
	``term_count`` (default: Burkina Education Settings.academic_terms_per_year,
	itself defaulting to 3 - the standard Burkina trimester calendar) evenly
	sized Academic Terms, skipping any that already exist by name. A school
	that already created its own terms by hand (different names, different
	split) is left untouched - this only fills the gap, never overwrites.
	"""
	require_setup_role()
	if not frappe.db.exists("Academic Year", academic_year):
		frappe.throw(_("Année scolaire introuvable."))

	settings = frappe.get_single("Burkina Education Settings")
	term_count = cint(term_count) or cint(settings.academic_terms_per_year) or 3
	year = frappe.get_doc("Academic Year", academic_year)
	start, end = getdate(year.year_start_date), getdate(year.year_end_date)
	total_days = (end - start).days or 1
	span = total_days // term_count
	label = _("Semestre") if term_count == 2 else _("Trimestre")

	created = []
	for i in range(term_count):
		term_start = add_days(start, span * i)
		term_end = end if i == term_count - 1 else add_days(start, span * (i + 1) - 1)
		term_name = f"{label} {i + 1}"
		# Academic Term.autoname() (Education's own controller) always names
		# the doc "<academic_year> (<term_name>)" regardless of what's passed
		# in - checking existence has to match that exact computed name, not
		# a name of our own invention, or this "idempotent" check would never
		# actually match and re-running would hit Education's own
		# validate_duplication() as a hard duplicate-key error instead.
		computed_name = f"{year.name} ({term_name})"
		if frappe.db.exists("Academic Term", computed_name):
			continue
		term = frappe.new_doc("Academic Term")
		term.academic_year = year.name
		term.term_name = term_name
		term.term_start_date = term_start
		term.term_end_date = term_end
		term.sequence = i + 1
		term.weight = 1
		term.insert(ignore_permissions=True)
		created.append(term.name)

	return {
		"created": created,
		"terms": frappe.get_all(
			"Academic Term",
			filters={"academic_year": academic_year},
			fields=["name", "term_name", "term_start_date", "term_end_date"],
			order_by="term_start_date asc",
		),
	}


# ---------------------------------------------------------------------------
# Step 3 - School structure (Education Level > Cycle > Grade)
# ---------------------------------------------------------------------------

#: The standard Burkina Faso structure master.md §6 gives as an example -
#: offered as pre-checked defaults the administrator can deselect, never
#: silently forced (master.md §78: don't hard-code assumptions about
#: Burkina regulations). Every level/cycle/grade this creates is a normal
#: editable record afterwards, same as one created by hand from Structure
#: scolaire.
DEFAULT_STRUCTURE = [
	{
		"education_level": "Préscolaire",
		"cycles": [{"cycle": "Préscolaire", "grades": ["Petite Section", "Moyenne Section", "Grande Section"]}],
	},
	{
		"education_level": "Primaire",
		"cycles": [{"cycle": "Primaire", "grades": ["CP1", "CP2", "CE1", "CE2", "CM1", "CM2"]}],
	},
	{
		"education_level": "Post-primaire",
		"cycles": [{"cycle": "Collège", "grades": ["6ème", "5ème", "4ème", "3ème"]}],
	},
	{
		"education_level": "Secondaire",
		"cycles": [{"cycle": "Lycée", "grades": ["2nde", "1ère", "Terminale"]}],
	},
]


@frappe.whitelist()
def get_default_structure():
	require_setup_role()
	return DEFAULT_STRUCTURE


@frappe.whitelist()
def save_structure(selection):
	"""``selection``: the same shape as ``DEFAULT_STRUCTURE`` (education
	level/cycle/grade names), but only whatever the administrator left
	checked on the wizard page. Create-or-skip by name, so re-running (e.g.
	after adding one more grade by hand) never duplicates."""
	require_setup_role()
	selection = frappe.parse_json(selection)
	settings = frappe.get_single("Burkina Education Settings")
	if not settings.default_school:
		frappe.throw(_("Configurez d'abord l'école (étape 1)."))
	school = settings.default_school

	created = {"education_levels": 0, "cycles": 0, "grades": 0}
	for idx, level_row in enumerate(selection):
		level_name = level_row["education_level"]
		if not frappe.db.exists("Education Level", {"education_level_name": level_name, "school": school}):
			frappe.get_doc(
				{
					"doctype": "Education Level",
					"education_level_name": level_name,
					"school": school,
					"sequence": idx + 1,
				}
			).insert(ignore_permissions=True)
			created["education_levels"] += 1
		level = frappe.db.get_value("Education Level", {"education_level_name": level_name, "school": school})

		for cidx, cycle_row in enumerate(level_row.get("cycles", [])):
			cycle_name = cycle_row["cycle"]
			if not frappe.db.exists("Cycle", {"cycle_name": cycle_name, "education_level": level}):
				frappe.get_doc(
					{
						"doctype": "Cycle",
						"cycle_name": cycle_name,
						"education_level": level,
						"school": school,
						"sequence": cidx + 1,
					}
				).insert(ignore_permissions=True)
				created["cycles"] += 1
			cycle = frappe.db.get_value("Cycle", {"cycle_name": cycle_name, "education_level": level})

			for gidx, grade_name in enumerate(cycle_row.get("grades", [])):
				if frappe.db.exists("Grade", {"grade_name": grade_name, "cycle": cycle}):
					continue
				frappe.get_doc(
					{"doctype": "Grade", "grade_name": grade_name, "cycle": cycle, "school": school, "sequence": gidx + 1}
				).insert(ignore_permissions=True)
				created["grades"] += 1

	return created


# ---------------------------------------------------------------------------
# Step 4 - Grading scheme
# ---------------------------------------------------------------------------


@frappe.whitelist()
def save_grading_scheme(data):
	require_setup_role()
	data = frappe.parse_json(data)
	scheme_name = data.get("scheme_name") or _("Barème standard")

	# Grading Scheme's own validate() (validate_single_default) forbids a
	# second is_default=1 scheme scoped the same way (school-wide, no
	# education_level) - so "create a brand-new default" is never a valid
	# outcome once one exists. Re-running this step always updates whichever
	# scheme already holds that slot, never competes with it.
	existing_default = frappe.db.get_value(
		"Grading Scheme", {"is_default": 1, "education_level": ["is", "not set"]}, "name"
	)
	target_name = existing_default or scheme_name
	if frappe.db.exists("Grading Scheme", target_name):
		scheme = frappe.get_doc("Grading Scheme", target_name)
	else:
		scheme = frappe.new_doc("Grading Scheme")
		scheme.scheme_name = scheme_name

	scheme.score_max = flt(data.get("score_max")) or 20
	scheme.passing_score = flt(data.get("passing_score")) or 10
	scheme.use_coefficients = 1
	scheme.is_default = 1
	scheme.is_active = 1
	scheme.save(ignore_permissions=True)

	settings = frappe.get_single("Burkina Education Settings")
	settings.max_grade = scheme.score_max
	settings.passing_grade = scheme.passing_score
	settings.save(ignore_permissions=True)

	return scheme.as_dict()


# ---------------------------------------------------------------------------
# Step 5 - Invite key staff
# ---------------------------------------------------------------------------


@frappe.whitelist()
def invite_users(users):
	"""``users``: [{"email", "full_name", "role"}, ...]. Create-or-reuse the
	User (existing users just get the role added, never demoted), send the
	standard Frappe welcome/reset-password email - the same mechanism the
	Desk's own User list "New User" already uses, not a bespoke one."""
	require_setup_role()
	users = frappe.parse_json(users)
	results = []
	for row in users:
		email = (row.get("email") or "").strip()
		role = row.get("role")
		if not email or not role:
			continue
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
		else:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": row.get("full_name") or email.split("@")[0],
					"send_welcome_email": 1,
					"user_type": "System User",
				}
			)
			user.insert(ignore_permissions=True)
		if role not in [r.role for r in user.roles]:
			user.append("roles", {"role": role})
			user.save(ignore_permissions=True)
		results.append({"email": user.name, "role": role})
	return results


@frappe.whitelist()
def finish():
	require_setup_role()
	frappe.get_single("Burkina Education Settings").db_set("setup_wizard_completed", 1)
	return {"status": "ok"}
