# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


def _insert_via_checkin_service(doc_dict):
	# Test helper standing in for pp2_hotel.services.checkin.check_in, which
	# is what actually sets this flag in real usage (see test_checkin.py for
	# the end-to-end Reservation -> check_in path).
	frappe.flags.via_checkin_service = True
	try:
		return frappe.get_doc(doc_dict).insert(ignore_permissions=True)
	finally:
		frappe.flags.via_checkin_service = False


class TestHotelStay(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()

	def test_direct_creation_is_blocked_outside_checkin_service(self):
		room = make_room(self.property, self.room_type, "T-800")
		stay = frappe.get_doc(
			{
				"doctype": "Hotel Stay",
				"guest": self.guest,
				"room": room,
				"property": self.property,
				"arrival": today(),
				"departure": add_days(today(), 2),
				"status": "Checked In",
			}
		)
		self.assertRaises(frappe.ValidationError, stay.insert, ignore_permissions=True)

	def test_departure_before_arrival_is_rejected(self):
		room = make_room(self.property, self.room_type, "T-801")
		stay_dict = {
			"doctype": "Hotel Stay",
			"guest": self.guest,
			"room": room,
			"property": self.property,
			"arrival": today(),
			"departure": add_days(today(), -1),
			"status": "Checked In",
		}
		frappe.flags.via_checkin_service = True
		try:
			self.assertRaises(
				frappe.ValidationError, frappe.get_doc(stay_dict).insert, ignore_permissions=True
			)
		finally:
			frappe.flags.via_checkin_service = False

	def test_checked_in_status_marks_room_occupied(self):
		room = make_room(self.property, self.room_type, "T-802", status="Available")
		_insert_via_checkin_service(
			{
				"doctype": "Hotel Stay",
				"guest": self.guest,
				"room": room,
				"property": self.property,
				"arrival": today(),
				"departure": add_days(today(), 2),
				"status": "Checked In",
			}
		)
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Occupied")

	def test_checked_out_status_leaves_room_dirty_not_available(self):
		# Checkout must not silently free the room for resale -- housekeeping
		# has to turn it first. See ROOM_STATUS_ENGINE.md.
		room = make_room(self.property, self.room_type, "T-803", status="Available")
		stay = _insert_via_checkin_service(
			{
				"doctype": "Hotel Stay",
				"guest": self.guest,
				"room": room,
				"property": self.property,
				"arrival": add_days(today(), -2),
				"departure": today(),
				"status": "Checked In",
			}
		)

		stay.status = "Checked Out"
		stay.save()

		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Dirty")
