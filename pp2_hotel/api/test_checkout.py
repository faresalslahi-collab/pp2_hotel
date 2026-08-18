# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.checkout import check_out
from pp2_hotel.services.folio import add_charge, add_payment
from pp2_hotel.tests.factories import (
	make_checked_in_stay,
	make_company,
	make_guest,
	make_property,
	make_room,
	make_room_type,
)


class TestCheckout(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.property = make_property()
		self.room_type = make_room_type(self.property)
		self.guest = make_guest()
		self.room = make_room(self.property, self.room_type, "T-901", status="Occupied")
		self.stay = make_checked_in_stay(
			self.property, self.room, self.guest, add_days(today(), -1), add_days(today(), 1)
		)
		self.folio = frappe.get_doc(
			{"doctype": "Hotel Folio", "stay": self.stay.name, "currency": "SAR", "tax_rate": 0, "items": []}
		).insert(ignore_permissions=True)

	def test_checkout_succeeds_with_zero_balance(self):
		add_charge(self.folio.name, "Room Charge", 400)
		add_payment(self.folio.name, 400, "Cash")

		result = check_out(self.stay.name)

		self.assertFalse(result["overridden"])
		self.assertEqual(frappe.db.get_value("Hotel Stay", self.stay.name, "status"), "Checked Out")
		self.assertEqual(frappe.db.get_value("Hotel Folio", self.folio.name, "status"), "Closed")
		self.assertEqual(frappe.db.get_value("Room", self.room, "status"), "Dirty")

	def test_checkout_auto_creates_a_housekeeping_task(self):
		add_charge(self.folio.name, "Room Charge", 400)
		add_payment(self.folio.name, 400, "Cash")

		check_out(self.stay.name)

		task = frappe.db.get_value(
			"Housekeeping Task", {"room": self.room, "status": "Pending"}, "name"
		)
		self.assertIsNotNone(task)

	def test_checkout_succeeds_with_negative_balance_no_override_needed(self):
		add_charge(self.folio.name, "Room Charge", 400)
		add_payment(self.folio.name, 500, "Cash")  # overpaid
		result = check_out(self.stay.name)
		self.assertFalse(result["overridden"])

	def test_checkout_blocked_with_positive_balance_and_no_reason(self):
		add_charge(self.folio.name, "Room Charge", 400)
		self.assertRaises(frappe.ValidationError, check_out, self.stay.name)
		self.assertEqual(frappe.db.get_value("Hotel Stay", self.stay.name, "status"), "Checked In")

	def test_checkout_blocked_for_non_override_role_even_with_reason(self):
		add_charge(self.folio.name, "Room Charge", 400)
		frappe.set_user("Guest")
		try:
			self.assertRaises(
				frappe.ValidationError, check_out, self.stay.name, "Guest promised to pay later"
			)
		finally:
			frappe.set_user("Administrator")

	def test_checkout_with_override_succeeds_and_records_reason(self):
		add_charge(self.folio.name, "Room Charge", 400)
		# Administrator holds System Manager, an override role.
		result = check_out(self.stay.name, "Manager approved -- guest will settle by wire transfer")

		self.assertTrue(result["overridden"])
		folio = frappe.get_doc("Hotel Folio", self.folio.name)
		self.assertEqual(folio.status, "Closed")
		self.assertEqual(folio.checkout_override_reason, "Manager approved -- guest will settle by wire transfer")

	def test_checkout_refused_for_already_checked_out_stay(self):
		add_charge(self.folio.name, "Room Charge", 400)
		add_payment(self.folio.name, 400, "Cash")
		check_out(self.stay.name)
		self.assertRaises(frappe.ValidationError, check_out, self.stay.name)

	def test_checkout_generates_a_real_invoice_when_the_property_is_configured(self):
		# Own Property/Company, not self.property from setUp() -- setUp's
		# property has no Company configured on purpose (to exercise the
		# checkout-still-succeeds-without-one path in the other tests above),
		# so a company-configured checkout needs its own fixture entirely.
		company = make_company("_TEST-PP2-CHKINV-CO")
		property = make_property("_TEST-PP2-CHKINV", company=company)
		room_type = make_room_type(property)
		guest = make_guest("_Test Guest CHKINV")
		room = make_room(property, room_type, "T-902", status="Occupied")
		stay = make_checked_in_stay(
			property, room, guest, add_days(today(), -1), add_days(today(), 1)
		)
		folio = frappe.get_doc(
			{"doctype": "Hotel Folio", "stay": stay.name, "currency": "SAR", "tax_rate": 0, "items": []}
		).insert(ignore_permissions=True)
		add_charge(folio.name, "Room Charge", 400)
		add_payment(folio.name, 400, "Cash")

		result = check_out(stay.name)

		self.assertIsNone(result["invoice_error"])
		self.assertIsNotNone(result["invoice"])
		self.assertTrue(frappe.db.exists("Sales Invoice", result["invoice"]))
		self.assertEqual(frappe.db.get_value("Sales Invoice", result["invoice"], "grand_total"), 400)
