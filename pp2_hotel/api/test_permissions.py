# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from pp2_hotel.tests.factories import make_property, make_room, make_room_type

# Property/Company/User are ERPNext-adjacent/core doctypes whose own test
# modules chain into ERPNextTestSuite's bootstrap the same way Guest.customer/
# Property.company already do (see test_guest.py/test_property.py) --
# creating a real User below triggers the same dependency walk.
IGNORE_TEST_RECORD_DEPENDENCIES = ["User"]


class TestPropertyScopedPermissions(FrappeTestCase):
	# Each test method builds its own two Properties/rooms/user -- property
	# membership is exactly the kind of state a shared fixture would leak
	# between methods, same house rule as every other phase's tests.
	def setUp(self):
		frappe.set_user("Administrator")

	def _two_properties_with_rooms(self, code):
		property_a = make_property(f"{code}-A")
		property_b = make_property(f"{code}-B")
		room_type_a = make_room_type(property_a)
		room_type_b = make_room_type(property_b)
		room_a = make_room(property_a, room_type_a, "PM1", status="Available")
		room_b = make_room(property_b, room_type_b, "PM1", status="Available")
		return property_a, property_b, room_a, room_b

	def _make_auditor(self, email):
		if frappe.db.exists("User", email):
			return email
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Auditor")
		return user.name

	def test_user_with_no_property_user_record_sees_nothing_property_scoped(self):
		property_a, property_b, room_a, room_b = self._two_properties_with_rooms("_TEST-PP2-PERM1")
		user = self._make_auditor("_test_pp2_perm1@example.com")
		self.assertFalse(frappe.has_permission("Room", doc=room_a, user=user))
		self.assertFalse(frappe.has_permission("Room", doc=room_b, user=user))

	def test_property_user_grant_allows_access_to_only_that_property(self):
		property_a, property_b, room_a, room_b = self._two_properties_with_rooms("_TEST-PP2-PERM2")
		user = self._make_auditor("_test_pp2_perm2@example.com")
		frappe.get_doc({"doctype": "Property User", "property": property_a, "user": user}).insert(
			ignore_permissions=True
		)

		self.assertTrue(frappe.has_permission("Room", doc=room_a, user=user))
		self.assertFalse(frappe.has_permission("Room", doc=room_b, user=user))

	def test_exempt_roles_see_everything_regardless_of_property_user(self):
		property_a, property_b, room_a, room_b = self._two_properties_with_rooms("_TEST-PP2-PERM3")
		# Administrator holds System Manager, an exempt role -- no Property
		# User record exists for it at all.
		self.assertTrue(frappe.has_permission("Room", doc=room_a, user="Administrator"))
		self.assertTrue(frappe.has_permission("Room", doc=room_b, user="Administrator"))

	def test_permission_query_conditions_filters_get_list(self):
		property_a, property_b, room_a, room_b = self._two_properties_with_rooms("_TEST-PP2-PERM4")
		user = self._make_auditor("_test_pp2_perm4@example.com")
		frappe.get_doc({"doctype": "Property User", "property": property_a, "user": user}).insert(
			ignore_permissions=True
		)

		frappe.set_user(user)
		try:
			visible = frappe.get_list("Room", filters={"name": ["in", [room_a, room_b]]}, pluck="name")
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(visible, [room_a])

	def test_property_user_rejects_a_duplicate_grant(self):
		property_a = make_property("_TEST-PP2-PERM5")
		user = self._make_auditor("_test_pp2_perm5@example.com")
		frappe.get_doc({"doctype": "Property User", "property": property_a, "user": user}).insert(
			ignore_permissions=True
		)
		self.assertRaises(
			frappe.ValidationError,
			frappe.get_doc({"doctype": "Property User", "property": property_a, "user": user}).insert,
			ignore_permissions=True,
		)
