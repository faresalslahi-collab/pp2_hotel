import frappe
import frappe.sessions

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/pp2_hotel"
		raise frappe.Redirect

	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosemgrep

	context.csrf_token = csrf_token
	context.boot = {
		"csrf_token": csrf_token,
		"user": frappe.session.user,
		"full_name": frappe.utils.get_fullname(frappe.session.user),
		"user_image": frappe.db.get_value("User", frappe.session.user, "user_image"),
		"roles": frappe.get_roles(frappe.session.user),
		"site_name": frappe.local.site,
	}

	return context
