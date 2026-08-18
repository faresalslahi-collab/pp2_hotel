# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from pp2_hotel.services.housekeeping import (
	create_task,
	get_housekeeping_board,
	inspect,
	mark_clean,
	report_maintenance,
	start_cleaning,
)
from pp2_hotel.tests.factories import make_property, make_room, make_room_type


class TestHousekeeping(FrappeTestCase):
	# FrappeTestCase only rolls back the DB once, at class teardown -- not
	# between individual test methods (see frappe.deprecation_dumpster.
	# FrappeTestCase.setUpClass's addClassCleanup(_rollback_db)). Every test
	# method here therefore gets its own room (room_number keyed off the
	# method name) rather than sharing one from setUp, so an earlier test's
	# task/inspection history can never leak into a later test's assertions.
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)

	def _dirty_room(self, suffix):
		return make_room(self.property, self.room_type, f"T-8{suffix}", status="Dirty")

	def test_create_task_dedupes_against_an_existing_active_task(self):
		room = self._dirty_room("01")
		first = create_task(room)
		second = create_task(room)
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count("Housekeeping Task", {"room": room}), 1)

	def test_full_happy_path_cycles_room_back_to_available(self):
		room = self._dirty_room("02")
		task = create_task(room)

		start_cleaning(task)
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Cleaning")
		self.assertEqual(frappe.db.get_value("Housekeeping Task", task, "status"), "In Progress")

		mark_clean(task)
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Clean")
		self.assertEqual(frappe.db.get_value("Housekeeping Task", task, "status"), "Completed")

		inspect(task, "Passed")
		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Available")
		self.assertEqual(frappe.db.get_value("Housekeeping Task", task, "status"), "Inspected")
		self.assertEqual(frappe.db.count("Room Inspection", {"housekeeping_task": task}), 1)

	def test_failed_inspection_requeues_the_room_and_task(self):
		room = self._dirty_room("03")
		task = create_task(room)
		start_cleaning(task)
		mark_clean(task)

		inspect(task, "Failed", notes="Bathroom not cleaned properly.")

		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Dirty")
		task_doc = frappe.get_doc("Housekeeping Task", task)
		self.assertEqual(task_doc.status, "Pending")
		self.assertIsNone(task_doc.started_at)
		self.assertIsNone(task_doc.completed_at)
		# The room still has exactly one active task -- re-queued, not duplicated.
		self.assertEqual(frappe.db.count("Housekeeping Task", {"room": room}), 1)

	def test_cannot_skip_stages(self):
		room = self._dirty_room("04")
		task = create_task(room)
		self.assertRaises(frappe.ValidationError, mark_clean, task)
		self.assertRaises(frappe.ValidationError, inspect, task, "Passed")

	def test_report_maintenance_takes_room_out_of_rotation(self):
		room = self._dirty_room("05")
		task = create_task(room)
		start_cleaning(task)

		report_maintenance(task, "AC unit not working.")

		self.assertEqual(frappe.db.get_value("Room", room, "status"), "Maintenance")
		task_doc = frappe.get_doc("Housekeeping Task", task)
		self.assertIn("AC unit not working.", task_doc.notes)
		# The task itself keeps its In Progress status/history -- reporting
		# maintenance blocks the room, it doesn't erase the cleaning record.
		self.assertEqual(task_doc.status, "In Progress")

	def test_room_reported_for_maintenance_drops_off_the_board(self):
		# Regression test: the task stays "In Progress" (see above), but the
		# room itself is no longer housekeeping's to act on -- caught via
		# browser testing, where a Maintenance-flagged room kept showing
		# "Mark Clean"/"Report Maintenance" actions on the board.
		room = self._dirty_room("07")
		task = create_task(room)
		start_cleaning(task)
		board_before = get_housekeeping_board(self.property)
		self.assertTrue(any(row["room"] == room for row in board_before))

		report_maintenance(task, "AC unit not working.")

		board_after = get_housekeeping_board(self.property)
		self.assertFalse(any(row["room"] == room for row in board_after))

	def test_housekeeping_board_includes_active_tasks_and_excludes_inspected(self):
		room = self._dirty_room("06")
		task = create_task(room)
		board = get_housekeeping_board(self.property)
		self.assertTrue(any(row["room"] == room for row in board))

		start_cleaning(task)
		mark_clean(task)
		inspect(task, "Passed")

		board_after = get_housekeeping_board(self.property)
		self.assertFalse(any(row["room"] == room for row in board_after))

	def test_report_maintenance_also_creates_a_real_maintenance_request(self):
		# Phase 8: report_maintenance's existing note-on-the-task/room-status
		# behavior (asserted above in test_report_maintenance_takes_room_out_
		# of_rotation) is unchanged -- this only checks the new, additive part.
		room = self._dirty_room("08")
		task = create_task(room)
		start_cleaning(task)

		report_maintenance(task, "Ceiling leak reported by guest.")

		request = frappe.db.get_value(
			"Maintenance Request", {"room": room, "description": "Ceiling leak reported by guest."}, "name"
		)
		self.assertIsNotNone(request)
		self.assertEqual(frappe.db.get_value("Maintenance Request", request, "status"), "Open")
