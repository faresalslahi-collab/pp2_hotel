# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from pp2_hotel.services.reservations import cancel_reservation, confirm_reservation, create_reservation
from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


class TestReservations(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()

	def _room_line(self, room=None):
		return {
			"room_type": self.room_type,
			"room": room,
			"arrival": today(),
			"departure": add_days(today(), 2),
			"adults": 2,
			"children": 0,
		}

	def test_create_reservation_defaults_rate_from_room_type(self):
		name = create_reservation(self.guest, self.property, [self._room_line()])
		doc = frappe.get_doc("Reservation", name)
		self.assertEqual(doc.status, "Draft")
		self.assertEqual(doc.arrival, getdate(today()))
		self.assertEqual(doc.rooms[0].rate, 400)  # make_room_type's base_rate

	def test_create_reservation_picks_up_a_rate_plan_covering_the_arrival_date(self):
		# Own Property/Room Type, not self.property/self.room_type from
		# setUp() -- creating a Rate Plan here must not leak into any other
		# test method's expectation of a plain base_rate default (see
		# api/test_reports.py's TestOccupancyRevenueReport for why a shared
		# fixture is unsafe once a test *changes* something instead of just
		# reading it: FrappeTestCase only rolls back once, at class teardown).
		property = make_property("_TEST-PP2-RESRP")
		room_type = make_room_type(property)
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Reservation Season",
				"property": property,
				"room_type": room_type,
				"start_date": today(),
				"end_date": add_days(today(), 5),
				"rate": 777,
			}
		).insert(ignore_permissions=True)
		name = create_reservation(
			self.guest,
			property,
			[
				{
					"room_type": room_type,
					"room": None,
					"arrival": today(),
					"departure": add_days(today(), 2),
					"adults": 2,
					"children": 0,
				}
			],
		)
		doc = frappe.get_doc("Reservation", name)
		self.assertEqual(doc.rooms[0].rate, 777)

	def test_confirm_reservation_reserves_a_pre_assigned_room(self):
		room = make_room(self.property, self.room_type, "T-601", status="Available")
		name = create_reservation(self.guest, self.property, [self._room_line(room=room)])
		confirm_reservation(name)
		self.assertEqual(frappe.db.get_value("Reservation", name, "status"), "Confirmed")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Reserved")

	def test_confirm_reservation_with_no_room_assigned_does_not_touch_any_room(self):
		name = create_reservation(self.guest, self.property, [self._room_line()])
		confirm_reservation(name)
		self.assertEqual(frappe.db.get_value("Reservation", name, "status"), "Confirmed")
		# Nothing to assert on a specific room -- the point is this doesn't throw
		# and doesn't require a room to exist.

	def test_cancel_reservation_requires_a_reason(self):
		room = make_room(self.property, self.room_type, "T-602", status="Available")
		name = create_reservation(self.guest, self.property, [self._room_line(room=room)])
		confirm_reservation(name)
		self.assertRaises(frappe.ValidationError, cancel_reservation, name, "")

	def test_cancel_reservation_releases_reserved_room_back_to_available(self):
		room = make_room(self.property, self.room_type, "T-603", status="Available")
		name = create_reservation(self.guest, self.property, [self._room_line(room=room)])
		confirm_reservation(name)
		cancel_reservation(name, "Guest changed plans")
		self.assertEqual(frappe.db.get_value("Reservation", name, "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Available")

	def test_cancel_reservation_twice_is_rejected(self):
		name = create_reservation(self.guest, self.property, [self._room_line()])
		confirm_reservation(name)
		cancel_reservation(name, "First cancellation")
		self.assertRaises(frappe.ValidationError, cancel_reservation, name, "Second attempt")
