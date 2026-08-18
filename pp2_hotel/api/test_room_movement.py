# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.room_movement import move_room
from pp2_hotel.tests.factories import make_checked_in_stay, make_guest, make_property, make_room, make_room_type


class TestRoomMovement(FrappeTestCase):
	# Each test method builds its own Property/rooms/stay rather than sharing
	# one via setUp() -- move_room() mutates room status and Hotel Stay state,
	# and FrappeTestCase only rolls back once, at class teardown, so a shared
	# fixture would leak one method's move into the next (see
	# api/test_reports.py's TestOccupancyRevenueReport for the full
	# explanation of this house rule).
	def setUp(self):
		frappe.set_user("Administrator")
		self.guest = make_guest()

	def _checked_in_stay(self, property_code, standard_room="T-101", occupied_room="T-102"):
		property = make_property(property_code)
		room_type = make_room_type(property)
		make_room(property, room_type, standard_room, status="Available")
		room = make_room(property, room_type, occupied_room, status="Occupied")
		stay = make_checked_in_stay(
			property, room, self.guest, add_days(today(), -1), add_days(today(), 2), rate=400
		)
		return property, room_type, room, stay

	def test_move_room_updates_both_rooms_and_recalculates_rate(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM1")
		to_room = make_room(property, room_type, "T-103", status="Available")
		# A Rate Plan covering today, on the destination Room Type, so the
		# move's "financial impact" is a real recalculated number, not just
		# base_rate again.
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Move Season",
				"property": property,
				"room_type": room_type,
				"start_date": today(),
				"end_date": add_days(today(), 1),
				"rate": 550,
			}
		).insert(ignore_permissions=True)

		result = move_room(stay.name, to_room, reason="Guest requested a quieter room.")

		self.assertEqual(result["from_room"], from_room)
		self.assertEqual(result["to_room"], to_room)
		self.assertEqual(result["old_rate"], 400)
		self.assertEqual(result["new_rate"], 550)
		self.assertEqual(result["rate_difference"], 150)
		self.assertEqual(frappe.db.get_value("Room", from_room, "status"), "Dirty")
		self.assertEqual(frappe.db.get_value("Room", to_room, "status"), "Occupied")
		self.assertEqual(frappe.db.get_value("Hotel Stay", stay.name, "room"), to_room)
		self.assertEqual(frappe.db.get_value("Hotel Stay", stay.name, "rate"), 550)

	def test_move_room_creates_a_housekeeping_task_for_the_vacated_room(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM2")
		to_room = make_room(property, room_type, "T-103", status="Available")

		move_room(stay.name, to_room)

		task = frappe.db.get_value("Housekeeping Task", {"room": from_room, "status": "Pending"}, "name")
		self.assertIsNotNone(task)

	def test_move_room_rejects_a_non_checked_in_stay(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM3")
		to_room = make_room(property, room_type, "T-103", status="Available")
		frappe.db.set_value("Hotel Stay", stay.name, "status", "Checked Out")

		self.assertRaises(frappe.ValidationError, move_room, stay.name, to_room)

	def test_move_room_rejects_a_non_available_destination(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM4")
		to_room = make_room(property, room_type, "T-103", status="Dirty")

		self.assertRaises(frappe.ValidationError, move_room, stay.name, to_room)

	def test_move_room_rejects_the_same_room(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM5")

		self.assertRaises(frappe.ValidationError, move_room, stay.name, from_room)

	def test_move_room_rejects_a_different_property(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM6")
		other_property = make_property("_TEST-PP2-RM6-OTHER")
		other_room_type = make_room_type(other_property)
		other_room = make_room(other_property, other_room_type, "T-201", status="Available")

		self.assertRaises(frappe.ValidationError, move_room, stay.name, other_room)

	def test_move_room_rejects_exceeding_max_occupancy(self):
		property, room_type, from_room, stay = self._checked_in_stay("_TEST-PP2-RM7")
		frappe.db.set_value("Hotel Stay", stay.name, "adults", 3)
		small_room_type = make_room_type(property, type_name="Small Room", max_occupancy=2)
		to_room = make_room(property, small_room_type, "T-103", status="Available")

		self.assertRaises(frappe.ValidationError, move_room, stay.name, to_room)
