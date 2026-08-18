# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

"""Small, deterministic test data builders -- not the random demo dataset in
pp2_hotel/demo/seed.py, which exists for local UI review, not test isolation.
"""

import frappe


def make_company(code="_TEST-PP2-CO"):
	if frappe.db.exists("Company", code):
		return code
	# abbr must be short and unique across the whole site -- derive it from
	# the code's own alnum characters rather than a fixed literal, so two
	# tests calling this with different codes don't collide.
	abbr = "".join(ch for ch in code if ch.isalnum())[-4:].upper()
	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": code,
			"abbr": abbr,
			"default_currency": "SAR",
			"country": "Saudi Arabia",
		}
	).insert(ignore_permissions=True)
	return doc.name


def make_property(code="_TEST-PP2", company=None):
	if frappe.db.exists("Property", code):
		return code
	frappe.get_doc(
		{
			"doctype": "Property",
			# property_name is unique -- derive it from `code` (not a fixed
			# literal) so a test creating two properties with different codes
			# in the same test doesn't collide on this field.
			"property_name": f"Test Property {code}",
			"property_code": code,
			"company": company,
			"default_currency": "SAR",
		}
	).insert(ignore_permissions=True)
	return code


def make_room_type(property_name, type_name="Test Room Type", base_rate=400, max_occupancy=None):
	name = f"{property_name}-{type_name}"
	if frappe.db.exists("Room Type", name):
		return name
	frappe.get_doc(
		{
			"doctype": "Room Type",
			"room_type_name": type_name,
			"property": property_name,
			"base_rate": base_rate,
			"max_occupancy": max_occupancy,
		}
	).insert(ignore_permissions=True)
	return name


def make_room(property_name, room_type, room_number, status="Available"):
	name = f"{property_name}-{room_number}"
	if frappe.db.exists("Room", name):
		frappe.db.set_value("Room", name, "status", status)
		return name
	frappe.get_doc(
		{
			"doctype": "Room",
			"room_number": room_number,
			"property": property_name,
			"room_type": room_type,
			"status": status,
		}
	).insert(ignore_permissions=True)
	return name


def make_guest(guest_name="_Test Guest"):
	existing = frappe.db.get_value("Guest", {"guest_name": guest_name})
	if existing:
		return existing
	return frappe.get_doc({"doctype": "Guest", "guest_name": guest_name}).insert(
		ignore_permissions=True
	).name


def make_checked_in_stay(property_name, room, guest, arrival, departure, rate=None):
	"""A direct Hotel Stay insert, for tests that need one to exist without
	exercising the full Reservation -> check-in flow. Hotel Stay refuses
	direct creation outside `services.checkin.check_in` (see
	hotel_stay.py's validate()), so this flips the same flag that service
	sets -- see test_checkin.py for a test that goes through check_in()
	itself end to end.
	"""
	frappe.flags.via_checkin_service = True
	try:
		return frappe.get_doc(
			{
				"doctype": "Hotel Stay",
				"guest": guest,
				"room": room,
				"property": property_name,
				"arrival": arrival,
				"departure": departure,
				"rate": rate or 0,
				"status": "Checked In",
			}
		).insert(ignore_permissions=True)
	finally:
		frappe.flags.via_checkin_service = False
