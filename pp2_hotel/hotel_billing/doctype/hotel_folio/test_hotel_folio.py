# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.tests.factories import (
	make_checked_in_stay,
	make_guest,
	make_property,
	make_room,
	make_room_type,
)

# Hotel Folio.sales_invoice (Phase 7) links to ERPNext's Sales Invoice,
# whose own test module chains into erpnext.tests.utils.ERPNextTestSuite the
# same way Customer/Company already did for test_guest.py/test_property.py --
# skip it here too, see those files' comments for the full explanation.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Sales Invoice"]


class TestHotelFolio(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()
		self.room = make_room(self.property, self.room_type, "T-701", status="Occupied")
		self.stay = make_checked_in_stay(
			self.property, self.room, self.guest, add_days(today(), -1), add_days(today(), 1)
		)

	def test_totals_are_computed_from_items_and_payments_not_trusted_from_input(self):
		folio = frappe.get_doc(
			{
				"doctype": "Hotel Folio",
				"stay": self.stay.name,
				"currency": "SAR",
				"tax_rate": 15,
				# Deliberately wrong subtotal/total/paid_amount to prove validate()
				# recomputes all three from items/payments rather than trusting
				# whatever was passed in.
				"subtotal": 999,
				"total": 999,
				"paid_amount": 999,
				"items": [
					{"posting_date": today(), "description": "Room Charge", "rate": 400, "qty": 1, "amount": 400},
					{"posting_date": today(), "description": "Breakfast", "rate": 50, "qty": 2, "amount": 100},
				],
				"payments": [
					{"posting_date": today(), "amount": 100, "payment_method": "Cash"},
				],
			}
		).insert(ignore_permissions=True)

		self.assertEqual(folio.subtotal, 500)
		self.assertEqual(folio.tax_amount, 75)
		self.assertEqual(folio.total, 575)
		self.assertEqual(folio.paid_amount, 100)
		self.assertEqual(folio.balance, 475)

	def test_balance_updates_when_payment_is_recorded(self):
		folio = frappe.get_doc(
			{
				"doctype": "Hotel Folio",
				"stay": self.stay.name,
				"currency": "SAR",
				"tax_rate": 0,
				"items": [
					{"posting_date": today(), "description": "Room Charge", "rate": 400, "qty": 1, "amount": 400}
				],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(folio.balance, 400)

		folio.append("payments", {"posting_date": today(), "amount": 400, "payment_method": "Card"})
		folio.save()
		self.assertEqual(folio.paid_amount, 400)
		self.assertEqual(folio.balance, 0)

	def test_guest_and_property_are_fetched_from_stay(self):
		folio = frappe.get_doc(
			{
				"doctype": "Hotel Folio",
				"stay": self.stay.name,
				"currency": "SAR",
				"items": [],
			}
		).insert(ignore_permissions=True)
		self.assertEqual(folio.guest, self.guest)
		self.assertEqual(folio.property, self.property)
