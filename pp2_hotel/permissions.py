"""Property-scoped access -- registered in hooks.py for the doctypes that
carry a direct `property` field (Room, Room Type, Floor, Rate Plan, Hotel
Stay, Hotel Folio, Reservation). System Manager/Hotel Administrator see
everything, matching every other role-based check in this app; any other
role only sees documents for a Property they're assigned to via a
Property User record. A user with *no* Property User records at all sees
nothing property-scoped -- fail closed, not open.

Scope, stated plainly: this restricts direct Frappe Desk access and the
Configuration UI's own `createListResource`-backed reads (Phase 11),
because both go through `frappe.get_list`, which is what these hooks
actually gate. It does **not** reach the custom Vue app's own dashboards/
boards/reports -- every one of those is a whitelisted `api.*` function
that reads via `frappe.get_all()`, which is documented to skip permission
checks entirely, by design, app-wide, since Phase 1. Making the Vue app
itself property-scoped would mean adding an explicit property-membership
check inside each of those ~15 service functions individually -- a much
larger undertaking than a hooks.py registration, and out of scope for
this phase. See PERMISSIONS.md section 3.
"""

import frappe

EXEMPT_ROLES = {"System Manager", "Hotel Administrator"}


def _user_properties(user):
	return frappe.get_all("Property User", filters={"user": user}, pluck="property")


def has_property_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if EXEMPT_ROLES & set(frappe.get_roles(user)):
		return True
	if not getattr(doc, "property", None):
		return True
	return doc.property in _user_properties(user)


def _property_scoped_conditions(table, user=None):
	user = user or frappe.session.user
	if EXEMPT_ROLES & set(frappe.get_roles(user)):
		return ""
	properties = _user_properties(user)
	if not properties:
		return "1=0"
	quoted = ", ".join(frappe.db.escape(p) for p in properties)
	return f"`{table}`.`property` in ({quoted})"


def get_permission_query_conditions_room(user=None):
	return _property_scoped_conditions("tabRoom", user)


def get_permission_query_conditions_room_type(user=None):
	return _property_scoped_conditions("tabRoom Type", user)


def get_permission_query_conditions_floor(user=None):
	return _property_scoped_conditions("tabFloor", user)


def get_permission_query_conditions_rate_plan(user=None):
	return _property_scoped_conditions("tabRate Plan", user)


def get_permission_query_conditions_hotel_stay(user=None):
	return _property_scoped_conditions("tabHotel Stay", user)


def get_permission_query_conditions_hotel_folio(user=None):
	return _property_scoped_conditions("tabHotel Folio", user)


def get_permission_query_conditions_reservation(user=None):
	return _property_scoped_conditions("tabReservation", user)
