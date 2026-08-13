app_name = "burkina_education"
app_title = "Burkina Education"
app_publisher = "Burkina Education Project"
app_description = "Burkina Faso School ERP — local layer on top of Frappe Education for schools in Burkina Faso"
app_email = "pourou.2000@gmail.com"
app_license = "gpl-3.0"

# Desk app icon (Frappe /apps screen, app switcher) - see public/images/logo.svg
# (Burkina Faso flag colours behind a graduation-cap/book glyph).
app_icon = "octicon octicon-mortar-board"
app_color = "#EF2B2D"
app_logo_url = "/assets/burkina_education/images/logo.svg"
# No single module workspace represents the whole app - land on the
# Desk's own workspace switcher rather than guessing at one.
app_home = "/app"

# Apps
# ------------------

required_apps = ["erpnext", "education"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": app_logo_url,
		"title": app_title,
		"route": app_home,
		"has_permission": "burkina_education.api.permission.has_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/burkina_education/css/burkina_education.css"
# app_include_js = "/assets/burkina_education/js/burkina_education.js"

# include js, css files in header of web template
web_include_css = "/assets/burkina_education/css/portal.css"
# web_include_js = "/assets/burkina_education/js/burkina_education.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "burkina_education/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "burkina_education/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role) - Student/Guardian/Teacher Portals
# (master.md §29/§30/§31) all now live in one Vue SPA (frontend/, see
# docs/architecture.md section L) mounted at "/portal"; the SPA's own router
# picks the right dashboard from frappe.boot.user.roles once loaded. This
# superseded the Jinja www/parent, www/student pages Phase 4 originally
# built (kept on disk, unlinked, in case they're ever wanted again).
role_home_page = {
	"Guardian": "portal",
	"Student": "portal",
	"Instructor": "portal",
}

# Vue 3 + frappe-ui SPA (frontend/) - one build serving all three portals.
website_route_rules = [
	{"from_route": "/portal/<path:app_path>", "to_route": "portal"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "burkina_education.utils.jinja_methods",
# 	"filters": "burkina_education.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "burkina_education.setup.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "burkina_education.uninstall.before_uninstall"
# after_uninstall = "burkina_education.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "burkina_education.utils.before_app_install"
# after_app_install = "burkina_education.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "burkina_education.utils.before_app_uninstall"
# after_app_uninstall = "burkina_education.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "burkina_education.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }

has_permission = {
	# Guardian/Student Portals (master.md §29/§30/§54/§77) - narrows the
	# Custom DocPerm read grant (install.py::create_portal_permissions) down
	# to "only this guardian's own children / this student's own record".
	# See messaging/permissions.py.
	doctype: "burkina_education.messaging.permissions.student_scoped_has_permission"
	for doctype in ("Student Term Report", "Student Annual Report", "Student Attendance", "Sales Invoice")
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# Fixes a genuine Education/Frappe-version incompatibility that breaks
	# every Fee Schedule save - see finance/overrides.py and
	# docs/architecture.md section H.
	"Fee Schedule": "burkina_education.finance.overrides.FeeSchedule",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Assessment Result": {
		# Marks are locked on submit; cancelling (the only way to change them
		# afterwards, via amend) must be restricted to authorized roles even
		# though Education's own "Academics User" role grants blanket cancel
		# rights (docs/architecture.md section G explains why this is a hook,
		# not a Custom DocPerm rewrite).
		"before_cancel": "burkina_education.academic.grading.guard_assessment_result_cancel",
	},
	"Sales Invoice": {
		# Only acts on school-fee invoices (Education's student/fee_schedule
		# custom fields) - applies a student's Scholarship/sibling discount by
		# setting Sales Invoice's own additional_discount_percentage, then
		# reuses the accounts controller to recompute totals (docs/architecture.md
		# section H).
		"validate": "burkina_education.finance.discounts.apply_scholarship_and_sibling_discount",
	},
	"Payment Entry": {
		# Covers both a normal cash/bank payment and a mobile money
		# confirmation (finance/mobile_money/api.py submits a real Payment
		# Entry too) - master.md §32 "Payment confirmation" (docs/architecture.md
		# section J).
		"on_submit": "burkina_education.finance.notifications.notify_payment_confirmation",
	},
	"Student Term Report": {
		# master.md §32 "Result available" (docs/architecture.md section J).
		"on_submit": "burkina_education.academic.notifications.notify_term_report_available",
	},
	"Student Annual Report": {
		"on_submit": "burkina_education.academic.notifications.notify_annual_report_available",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		# master.md §24: detect attendance below the configured threshold every
		# day. Notifying the guardian/administration is a separate, explicit
		# step (Attendance Alert.notify_guardians(), Phase 4/Communication) -
		# see attendance/alerts.py.
		"burkina_education.attendance.alerts.run_attendance_alerts",
		# master.md §32 "Fee reminder": one reminder per overdue school-fee
		# invoice at most every N days (docs/architecture.md section J).
		"burkina_education.finance.notifications.run_fee_reminders",
		# master.md §39 "notifications": flips overdue Library Transactions to
		# "En retard" and notifies guardians once per loan (docs/architecture.md
		# section K).
		"burkina_education.library.notifications.run_overdue_notices",
	],
}

# Testing
# -------

# before_tests = "burkina_education.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "burkina_education.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "burkina_education.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["burkina_education.utils.before_request"]
# after_request = ["burkina_education.utils.after_request"]

# Job Events
# ----------
# before_job = ["burkina_education.utils.before_job"]
# after_job = ["burkina_education.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"burkina_education.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

