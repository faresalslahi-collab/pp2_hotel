# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.folio import add_charge, add_payment, get_folio_detail
from pp2_hotel.tests.factories import (
	make_checked_in_stay,
	make_guest,
	make_property,
	make_room,
	make_room_type,
)


class TestFolioService(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()
		self.room = make_room(self.property, self.room_type, "T-601", status="Occupied")
		self.stay = make_checked_in_stay(
			self.property, self.room, self.guest, add_days(today(), -1), add_days(today(), 1)
		)
		self.folio = frappe.get_doc(
			{"doctype": "Hotel Folio", "stay": self.stay.name, "currency": "SAR", "tax_rate": 0, "items": []}
		).insert(ignore_permissions=True)

	def test_add_charge_recomputes_totals(self):
		add_charge(self.folio.name, "Room Service", 75)
		folio = frappe.get_doc("Hotel Folio", self.folio.name)
		self.assertEqual(folio.subtotal, 75)
		self.assertEqual(folio.balance, 75)

	def test_add_payment_recomputes_balance(self):
		add_charge(self.folio.name, "Room Charge", 400)
		add_payment(self.folio.name, 150, "Cash")
		folio = frappe.get_doc("Hotel Folio", self.folio.name)
		self.assertEqual(folio.paid_amount, 150)
		self.assertEqual(folio.balance, 250)

	def test_add_payment_rejects_zero_or_negative_amount(self):
		self.assertRaises(frappe.ValidationError, add_payment, self.folio.name, 0, "Cash")
		self.assertRaises(frappe.ValidationError, add_payment, self.folio.name, -10, "Cash")

	def test_add_charge_and_payment_refused_on_closed_folio(self):
		frappe.db.set_value("Hotel Folio", self.folio.name, "status", "Closed")
		self.assertRaises(frappe.ValidationError, add_charge, self.folio.name, "Late Charge", 50)
		self.assertRaises(frappe.ValidationError, add_payment, self.folio.name, 50, "Cash")

	def test_get_folio_detail_includes_guest_and_room(self):
		add_charge(self.folio.name, "Room Charge", 400)
		add_payment(self.folio.name, 100, "Card", reference="1234")
		detail = get_folio_detail(self.folio.name)
		self.assertEqual(detail["guest_name"], "_Test Guest")
		self.assertEqual(detail["room"], self.room)
		self.assertEqual(len(detail["items"]), 1)
		self.assertEqual(len(detail["payments"]), 1)
		self.assertEqual(detail["balance"], 300)
