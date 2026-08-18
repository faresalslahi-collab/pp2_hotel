# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

# Guest.customer links to ERPNext's Customer. Frappe's test-record dependency
# walker (frappe/tests/utils/generators.py) would otherwise recurse into
# Customer and import erpnext.selling.doctype.customer.test_customer, whose
# module-level `ERPNextTestSuite()` bootstraps default Price Lists
# unconditionally -- on a site (like this bench's) that already has a real
# Company/Price List set up, that raises DuplicateEntryError before any test
# runs at all, for every app in the bench, not just pp2_hotel. Guest never
# needs a real Customer to test its own behaviour, so skip the dependency
# rather than working around ERPNext's bootstrap (which we don't own and
# shouldn't patch).
IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer"]


class TestGuest(FrappeTestCase):
	def test_guest_name_is_required(self):
		self.assertRaises(frappe.MandatoryError, frappe.get_doc({"doctype": "Guest"}).insert)

	def test_naming_series_produces_gst_prefixed_name(self):
		doc = frappe.get_doc({"doctype": "Guest", "guest_name": "_Test Guest Naming"}).insert(
			ignore_permissions=True
		)
		self.assertTrue(doc.name.startswith("GST-"))

	def test_customer_link_accepts_a_real_customer_without_triggering_bootstrap(self):
		# Directly creating a Customer here (rather than relying on Frappe's
		# automatic test-record generation) is what IGNORE_TEST_RECORD_
		# DEPENDENCIES above is meant to avoid -- this still exercises the
		# link field for real.
		customer_name = frappe.db.get_value("Customer", {"customer_name": "_Test Guest Customer"})
		if not customer_name:
			customer_name = frappe.get_doc(
				{"doctype": "Customer", "customer_name": "_Test Guest Customer", "customer_type": "Individual"}
			).insert(ignore_permissions=True).name

		doc = frappe.get_doc(
			{
				"doctype": "Guest",
				"guest_name": "_Test Guest With Customer",
				"customer": customer_name,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(doc.customer, customer_name)
