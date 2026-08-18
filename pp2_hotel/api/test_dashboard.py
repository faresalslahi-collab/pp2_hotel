# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today

from pp2_hotel.api.dashboard import get_front_desk_kpis, get_room_grid
from pp2_hotel.tests.factories import (
	make_checked_in_stay,
	make_guest,
	make_property,
	make_room,
	make_room_type,
)


class TestFrontDeskDashboard(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)

	def test_get_front_desk_kpis_runs_without_error_and_scopes_by_property(self):
		# Regression test: frappe.get_all(fields=["status", "count(name) as count"])
		# raises ValidationError on this Frappe version -- SQL functions in a
		# field string must use the {"COUNT": "name", "as": "count"} dict form.
		make_room(self.property, self.room_type, "T-901", status="Available")
		make_room(self.property, self.room_type, "T-902", status="Dirty")

		result = get_front_desk_kpis(property=self.property)
		self.assertGreaterEqual(result["available_rooms"], 1)
		self.assertGreaterEqual(result["dirty_rooms"], 1)
		self.assertEqual(result["currency"], "SAR")

		other_property = make_property(code="_TEST-PP2-OTHER")
		other_result = get_front_desk_kpis(property=other_property)
		self.assertEqual(other_result["available_rooms"], 0)

	def test_get_room_grid_includes_current_guest_for_occupied_room(self):
		room = make_room(self.property, self.room_type, "T-903", status="Occupied")
		guest = make_guest()
		make_checked_in_stay(
			self.property, room, guest, today(), frappe.utils.add_days(today(), 2), rate=400
		)

		grid = get_room_grid(property=self.property)
		row = next(r for r in grid if r["name"] == room)
		self.assertEqual(row["status"], "Occupied")
		self.assertEqual(row["guest_name"], "_Test Guest")
		self.assertIsNotNone(row["stay"])

	def test_get_room_grid_has_no_guest_for_available_room(self):
		room = make_room(self.property, self.room_type, "T-904", status="Available")
		grid = get_room_grid(property=self.property)
		row = next(r for r in grid if r["name"] == room)
		self.assertIsNone(row["guest_name"])
		self.assertIsNone(row["stay"])
