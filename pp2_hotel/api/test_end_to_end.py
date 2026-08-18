# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

"""Phase 13 -- a final testing pass. Every prior phase's own test file
verifies its feature in isolation; this one instead walks one guest
through the *entire* system in a single continuous scenario, the kind of
cross-phase interaction bug an isolated unit test can't catch (e.g. a
Room Movement's vacated room correctly feeding into the Housekeeping
cycle, or a Service Order's charge correctly showing up on the same
folio a Sales Invoice later gets generated from).
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, today

from pp2_hotel.services.checkin import check_in
from pp2_hotel.services.checkout import check_out
from pp2_hotel.services.folio import add_charge, add_payment
from pp2_hotel.services.housekeeping import inspect, mark_clean, start_cleaning
from pp2_hotel.services.maintenance import create_request, resolve_request
from pp2_hotel.services.reservations import confirm_reservation, create_reservation
from pp2_hotel.services.room_movement import move_room
from pp2_hotel.services.service_orders import create_order, deliver_order
from pp2_hotel.tests.factories import make_company, make_guest, make_property, make_room, make_room_type

# Company/Sales Invoice chain into ERPNext's test bootstrap the same way
# Guest.customer/Property.company/Hotel Folio.sales_invoice already do.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Sales Invoice"]


class TestFullGuestLifecycle(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_reservation_to_invoice_touches_every_phase_correctly(self):
		company = make_company("_TEST-PP2-E2E-CO")
		property = make_property("_TEST-PP2-E2E", company=company)
		standard = make_room_type(property, type_name="E2E Standard", base_rate=300)
		deluxe = make_room_type(property, type_name="E2E Deluxe", base_rate=500)
		guest = make_guest("_Test E2E Guest")
		room_a = make_room(property, standard, "E2E-101", status="Available")
		room_b = make_room(property, deluxe, "E2E-201", status="Available")

		# Phase 2: book and confirm.
		reservation_name = create_reservation(
			guest,
			property,
			[{"room_type": standard, "room": room_a, "arrival": today(), "departure": add_days(today(), 2), "adults": 1, "children": 0}],
		)
		confirm_reservation(reservation_name)
		self.assertEqual(frappe.db.get_value("Room", room_a, "status"), "Reserved")

		# Phase 2: check in -> Hotel Stay + Hotel Folio.
		reservation = frappe.get_doc("Reservation", reservation_name)
		result = check_in(reservation_name, reservation.rooms[0].name)
		stay_name, folio_name = result["hotel_stay"], result["folio"]
		self.assertEqual(frappe.db.get_value("Room", room_a, "status"), "Occupied")
		self.assertEqual(frappe.db.get_value("Hotel Stay", stay_name, "rate"), 300)

		# Phase 9: order a service, then deliver it -- bills the folio only
		# at delivery, not at order time.
		order_name = create_order(folio_name, description="Breakfast", rate=40, qty=1, service_type="Room Service")
		folio_before_delivery = frappe.get_doc("Hotel Folio", folio_name)
		self.assertEqual(len(folio_before_delivery.items), 0)
		deliver_order(order_name)
		folio_after_delivery = frappe.get_doc("Hotel Folio", folio_name)
		self.assertEqual(len(folio_after_delivery.items), 1)

		# Phase 3: a manual charge and a payment.
		add_charge(folio_name, "Room Charge", 300)
		add_payment(folio_name, 200, "Cash")

		# Phase 6: move the guest to a different Room Type -- financial
		# impact reflects the new room's own rate, and the vacated room
		# feeds straight into Phase 4's Housekeeping cycle.
		move_result = move_room(stay_name, room_b, reason="Guest requested an upgrade.")
		self.assertEqual(move_result["new_rate"], 500)
		self.assertEqual(frappe.db.get_value("Room", room_a, "status"), "Dirty")
		self.assertEqual(frappe.db.get_value("Room", room_b, "status"), "Occupied")
		self.assertEqual(frappe.db.get_value("Hotel Stay", stay_name, "room"), room_b)

		vacated_task = frappe.db.get_value("Housekeeping Task", {"room": room_a, "status": "Pending"}, "name")
		self.assertIsNotNone(vacated_task)
		start_cleaning(vacated_task)
		mark_clean(vacated_task)
		inspect(vacated_task, "Passed")
		self.assertEqual(frappe.db.get_value("Room", room_a, "status"), "Available")

		# Phase 8: report and resolve a maintenance issue on the now-Available
		# vacated room -- takes it out of rotation and back through
		# Housekeeping once resolved.
		request_name = create_request(room_a, "Squeaky door hinge.")
		self.assertEqual(frappe.db.get_value("Room", room_a, "status"), "Maintenance")
		resolve_request(request_name, "Oiled the hinge.")
		self.assertEqual(frappe.db.get_value("Room", room_a, "status"), "Dirty")
		self.assertIsNotNone(frappe.db.get_value("Housekeeping Task", {"room": room_a, "status": "Pending"}, "name"))

		# Phase 7: settle the balance and check out -- generates a real,
		# Draft Sales Invoice matching the folio exactly. Room Movement
		# never touches the folio itself (only Hotel Stay.rate, for
		# whatever gets charged next -- see services/room_movement.py), so
		# the balance here is just the breakfast + room charge minus what
		# was already paid: (40 + 300) - 200 = 140.
		add_payment(folio_name, 140, "Card")
		folio = frappe.get_doc("Hotel Folio", folio_name)
		self.assertAlmostEqual(flt(folio.balance), 0, places=2)

		checkout_result = check_out(stay_name)
		self.assertIsNone(checkout_result["invoice_error"])
		self.assertIsNotNone(checkout_result["invoice"])
		invoice = frappe.get_doc("Sales Invoice", checkout_result["invoice"])
		self.assertEqual(invoice.docstatus, 0)  # left as Draft
		self.assertEqual(flt(invoice.grand_total), flt(folio.total))
		self.assertEqual(frappe.db.get_value("Room", room_b, "status"), "Dirty")
		self.assertIsNotNone(frappe.db.get_value("Housekeeping Task", {"room": room_b, "status": "Pending"}, "name"))

		# Property-scoped permissions (Phase 12): Administrator sees
		# everything end to end, no Property User grant needed.
		self.assertTrue(frappe.has_permission("Hotel Folio", doc=folio_name, user="Administrator"))
		self.assertTrue(frappe.has_permission("Room", doc=room_b, user="Administrator"))
