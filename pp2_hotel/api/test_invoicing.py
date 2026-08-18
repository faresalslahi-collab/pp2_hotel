# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.folio import add_charge, add_payment
from pp2_hotel.services.invoicing import generate_invoice, get_or_create_customer_for_guest
from pp2_hotel.tests.factories import make_checked_in_stay, make_company, make_guest, make_property, make_room, make_room_type


class TestInvoicing(FrappeTestCase):
	# Each test method builds its own Property/Company/Guest -- generate_invoice
	# mutates the Guest (auto-provisioning a Customer) and the Company's Sales
	# Invoice count, and FrappeTestCase only rolls back once at class teardown,
	# so a shared fixture would leak one method's invoice/customer into the
	# next (same house rule as every prior phase's report/movement tests).
	def setUp(self):
		frappe.set_user("Administrator")

	def _closed_folio(self, code, tax_rate=0, with_charge=True):
		company = make_company(f"{code}-CO")
		property = make_property(code, company=company)
		room_type = make_room_type(property)
		guest = make_guest(f"_Test Guest {code}")
		room = make_room(property, room_type, "T-INV1", status="Occupied")
		stay = make_checked_in_stay(
			property, room, guest, add_days(today(), -1), add_days(today(), 1), rate=400
		)
		folio = frappe.get_doc(
			{
				"doctype": "Hotel Folio",
				"stay": stay.name,
				"currency": "SAR",
				"tax_rate": tax_rate,
				"items": [],
			}
		).insert(ignore_permissions=True)
		if with_charge:
			add_charge(folio.name, "Room Charge", 400)
			add_payment(folio.name, 400 * (1 + tax_rate / 100), "Cash")
		frappe.db.set_value("Hotel Folio", folio.name, "status", "Closed")
		return frappe.get_doc("Hotel Folio", folio.name), guest, company

	def test_get_or_create_customer_for_guest_creates_once_and_reuses(self):
		guest = make_guest("_Test Guest INV-CUST")
		first = get_or_create_customer_for_guest(guest)
		self.assertTrue(frappe.db.exists("Customer", first))
		second = get_or_create_customer_for_guest(guest)
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count("Customer", {"customer_name": "_Test Guest INV-CUST"}), 1)

	def test_get_or_create_customer_for_guest_respects_existing_corporate_link(self):
		customer = frappe.get_doc(
			{"doctype": "Customer", "customer_name": "_Test Corporate Customer INV", "customer_type": "Company"}
		).insert(ignore_permissions=True)
		guest = make_guest("_Test Guest INV-CORP")
		frappe.db.set_value("Guest", guest, "customer", customer.name)
		self.assertEqual(get_or_create_customer_for_guest(guest), customer.name)

	def test_generate_invoice_produces_correct_items_and_tax(self):
		folio, guest, company = self._closed_folio("_TEST-PP2-INV1", tax_rate=15)
		invoice_name = generate_invoice(folio.name)
		invoice = frappe.get_doc("Sales Invoice", invoice_name)

		self.assertEqual(invoice.company, company)
		self.assertEqual(invoice.docstatus, 0)  # left as Draft, not auto-submitted
		self.assertEqual(len(invoice.items), 1)
		self.assertEqual(invoice.items[0].amount, 400)
		self.assertEqual(invoice.net_total, 400)
		self.assertEqual(len(invoice.taxes), 1)
		self.assertEqual(invoice.taxes[0].tax_amount, 60)
		self.assertEqual(invoice.grand_total, 460)
		self.assertEqual(frappe.db.get_value("Hotel Folio", folio.name, "sales_invoice"), invoice_name)

	def test_generate_invoice_is_idempotent(self):
		folio, guest, company = self._closed_folio("_TEST-PP2-INV2")
		first = generate_invoice(folio.name)
		second = generate_invoice(folio.name)
		self.assertEqual(first, second)
		self.assertEqual(frappe.db.count("Sales Invoice", {"company": company}), 1)

	def test_generate_invoice_returns_none_for_a_folio_with_no_charges(self):
		folio, guest, company = self._closed_folio("_TEST-PP2-INV3", with_charge=False)
		self.assertIsNone(generate_invoice(folio.name))

	def test_generate_invoice_rejects_an_open_folio(self):
		company = make_company("_TEST-PP2-INV4-CO")
		property = make_property("_TEST-PP2-INV4", company=company)
		room_type = make_room_type(property)
		guest = make_guest("_Test Guest INV4")
		room = make_room(property, room_type, "T-INV2", status="Occupied")
		stay = make_checked_in_stay(
			property, room, guest, add_days(today(), -1), add_days(today(), 1), rate=400
		)
		folio = frappe.get_doc(
			{"doctype": "Hotel Folio", "stay": stay.name, "currency": "SAR", "tax_rate": 0, "items": []}
		).insert(ignore_permissions=True)
		add_charge(folio.name, "Room Charge", 400)
		self.assertRaises(frappe.ValidationError, generate_invoice, folio.name)

	def test_generate_invoice_requires_a_configured_company(self):
		property = make_property("_TEST-PP2-INV5")  # no company
		# Frappe auto-fills a Link field literally named "company" from the
		# site's global default (frappe.defaults.get_global_default("company"))
		# even via a raw frappe.get_doc({...}).insert() -- passing company=None
		# in the dict isn't enough to keep it empty on a site that has *any*
		# global default company set (this bench does, from unrelated cross-app
		# data). Force it back to empty so this test actually exercises the
		# no-company-configured path instead of accidentally invoicing against
		# whatever company happens to be the site-wide default.
		frappe.db.set_value("Property", property, "company", None)
		room_type = make_room_type(property)
		guest = make_guest("_Test Guest INV5")
		room = make_room(property, room_type, "T-INV3", status="Occupied")
		stay = make_checked_in_stay(
			property, room, guest, add_days(today(), -1), add_days(today(), 1), rate=400
		)
		folio = frappe.get_doc(
			{"doctype": "Hotel Folio", "stay": stay.name, "currency": "SAR", "tax_rate": 0, "items": []}
		).insert(ignore_permissions=True)
		add_charge(folio.name, "Room Charge", 400)
		frappe.db.set_value("Hotel Folio", folio.name, "status", "Closed")
		self.assertRaises(frappe.ValidationError, generate_invoice, folio.name)
