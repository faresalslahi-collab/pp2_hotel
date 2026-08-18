# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.api.rooms import get_room_detail
from pp2_hotel.tests.factories import make_checked_in_stay, make_property, make_room, make_room_type


class TestRoomDetail(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)

	def test_available_room_has_no_stay_or_folio(self):
		room = make_room(self.property, self.room_type, "T-950", status="Available")
		detail = get_room_detail(room)
		self.assertEqual(detail["room"]["status"], "Available")
		self.assertIsNone(detail["stay"])
		self.assertIsNone(detail["folio"])

	def test_occupied_room_returns_stay_and_folio_balance(self):
		room = make_room(self.property, self.room_type, "T-951", status="Occupied")
		guest = frappe.get_doc({"doctype": "Guest", "guest_name": "_Test Detail Guest"}).insert(
			ignore_permissions=True
		)
		stay = make_checked_in_stay(
			self.property, room, guest.name, add_days(today(), -1), add_days(today(), 2), rate=500
		)
		folio = frappe.get_doc(
			{
				"doctype": "Hotel Folio",
				"stay": stay.name,
				"currency": "SAR",
				"tax_rate": 15,
				"items": [
					{"posting_date": today(), "description": "Room Charge", "rate": 500, "qty": 1, "amount": 500}
				],
				"payments": [{"posting_date": today(), "amount": 200, "payment_method": "Cash"}],
			}
		).insert(ignore_permissions=True)

		detail = get_room_detail(room)
		self.assertEqual(detail["stay"]["guest_name"], "_Test Detail Guest")
		self.assertEqual(detail["stay"]["status"], "Checked In")
		self.assertEqual(detail["folio"]["subtotal"], 500)
		self.assertEqual(detail["folio"]["tax"], 75)
		self.assertEqual(detail["folio"]["total"], 575)
		self.assertEqual(detail["folio"]["balance"], 375)
		self.assertEqual(detail["folio"]["name"], folio.name)
