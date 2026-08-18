# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.checkin import check_in
from pp2_hotel.services.checkout import check_out
from pp2_hotel.services.folio import add_charge, add_payment
from pp2_hotel.services.housekeeping import create_task, inspect, mark_clean, start_cleaning
from pp2_hotel.services.reports import (
	get_guest_ledger,
	get_housekeeping_report,
	get_occupancy_revenue_report,
	get_outstanding_balances,
	get_payment_report,
)
from pp2_hotel.services.reservations import confirm_reservation, create_reservation
from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


class TestOccupancyRevenueReport(FrappeTestCase):
	# Each test method uses its own Property (not one shared via setUp()) --
	# FrappeTestCase only rolls back the DB once, at class teardown (see
	# ROOM_STATUS_ENGINE.md-adjacent notes in test_housekeeping.py for the
	# full explanation), so a report test that counts *all* rooms/revenue
	# for "the" property would otherwise pick up whatever an earlier method
	# in this same class left behind.
	def setUp(self):
		frappe.set_user("Administrator")
		self.guest = make_guest()

	def test_single_stay_produces_expected_occupancy_and_adr(self):
		property = make_property("_TEST-PP2-OCC1")
		room_type = make_room_type(property)
		self.property, self.room_type = property, room_type
		# Two rooms total, one Out of Order (excluded from "total sellable
		# rooms"), one occupied for exactly the 3-day report window.
		occupied_room = make_room(self.property, self.room_type, "T-r01", status="Available")
		make_room(self.property, self.room_type, "T-r02", status="Out of Order")

		start = add_days(today(), -2)
		end = today()
		name = create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "room": occupied_room, "arrival": start, "departure": add_days(end, 1)}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		result = check_in(name, reservation.rooms[0].name)
		folio = result["folio"]
		for n in range(3):
			add_charge(folio, "Room Charge", 400, posting_date=add_days(start, n))
		add_charge(folio, "Breakfast", 50, hotel_service=None, posting_date=today())
		# hotel_service left unset above on purpose -- test the *actual*
		# add_charge contract (hotel_service is optional), the report's own
		# room-vs-other split is exercised properly below with one that does
		# set it.

		report = get_occupancy_revenue_report(self.property, start, end)

		self.assertEqual(report["total_rooms"], 1)  # Out of Order excluded
		self.assertEqual(len(report["daily"]), 3)
		for day in report["daily"]:
			self.assertEqual(day["occupied_rooms"], 1)
			self.assertEqual(day["occupancy_pct"], 100.0)
		self.assertEqual(report["occupancy_pct"], 100.0)
		# 3 nights x 400 room charge + 1 x 50 (unset hotel_service, so still
		# counted as room revenue by this report's own signal) = 1250.
		self.assertEqual(report["room_revenue"], 1250.0)
		self.assertEqual(report["adr"], round(1250.0 / 3, 2))
		self.assertEqual(report["revpar"], round(1250.0 / 3, 2))  # 1 room x 3 nights available

	def test_service_charge_counted_as_other_revenue(self):
		property = make_property("_TEST-PP2-OCC2")
		room_type = make_room_type(property)
		self.property, self.room_type = property, room_type
		room = make_room(self.property, self.room_type, "T-r03", status="Available")
		service = frappe.get_doc(
			{"doctype": "Hotel Service", "service_name": "_Test Spa", "rate": 200}
		).insert(ignore_permissions=True)
		name = create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": today(), "departure": add_days(today(), 1)}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		result = check_in(name, reservation.rooms[0].name)
		add_charge(result["folio"], "Spa", 200, hotel_service=service.name, posting_date=today())

		report = get_occupancy_revenue_report(self.property, today(), today())
		self.assertEqual(report["other_revenue"], 200.0)
		self.assertEqual(report["room_revenue"], 0.0)


