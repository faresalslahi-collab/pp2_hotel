# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services import front_desk
from pp2_hotel.services.checkin import check_in
from pp2_hotel.services.reservations import confirm_reservation, create_reservation
from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


class TestFrontDesk(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()

	def test_arrivals_today_excludes_rows_already_checked_in(self):
		# Regression test: an unset Link field (Reservation Room.hotel_stay)
		# can be stored as SQL NULL, not '' -- a plain `== ""` filter silently
		# excludes NULL rows and the arrivals list would show nothing.
		room = make_room(self.property, self.room_type, "T-401", status="Available")
		name = create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": today(), "departure": add_days(today(), 1)}],
		)
		confirm_reservation(name)

		arrivals = front_desk.get_arrivals_today(self.property)
		self.assertEqual(len(arrivals), 1)
		self.assertEqual(arrivals[0]["guest_name"], "_Test Guest")

		reservation = frappe.get_doc("Reservation", name)
		check_in(name, reservation.rooms[0].name)

		self.assertEqual(front_desk.get_arrivals_today(self.property), [])

	def test_arrivals_today_excludes_draft_reservations(self):
		create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "arrival": today(), "departure": add_days(today(), 1)}],
		)  # left as Draft
		self.assertEqual(front_desk.get_arrivals_today(self.property), [])

	def test_in_house_includes_balance_from_folio(self):
		room = make_room(self.property, self.room_type, "T-402", status="Available")
		name = create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": today(), "departure": add_days(today(), 2)}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		check_in(name, reservation.rooms[0].name)

		in_house = front_desk.get_in_house(self.property)
		row = next(r for r in in_house if r["room"] == room)
		self.assertEqual(row["balance"], 0)  # empty folio, no charges yet
		self.assertEqual(row["guest_name"], "_Test Guest")

	def test_departures_today_only_includes_checked_in_stays_departing_today(self):
		room = make_room(self.property, self.room_type, "T-403", status="Available")
		name = create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": add_days(today(), -1), "departure": today()}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		check_in(name, reservation.rooms[0].name)

		departures = front_desk.get_departures_today(self.property)
		self.assertEqual(len(departures), 1)
		self.assertEqual(departures[0]["room_number"], "T-403")

	def test_reservation_calendar_includes_room_and_marks_checked_in_bookings(self):
		# Own Property, not self.property -- get_reservation_calendar's
		# default 14-day window would otherwise pick up the other test
		# methods' own bookings in this same shared-fixture class (several of
		# them use an arrival/departure inside that window), which an exact
		# count/membership check here can't tolerate. Same house rule as
		# every other aggregate-over-a-property test since Phase 4.
		property = make_property("_TEST-PP2-CAL")
		room_type = make_room_type(property)
		guest = make_guest("_Test Guest CAL")
		room_upcoming = make_room(property, room_type, "T-CAL1", status="Available")
		room_in_house = make_room(property, room_type, "T-CAL2", status="Available")

		upcoming_name = create_reservation(
			guest, property, [{"room_type": room_type, "room": room_upcoming, "arrival": add_days(today(), 2), "departure": add_days(today(), 4)}]
		)
		confirm_reservation(upcoming_name)

		in_house_name = create_reservation(
			guest, property, [{"room_type": room_type, "room": room_in_house, "arrival": today(), "departure": add_days(today(), 2)}]
		)
		confirm_reservation(in_house_name)
		reservation = frappe.get_doc("Reservation", in_house_name)
		check_in(in_house_name, reservation.rooms[0].name)

		calendar = front_desk.get_reservation_calendar(property)

		self.assertEqual(len(calendar["rooms"]), 2)
		bookings_by_room = {b["room"]: b for b in calendar["bookings"]}
		self.assertFalse(bookings_by_room[room_upcoming]["checked_in"])
		self.assertTrue(bookings_by_room[room_in_house]["checked_in"])
		self.assertEqual(bookings_by_room[room_upcoming]["guest_name"], "_Test Guest CAL")

	def test_reservation_calendar_excludes_bookings_outside_the_window(self):
		property = make_property("_TEST-PP2-CAL2")
		room_type = make_room_type(property)
		guest = make_guest("_Test Guest CAL2")
		room = make_room(property, room_type, "T-CAL3", status="Available")
		name = create_reservation(
			guest, property, [{"room_type": room_type, "room": room, "arrival": add_days(today(), 30), "departure": add_days(today(), 32)}]
		)
		confirm_reservation(name)

		calendar = front_desk.get_reservation_calendar(property, today(), add_days(today(), 13))
		self.assertFalse(any(b["room"] == room for b in calendar["bookings"]))

	def test_search_guests_requires_at_least_two_characters(self):
		self.assertEqual(front_desk.search_guests(""), [])
		self.assertEqual(front_desk.search_guests("a"), [])

	def test_search_guests_matches_by_name_phone_or_email(self):
		guest = frappe.get_doc(
			{
				"doctype": "Guest",
				"guest_name": "_Test Search Zorro",
				"phone": "+974-5555-0199",
				"email": "zorro.search@example.com",
			}
		).insert(ignore_permissions=True)

		for query in ["Zorro", "5555-0199", "zorro.search"]:
			results = front_desk.search_guests(query)
			self.assertTrue(any(r["name"] == guest.name for r in results), query)

	def test_search_guests_includes_room_for_a_checked_in_guest(self):
		guest = make_guest("_Test Search In-House")
		room = make_room(self.property, self.room_type, "T-SEARCH1", status="Available")
		name = create_reservation(
			guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": today(), "departure": add_days(today(), 1)}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		check_in(name, reservation.rooms[0].name)

		results = front_desk.search_guests("_Test Search In-House")
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]["room_number"], "T-SEARCH1")
		self.assertIsNone(results[0]["reservation"])

	def test_search_guests_includes_an_upcoming_confirmed_reservation(self):
		guest = make_guest("_Test Search Upcoming")
		room = make_room(self.property, self.room_type, "T-SEARCH2", status="Available")
		name = create_reservation(
			guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": add_days(today(), 3), "departure": add_days(today(), 5)}],
		)
		confirm_reservation(name)

		results = front_desk.search_guests("_Test Search Upcoming")
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]["reservation"], name)
		self.assertIsNone(results[0]["room"])
