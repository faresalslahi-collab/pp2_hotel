# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

# Property.company links to ERPNext's Company, whose own test module chains
# into erpnext.tests.utils.ERPNextTestSuite the same way Customer does (see
# test_guest.py's comment for the full explanation) -- skip it here too.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]


class TestProperty(FrappeTestCase):
	def test_property_code_is_uppercased(self):
		doc = frappe.get_doc(
			{
				"doctype": "Property",
				"property_name": "_Test Lowercase Property",
				"property_code": "_test-lower-code",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(doc.property_code, "_TEST-LOWER-CODE")

	def test_property_code_must_be_unique(self):
		frappe.get_doc(
			{
				"doctype": "Property",
				"property_name": "_Test Dup Property One",
				"property_code": "_TEST-DUP-CODE",
			}
		).insert(ignore_permissions=True)
		self.assertRaises(
			frappe.DuplicateEntryError,
			frappe.get_doc(
				{
					"doctype": "Property",
					"property_name": "_Test Dup Property Two",
					"property_code": "_TEST-DUP-CODE",
				}
			).insert,
		)
