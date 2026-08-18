app_name = "pp2_hotel"
app_title = "PP2 Hotel PMS"
app_publisher = "Code Ocean"
app_description = "Hotel Property Management System for Code Ocean"
app_email = "code.ocean.open@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "pp2_hotel",
		"logo": "/assets/pp2_hotel/images/pp2-hotel-logo.svg",
		"title": "PP2 Hotel PMS",
		"route": "/pp2_hotel",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pp2_hotel/css/pp2_hotel.css"
# app_include_js = "/assets/pp2_hotel/js/pp2_hotel.js"

# include js, css files in header of web template
# web_include_css = "/assets/pp2_hotel/css/pp2_hotel.css"
# web_include_js = "/assets/pp2_hotel/js/pp2_hotel.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pp2_hotel/public/scss/website"

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
# app_include_icons = "pp2_hotel/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Website Route Rules
# --------------------
# Vue Router uses history mode, so every sub-route under /pp2_hotel needs to
# resolve server-side to the same SPA shell (www/pp2_hotel.py) -- otherwise a
# direct link/refresh to e.g. /pp2_hotel/reservations 404s instead of letting
# the client-side router handle it. Same pattern qcore/gcc_hr use.
website_route_rules = [
	{"from_route": "/pp2_hotel/<path:app_path>", "to_route": "pp2_hotel"},
	{"from_route": "/pp2_hotel", "to_route": "pp2_hotel"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pp2_hotel.utils.jinja_methods",
# 	"filters": "pp2_hotel.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pp2_hotel.install.before_install"
# after_install = "pp2_hotel.install.after_install"

# Fixtures
# --------
# The section-17 role vocabulary is re-synced on every `bench migrate`.
# Demo/seed data is intentionally NOT a fixture -- see pp2_hotel/demo/seed.py,
# run explicitly via `bench execute`.

fixtures = [
	{
		"doctype": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"Hotel Administrator",
					"Hotel Manager",
					"Front Desk Manager",
					"Receptionist",
					"Cashier",
					"Housekeeping Manager",
					"Housekeeper",
					"Accountant",
					"Maintenance Manager",
					"Maintenance Staff",
					"Auditor",
				],
			]
		],
	}
]

# Uninstallation
# ------------

# before_uninstall = "pp2_hotel.uninstall.before_uninstall"
# after_uninstall = "pp2_hotel.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pp2_hotel.utils.before_app_install"
# after_app_install = "pp2_hotel.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pp2_hotel.utils.before_app_uninstall"
# after_app_uninstall = "pp2_hotel.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "pp2_hotel.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pp2_hotel.notifications.get_notification_config"

# Permissions
# -----------
# Property-scoped access (Phase 12) -- see pp2_hotel/permissions.py's module
# docstring for exactly what this does and does not restrict (Desk + the
# Configuration UI's frappe.client-based reads; NOT the custom Vue app's own
# api.* functions, which read via frappe.get_all() and always have).

permission_query_conditions = {
	"Room": "pp2_hotel.permissions.get_permission_query_conditions_room",
	"Room Type": "pp2_hotel.permissions.get_permission_query_conditions_room_type",
	"Floor": "pp2_hotel.permissions.get_permission_query_conditions_floor",
	"Rate Plan": "pp2_hotel.permissions.get_permission_query_conditions_rate_plan",
	"Hotel Stay": "pp2_hotel.permissions.get_permission_query_conditions_hotel_stay",
	"Hotel Folio": "pp2_hotel.permissions.get_permission_query_conditions_hotel_folio",
	"Reservation": "pp2_hotel.permissions.get_permission_query_conditions_reservation",
}

has_permission = {
	"Room": "pp2_hotel.permissions.has_property_permission",
	"Room Type": "pp2_hotel.permissions.has_property_permission",
	"Floor": "pp2_hotel.permissions.has_property_permission",
	"Rate Plan": "pp2_hotel.permissions.has_property_permission",
	"Hotel Stay": "pp2_hotel.permissions.has_property_permission",
	"Hotel Folio": "pp2_hotel.permissions.has_property_permission",
	"Reservation": "pp2_hotel.permissions.has_property_permission",
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pp2_hotel.tasks.all"
# 	],
# 	"daily": [
# 		"pp2_hotel.tasks.daily"
# 	],
# 	"hourly": [
# 		"pp2_hotel.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pp2_hotel.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pp2_hotel.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "pp2_hotel.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "pp2_hotel.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pp2_hotel.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pp2_hotel.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pp2_hotel.utils.before_request"]
# after_request = ["pp2_hotel.utils.after_request"]

# Job Events
# ----------
# before_job = ["pp2_hotel.utils.before_job"]
# after_job = ["pp2_hotel.utils.after_job"]

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
# 	"pp2_hotel.auth.validate"
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