class TestGuestLedgerAndOutstandingBalances(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()

	def _checked_in_folio(self, room_suffix):
		room = make_room(self.property, self.room_type, f"T-r{room_suffix}", status="Available")
		name = create_reservation(
			self.guest,
			self.property,
			[{"room_type": self.room_type, "room": room, "arrival": today(), "departure": add_days(today(), 2)}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		result = check_in(name, reservation.rooms[0].name)
		return result["folio"], room

	def test_guest_ledger_includes_enriched_fields(self):
		folio, room = self._checked_in_folio("11")
		add_charge(folio, "Room Charge", 400)

		ledger = get_guest_ledger(self.property)
		row = next(r for r in ledger if r["name"] == folio)
		self.assertEqual(row["guest_name"], "_Test Guest")
		self.assertEqual(row["room_number"], "T-r11")
		self.assertEqual(row["balance"], 400.0)

	def test_outstanding_balances_includes_closed_folio_with_override(self):
		folio, _ = self._checked_in_folio("12")
		add_charge(folio, "Room Charge", 400)
		stay = frappe.db.get_value("Hotel Folio", folio, "stay")
		check_out(stay, override_reason="Corporate account, will settle later.")

		outstanding = get_outstanding_balances(self.property)
		row = next((r for r in outstanding if r["name"] == folio), None)
		self.assertIsNotNone(row)
		self.assertEqual(row["status"], "Closed")
		self.assertEqual(row["balance"], 400.0)
		self.assertEqual(row["checkout_override_reason"], "Corporate account, will settle later.")

	def test_outstanding_balances_excludes_settled_folio(self):
		folio, _ = self._checked_in_folio("13")
		add_charge(folio, "Room Charge", 400)
		add_payment(folio, 400, "Cash")

		outstanding = get_outstanding_balances(self.property)
		self.assertFalse(any(r["name"] == folio for r in outstanding))


class TestPaymentReport(FrappeTestCase):
	# get_payment_report sums *all* payments for the property+range, not one
	# folio -- each method needs its own property so the two don't sum each
	# other's payments (see TestOccupancyRevenueReport's comment above for
	# why methods in one class can't share a fixture for an aggregate test).
	def setUp(self):
		frappe.set_user("Administrator")
		self.guest = make_guest()

	def _folio_for(self, property_code):
		property = make_property(property_code)
		room_type = make_room_type(property)
		room = make_room(property, room_type, "T-r21", status="Available")
		name = create_reservation(
			self.guest,
			property,
			[{"room_type": room_type, "room": room, "arrival": today(), "departure": add_days(today(), 1)}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		folio = check_in(name, reservation.rooms[0].name)["folio"]
		return property, folio

	def test_totals_by_method(self):
		self.property, self.folio = self._folio_for("_TEST-PP2-PAY1")
		add_payment(self.folio, 100, "Cash", posting_date=today())
		add_payment(self.folio, 250, "Card", posting_date=today())
		add_payment(self.folio, 50, "Cash", posting_date=today())

		report = get_payment_report(self.property, today(), today())

		self.assertEqual(report["total"], 400.0)
		by_method = {row["payment_method"]: row["total"] for row in report["by_method"]}
		self.assertEqual(by_method["Cash"], 150.0)
		self.assertEqual(by_method["Card"], 250.0)
		self.assertEqual(len(report["payments"]), 3)

	def test_payments_outside_range_are_excluded(self):
		self.property, self.folio = self._folio_for("_TEST-PP2-PAY2")
		add_payment(self.folio, 100, "Cash", posting_date=add_days(today(), -10))
		report = get_payment_report(self.property, today(), today())
		self.assertEqual(report["total"], 0.0)


class TestHousekeepingReport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)

	def test_pass_rate_and_task_counts(self):
		room_a = make_room(self.property, self.room_type, "T-r31", status="Dirty")
		room_b = make_room(self.property, self.room_type, "T-r32", status="Dirty")

		task_a = create_task(room_a)
		start_cleaning(task_a)
		mark_clean(task_a)
		inspect(task_a, "Passed")

		task_b = create_task(room_b)
		start_cleaning(task_b)
		mark_clean(task_b)
		inspect(task_b, "Failed", notes="redo")

		report = get_housekeeping_report(self.property)

		self.assertEqual(report["total_tasks"], 2)
		self.assertEqual(report["completed_tasks"], 1)  # only task_a reached Inspected
		self.assertEqual(report["pending_tasks"], 1)  # task_b re-queued to Pending
		self.assertEqual(report["inspections_passed"], 1)
		self.assertEqual(report["inspections_failed"], 1)
		self.assertEqual(report["pass_rate"], 50.0)
		self.assertIsNotNone(report["avg_turnaround_minutes"])
