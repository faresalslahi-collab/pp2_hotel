# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.checkin import check_in
from pp2_hotel.services.reservations import cancel_reservation, confirm_reservation, create_reservation
from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


class TestCheckIn(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		frappe.db.set_value("Property", self.property, "default_tax_rate", 15)
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()

	def _confirmed_reservation(self, room=None):
		name = create_reservation(
			self.guest,
			self.property,
			[
				{
					"room_type": self.room_type,
					"room": room,
					"arrival": today(),
					"departure": add_days(today(), 2),
					"adults": 1,
					"children": 0,
				}
			],
		)
		confirm_reservation(name)
		return frappe.get_doc("Reservation", name)

	def test_check_in_with_pre_assigned_room_creates_stay_and_folio(self):
		room = make_room(self.property, self.room_type, "T-501", status="Available")
		reservation = self._confirmed_reservation(room=room)

		result = check_in(reservation.name, reservation.rooms[0].name)

		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Occupied")
		stay = frappe.get_doc("Hotel Stay", result["hotel_stay"])
		self.assertEqual(stay.guest, self.guest)
		self.assertEqual(stay.reservation, reservation.name)
		folio = frappe.get_doc("Hotel Folio", result["folio"])
		self.assertEqual(folio.tax_rate, 15)
		self.assertEqual(
			frappe.db.get_value("Reservation Room", reservation.rooms[0].name, "hotel_stay"),
			result["hotel_stay"],
		)

	def test_check_in_assigns_a_room_when_none_was_pre_assigned(self):
		room = make_room(self.property, self.room_type, "T-502", status="Available")
		reservation = self._confirmed_reservation()  # no room pre-assigned

		result = check_in(reservation.name, reservation.rooms[0].name, room=room)

		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Occupied")
		self.assertEqual(
			frappe.db.get_value("Reservation Room", reservation.rooms[0].name, "room"), room
		)

	def test_check_in_rejects_room_of_the_wrong_type(self):
		other_room_type = frappe.get_doc(
			{
				"doctype": "Room Type",
				"room_type_name": "Other Test Room Type",
				"property": self.property,
				"base_rate": 600,
			}
		).insert(ignore_permissions=True).name
		wrong_room = make_room(self.property, other_room_type, "T-503", status="Available")
		reservation = self._confirmed_reservation()  # line wants self.room_type
		self.assertRaises(
			frappe.ValidationError, check_in, reservation.name, reservation.rooms[0].name, wrong_room
		)

	def test_double_check_in_is_rejected(self):
		room = make_room(self.property, self.room_type, "T-504", status="Available")
		reservation = self._confirmed_reservation(room=room)
		check_in(reservation.name, reservation.rooms[0].name)
		self.assertRaises(frappe.ValidationError, check_in, reservation.name, reservation.rooms[0].name)

	def test_check_in_on_a_cancelled_reservation_is_rejected(self):
		room = make_room(self.property, self.room_type, "T-506", status="Available")
		reservation = self._confirmed_reservation(room=room)
		cancel_reservation(reservation.name, "Guest changed plans")
		self.assertRaises(frappe.ValidationError, check_in, reservation.name, reservation.rooms[0].name)

	def test_check_in_from_draft_reservation_confirms_it(self):
		# Covers the walk-in path: create + check in immediately, no separate
		# "confirm" step required first.
		room = make_room(self.property, self.room_type, "T-505", status="Available")
		name = create_reservation(
			self.guest,
			self.property,
			[
				{
					"room_type": self.room_type,
					"room": room,
					"arrival": today(),
					"departure": add_days(today(), 1),
				}
			],
		)
		reservation = frappe.get_doc("Reservation", name)
		self.assertEqual(reservation.status, "Draft")

		check_in(name, reservation.rooms[0].name)

		self.assertEqual(frappe.db.get_value("Reservation", name, "status"), "Confirmed")
