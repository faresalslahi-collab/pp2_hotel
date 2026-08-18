# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from pp2_hotel.services.checkin import check_in
from pp2_hotel.services.checkout import check_out
from pp2_hotel.services.folio import add_charge, add_payment
from pp2_hotel.services.reservations import confirm_reservation, create_reservation
from pp2_hotel.services.service_orders import cancel_order, create_order, deliver_order, get_service_board
from pp2_hotel.tests.factories import make_guest, make_property, make_room, make_room_type


class TestServiceOrders(FrappeTestCase):
	# Each test method builds its own Property/room/folio -- deliver_order/
	# cancel_order mutate the folio's items and the order's own state, and
	# FrappeTestCase only rolls back once at class teardown, so a shared
	# fixture would leak one method's order/charge into the next (same house
	# rule as every prior phase's service-level tests).
	def setUp(self):
		frappe.set_user("Administrator")

	def _open_folio(self, code, room_suffix="1"):
		property = make_property(code)
		room_type = make_room_type(property)
		guest = make_guest(f"_Test Guest {code}")
		room = make_room(property, room_type, f"T-S{room_suffix}", status="Available")
		name = create_reservation(
			guest,
			property,
			[{"room_type": room_type, "room": room, "arrival": today(), "departure": add_days(today(), 1), "adults": 1, "children": 0}],
		)
		confirm_reservation(name)
		reservation = frappe.get_doc("Reservation", name)
		result = check_in(name, reservation.rooms[0].name)
		return result["folio"], property, room

	def _service(self, code, rate=45, service_type="Room Service"):
		return frappe.get_doc(
			{"doctype": "Hotel Service", "service_name": f"_Test Service {code}", "service_type": service_type, "rate": rate}
		).insert(ignore_permissions=True).name

	def test_create_order_defaults_from_hotel_service(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC1")
		service = self._service("_TEST-PP2-SVC1", rate=45, service_type="Room Service")

		order = create_order(folio, hotel_service=service, qty=2)
		doc = frappe.get_doc("Service Order", order)

		self.assertEqual(doc.description, "_Test Service _TEST-PP2-SVC1")
		self.assertEqual(doc.rate, 45)
		self.assertEqual(doc.amount, 90)
		self.assertEqual(doc.service_type, "Room Service")
		self.assertEqual(doc.room, room)
		self.assertEqual(doc.status, "Pending")

	def test_create_order_rejects_no_description_and_no_rate(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC2")
		self.assertRaises(frappe.ValidationError, create_order, folio)

	def test_create_order_rejects_a_closed_folio(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC3")
		stay = frappe.db.get_value("Hotel Folio", folio, "stay")
		add_charge(folio, "Room Charge", 400)
		add_payment(folio, 400, "Cash")
		check_out(stay)
		self.assertRaises(
			frappe.ValidationError, create_order, folio, None, "Extra towels", 1, 10
		)

	def test_deliver_order_posts_a_real_folio_charge(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC4")
		order = create_order(folio, description="Extra towels", rate=10, qty=3)

		deliver_order(order)

		folio_doc = frappe.get_doc("Hotel Folio", folio)
		item = next(i for i in folio_doc.items if i.description == "Extra towels")
		self.assertEqual(item.amount, 30)
		self.assertEqual(item.qty, 3)
		self.assertEqual(frappe.db.get_value("Service Order", order, "status"), "Delivered")
		self.assertIsNotNone(frappe.db.get_value("Service Order", order, "delivered_at"))

	def test_deliver_order_rejects_a_folio_that_has_since_closed(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC5")
		order = create_order(folio, description="Minibar snack", rate=15)
		stay = frappe.db.get_value("Hotel Folio", folio, "stay")
		add_charge(folio, "Room Charge", 400)
		add_payment(folio, 400, "Cash")
		check_out(stay)

		self.assertRaises(frappe.ValidationError, deliver_order, order)

	def test_cancel_order_requires_a_reason(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC6")
		order = create_order(folio, description="Laundry bag", rate=20)
		self.assertRaises(frappe.ValidationError, cancel_order, order, "")

	def test_cancel_order_posts_no_charge(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC7")
		order = create_order(folio, description="Spa booking", rate=200)

		cancel_order(order, "Guest changed their mind")

		self.assertEqual(frappe.db.get_value("Service Order", order, "status"), "Cancelled")
		folio_doc = frappe.get_doc("Hotel Folio", folio)
		self.assertFalse(any(i.description == "Spa booking" for i in folio_doc.items))

	def test_get_service_board_filters_by_service_type_and_active_status(self):
		folio, property, room = self._open_folio("_TEST-PP2-SVC8")
		room_order = create_order(folio, description="Club sandwich", rate=55, service_type="Room Service")
		laundry_order = create_order(folio, description="Dry cleaning", rate=35, service_type="Laundry")
		delivered_order = create_order(folio, description="Bottled water", rate=8, service_type="Minibar")
		deliver_order(delivered_order)

		room_service_board = get_service_board(property, service_type="Room Service")
		self.assertTrue(any(row["name"] == room_order for row in room_service_board))
		self.assertFalse(any(row["name"] == laundry_order for row in room_service_board))
		self.assertFalse(any(row["name"] == delivered_order for row in room_service_board))

		all_board = get_service_board(property)
		self.assertTrue(any(row["name"] == room_order for row in all_board))
		self.assertTrue(any(row["name"] == laundry_order for row in all_board))
		self.assertFalse(any(row["name"] == delivered_order for row in all_board))
