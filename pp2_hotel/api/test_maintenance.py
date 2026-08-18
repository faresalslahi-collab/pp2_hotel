# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from pp2_hotel.services.maintenance import (
	cancel_request,
	create_request,
	get_maintenance_board,
	resolve_request,
	start_work,
)
from pp2_hotel.tests.factories import make_property, make_room, make_room_type


class TestMaintenance(FrappeTestCase):
	# Each test method gets its own room -- resolve_request/cancel_request
	# mutate Room.status and create Housekeeping Tasks, and FrappeTestCase
	# only rolls back once at class teardown, so a shared fixture would leak
	# one method's request/room state into the next (same house rule as
	# every prior phase's service-level tests).
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)

	def _room(self, suffix, status="Available"):
		return make_room(self.property, self.room_type, f"T-9{suffix}", status=status)

	def test_create_request_takes_a_vacant_room_out_of_rotation(self):
		room = self._room("01")
		create_request(room, "AC not working")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Maintenance")

	def test_create_request_leaves_an_occupied_room_occupied(self):
		room = self._room("02", status="Occupied")
		request = create_request(room, "TV remote missing")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Occupied")
		self.assertTrue(frappe.db.exists("Maintenance Request", request))

	def test_create_request_dedupes_against_an_existing_active_request(self):
		room = self._room("03")
		first = create_request(room, "Leaky faucet")
		second = create_request(room, "Leaky faucet again")
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count("Maintenance Request", {"room": room}), 1)

	def test_start_work_transitions_to_in_progress(self):
		room = self._room("04")
		request = create_request(room, "Broken lock")
		start_work(request)
		doc = frappe.get_doc("Maintenance Request", request)
		self.assertEqual(doc.status, "In Progress")
		self.assertIsNotNone(doc.started_at)

	def test_resolve_request_sends_the_room_to_dirty_with_a_cleaning_task(self):
		room = self._room("05")
		request = create_request(room, "Broken AC")
		resolve_request(request, "Replaced the unit")

		doc = frappe.get_doc("Maintenance Request", request)
		self.assertEqual(doc.status, "Resolved")
		self.assertEqual(doc.resolution_notes, "Replaced the unit")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Dirty")
		task = frappe.db.get_value("Housekeeping Task", {"room": room, "status": "Pending"}, "name")
		self.assertIsNotNone(task)

	def test_resolve_request_on_an_occupied_room_does_not_touch_room_status(self):
		room = self._room("06", status="Occupied")
		request = create_request(room, "Minibar not cooling")
		resolve_request(request, "Fixed")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Occupied")

	def test_cancel_request_requires_a_reason(self):
		room = self._room("07")
		request = create_request(room, "False alarm")
		self.assertRaises(frappe.ValidationError, cancel_request, request, "")

	def test_cancel_request_reverts_straight_to_available_with_no_task(self):
		room = self._room("08")
		request = create_request(room, "Thought the AC was broken")
		cancel_request(request, "Guest was just holding the remote wrong")

		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Available")
		self.assertEqual(frappe.db.count("Housekeeping Task", {"room": room}), 0)

	def test_resolve_request_rejects_an_already_resolved_request(self):
		room = self._room("09")
		request = create_request(room, "Broken window latch")
		resolve_request(request, "Fixed")
		self.assertRaises(frappe.ValidationError, resolve_request, request, "Fixed again")

	def test_cancel_request_rejects_an_already_cancelled_request(self):
		room = self._room("10")
		request = create_request(room, "Duplicate report")
		cancel_request(request, "Duplicate of another ticket")
		self.assertRaises(frappe.ValidationError, cancel_request, request, "Trying again")

	def test_get_maintenance_board_only_includes_active_requests(self):
		room_a = self._room("11")
		room_b = self._room("12")
		open_request = create_request(room_a, "Still broken")
		resolved_request = create_request(room_b, "Already fixed")
		resolve_request(resolved_request, "Done")

		board = get_maintenance_board(self.property)
		board_names = {row["name"] for row in board}
		self.assertIn(open_request, board_names)
		self.assertNotIn(resolved_request, board_names)
