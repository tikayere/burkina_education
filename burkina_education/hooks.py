app_name = "burkina_education"
app_title = "Burkina Education"
app_publisher = "Burkina Education Project"
app_description = "Burkina Faso School ERP — local layer on top of Frappe Education for schools in Burkina Faso"
app_email = "pourou.2000@gmail.com"
app_license = "gpl-3.0"

# Apps
# ------------------

required_apps = ["erpnext", "education"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "burkina_education",
# 		"logo": "/assets/burkina_education/logo.png",
# 		"title": "Burkina Education",
# 		"route": "/burkina_education",
# 		"has_permission": "burkina_education.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/burkina_education/css/burkina_education.css"
# app_include_js = "/assets/burkina_education/js/burkina_education.js"

# include js, css files in header of web template
# web_include_css = "/assets/burkina_education/css/burkina_education.css"
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

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

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
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

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
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		# master.md §24: detect attendance below the configured threshold every
		# day. Notifying the guardian/administration is Phase 4 (Communication).
		"burkina_education.attendance.alerts.run_attendance_alerts",
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

