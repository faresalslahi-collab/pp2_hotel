# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.availability import get_availability
from pp2_hotel.services.reservations import confirm_reservation, create_reservation
from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


class TestAvailability(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()
		# Two rooms of this type, so availability starts at 2.
		make_room(self.property, self.room_type, "T-601")
		make_room(self.property, self.room_type, "T-602")

	def test_availability_excludes_out_of_order_and_maintenance_rooms(self):
		make_room(self.property, self.room_type, "T-603", status="Out of Order")
		make_room(self.property, self.room_type, "T-604", status="Maintenance")
		available = get_availability(self.property, self.room_type, today(), add_days(today(), 2))
		self.assertEqual(available, 2)

	def test_confirmed_overlapping_reservation_reduces_availability(self):
		before = get_availability(self.property, self.room_type, today(), add_days(today(), 2))
		name = create_reservation(
			self.guest,
			self.property,
			[
				{
					"room_type": self.room_type,
					"arrival": today(),
					"departure": add_days(today(), 2),
				}
			],
		)
		confirm_reservation(name)
		after = get_availability(self.property, self.room_type, today(), add_days(today(), 2))
		self.assertEqual(after, before - 1)

	def test_draft_reservation_does_not_reduce_availability(self):
		before = get_availability(self.property, self.room_type, today(), add_days(today(), 2))
		create_reservation(
			self.guest,
			self.property,
			[
				{
					"room_type": self.room_type,
					"arrival": today(),
					"departure": add_days(today(), 2),
				}
			],
		)  # left as Draft, never confirmed
		after = get_availability(self.property, self.room_type, today(), add_days(today(), 2))
		self.assertEqual(after, before)

	def test_non_overlapping_dates_do_not_reduce_availability(self):
		name = create_reservation(
			self.guest,
			self.property,
			[
				{
					"room_type": self.room_type,
					"arrival": add_days(today(), 10),
					"departure": add_days(today(), 12),
				}
			],
		)
		confirm_reservation(name)
		# Same-day turnover: a stay ending on day X and a new one starting on
		# day X are not an overlap.
		available = get_availability(
			self.property, self.room_type, add_days(today(), 12), add_days(today(), 14)
		)
		self.assertEqual(available, 2)
