# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.rate_plan import get_effective_rate
from pp2_hotel.tests.factories import make_property, make_room_type


class TestRatePlan(FrappeTestCase):
	# Each test method uses its own Property -- Rate Plan's own overlap
	# validation is scoped to a Room Type, and a Room Type is scoped to a
	# Property, so a shared fixture here risks one method's plan accidentally
	# overlapping another's (see TestOccupancyRevenueReport in
	# api/test_reports.py for the full FrappeTestCase-class-only-rollback
	# explanation this house rule comes from).
	def setUp(self):
		frappe.set_user("Administrator")

	def test_end_date_before_start_date_is_rejected(self):
		property = make_property("_TEST-PP2-RP1")
		room_type = make_room_type(property)
		self.assertRaises(
			frappe.ValidationError,
			frappe.get_doc(
				{
					"doctype": "Rate Plan",
					"plan_name": "_Test Backwards Plan",
					"property": property,
					"room_type": room_type,
					"start_date": today(),
					"end_date": add_days(today(), -1),
					"rate": 500,
				}
			).insert,
			ignore_permissions=True,
		)

	def test_overlapping_active_plan_is_rejected(self):
		property = make_property("_TEST-PP2-RP2")
		room_type = make_room_type(property)
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Summer",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), 10),
				"end_date": add_days(today(), 20),
				"rate": 600,
			}
		).insert(ignore_permissions=True)

		self.assertRaises(
			frappe.ValidationError,
			frappe.get_doc(
				{
					"doctype": "Rate Plan",
					"plan_name": "_Test Overlapping Summer",
					"property": property,
					"room_type": room_type,
					"start_date": add_days(today(), 15),
					"end_date": add_days(today(), 25),
					"rate": 650,
				}
			).insert,
			ignore_permissions=True,
		)

	def test_adjacent_non_overlapping_plans_are_accepted(self):
		property = make_property("_TEST-PP2-RP3")
		room_type = make_room_type(property)
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Early Window",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), 1),
				"end_date": add_days(today(), 10),
				"rate": 600,
			}
		).insert(ignore_permissions=True)
		# Starts the day after the first plan ends -- must not be rejected.
		doc = frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Later Window",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), 11),
				"end_date": add_days(today(), 20),
				"rate": 650,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)

	def test_inactive_plan_does_not_block_overlap(self):
		property = make_property("_TEST-PP2-RP4")
		room_type = make_room_type(property)
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Retired Plan",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), 1),
				"end_date": add_days(today(), 10),
				"rate": 600,
				"is_active": 0,
			}
		).insert(ignore_permissions=True)
		doc = frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Replacement Plan",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), 1),
				"end_date": add_days(today(), 10),
				"rate": 700,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)

	def test_get_effective_rate_matches_covering_plan(self):
		property = make_property("_TEST-PP2-RP5")
		room_type = make_room_type(property, base_rate=400)
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Peak Season",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), -2),
				"end_date": add_days(today(), 2),
				"rate": 999,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(get_effective_rate(room_type, today()), 999.0)

	def test_get_effective_rate_falls_back_to_base_rate_outside_window(self):
		property = make_property("_TEST-PP2-RP6")
		room_type = make_room_type(property, base_rate=425)
		frappe.get_doc(
			{
				"doctype": "Rate Plan",
				"plan_name": "_Test Far Future Plan",
				"property": property,
				"room_type": room_type,
				"start_date": add_days(today(), 100),
				"end_date": add_days(today(), 110),
				"rate": 999,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(get_effective_rate(room_type, today()), 425.0)

	def test_get_effective_rate_falls_back_to_base_rate_with_no_plan_at_all(self):
		property = make_property("_TEST-PP2-RP7")
		room_type = make_room_type(property, base_rate=350)
		self.assertEqual(get_effective_rate(room_type, today()), 350.0)
