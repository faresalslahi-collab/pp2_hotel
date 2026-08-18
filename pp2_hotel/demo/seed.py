"""Idempotent demo data for local development and UI review.

Run with:
    bench --site <site> execute pp2_hotel.demo.seed.run

Guarded by the demo Property's existence -- if PP2-DOH is already there, the
whole seed is assumed to have run already and this is a no-op. Not a fixture:
this is throwaway demo data, not reference configuration.
"""

import random

import frappe
from frappe.utils import add_days, nowdate

from pp2_hotel.services.checkin import check_in
from pp2_hotel.services.housekeeping import create_task
from pp2_hotel.services.reservations import confirm_reservation, create_reservation

PROPERTY_CODE = "PP2-DOH"

FLOORS = [("Floor 1", 1), ("Floor 2", 2), ("Floor 3", 3)]

ROOM_TYPES = [
	("Standard Room", 350, 2),
	("Deluxe Room", 550, 3),
	("Suite", 950, 4),
]

SERVICES = [
	("Breakfast", "Room Service", 45),
	("Laundry", "Laundry", 60),
	("Minibar", "Minibar", 35),
	("Airport Transfer", "Other", 120),
]

GUEST_NAMES = [
	"Ahmed Al-Sayed",
	"Fatima Noor",
	"John Carter",
	"Layla Haddad",
	"Michael Chen",
	"Sara Abdullah",
	"David Okafor",
	"Nora Al-Farsi",
]


def run():
	if frappe.db.exists("Property", PROPERTY_CODE):
		frappe.msgprint("Demo data already seeded -- skipping.")
		return

	company_name = _make_company()
	property_name = _make_property(company_name)
	floor_names = _make_floors(property_name)
	room_type_names = _make_room_types(property_name)
	room_names = _make_rooms(property_name, floor_names, room_type_names)
	_make_services()
	guest_names = _make_guests()
	_make_reservations_and_stays(property_name, room_names, guest_names)
	_make_housekeeping_tasks(room_names)

	frappe.db.commit()  # nosemgrep
	frappe.msgprint(f"Seeded demo property {property_name} with {len(room_names)} rooms.")


COMPANY_NAME = "PP2 Demo Hotel"


def _make_company():
	# Same name as the Property itself (one-to-one for this single-property
	# demo) -- currency/country match the Property's own below exactly, so
	# Phase 7's invoicing never hits its own multi-currency guard. Inserting
	# a Company triggers ERPNext's standard default-CoA/cost-center/
	# receivable-account creation (Sales - PDH, Debtors - PDH, Main - PDH),
	# which is all invoicing needs -- no Item required either (see
	# services/invoicing.py).
	if frappe.db.exists("Company", COMPANY_NAME):
		return COMPANY_NAME
	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": COMPANY_NAME,
			"abbr": "PDH",
			"default_currency": "SAR",
			"country": "Saudi Arabia",
		}
	).insert(ignore_permissions=True)
	return doc.name


def _make_property(company_name):
	doc = frappe.get_doc(
		{
			"doctype": "Property",
			"property_name": "PP2 Demo Hotel",
			"property_code": PROPERTY_CODE,
			"is_active": 1,
			"company": company_name,
			"country": "Saudi Arabia",
			"city": "Riyadh",
			"default_currency": "SAR",
			"timezone": "Asia/Riyadh",
			"default_tax_rate": 15,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _make_floors(property_name):
	names = []
	for floor_name, floor_number in FLOORS:
		doc = frappe.get_doc(
			{
				"doctype": "Floor",
				"floor_name": floor_name,
				"property": property_name,
				"floor_number": floor_number,
			}
		).insert(ignore_permissions=True)
		names.append(doc.name)
	return names


def _make_room_types(property_name):
	names = []
	for type_name, base_rate, max_occupancy in ROOM_TYPES:
		doc = frappe.get_doc(
			{
				"doctype": "Room Type",
				"room_type_name": type_name,
				"property": property_name,
				"base_rate": base_rate,
				"max_occupancy": max_occupancy,
				"description": f"{type_name} at PP2 Demo Hotel.",
			}
		).insert(ignore_permissions=True)
		names.append(doc.name)
	return names


# room_number -> status, keeps a believable front-desk mix rather than
# everything Available.
ROOM_STATUS_PLAN = {
	"Occupied": 6,
	"Available": 10,
	"Dirty": 3,
	"Reserved": 2,
	"Out of Order": 1,
	"Maintenance": 1,
}


def _make_rooms(property_name, floor_names, room_type_names):
	statuses = []
	for status, count in ROOM_STATUS_PLAN.items():
		statuses.extend([status] * count)
	random.shuffle(statuses)

	names = []
	for i, status in enumerate(statuses):
		floor_index = i % len(floor_names)
		floor = floor_names[floor_index]
		room_type = room_type_names[i % len(room_type_names)]
		room_number = str((floor_index + 1) * 100 + (i // len(floor_names)) + 1)
		doc = frappe.get_doc(
			{
				"doctype": "Room",
				"room_number": room_number,
				"property": property_name,
				"floor": floor,
				"room_type": room_type,
				"status": status,
			}
		).insert(ignore_permissions=True)
		names.append({"name": doc.name, "status": status, "room_type": room_type})
	return names


def _make_services():
	for service_name, service_type, rate in SERVICES:
		if frappe.db.exists("Hotel Service", service_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Hotel Service",
				"service_name": service_name,
				"service_type": service_type,
				"rate": rate,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)


def _make_guests():
	names = []
	for guest_name in GUEST_NAMES:
		doc = frappe.get_doc(
			{
				"doctype": "Guest",
				"guest_name": guest_name,
				"phone": f"+974-5{random.randint(1000000, 9999999)}",
				"email": guest_name.lower().replace(" ", ".").replace("-", "") + "@example.com",
			}
		).insert(ignore_permissions=True)
		names.append(doc.name)
	return names


def _make_reservations_and_stays(property_name, rooms, guest_names):
	# Goes through the real Reservation -> confirm -> check-in path (not a
	# direct Hotel Stay insert -- that's blocked outside the check-in
	# service, see hotel_stay.py's validate()) so the demo data actually
	# exercises Phase 2's code, not just Phase 1's.
	guest_pool = iter(random.sample(guest_names, len(guest_names)))

	def next_guest():
		nonlocal guest_pool
		try:
			return next(guest_pool)
		except StopIteration:
			guest_pool = iter(random.sample(guest_names, len(guest_names)))
			return next(guest_pool)

	for room in rooms:
		if room["status"] not in ("Occupied", "Reserved"):
			continue

		if room["status"] == "Occupied":
			arrival = add_days(nowdate(), -random.randint(1, 3))
			departure = add_days(nowdate(), random.randint(1, 4))
		else:
			arrival = add_days(nowdate(), random.randint(1, 5))
			departure = add_days(arrival, random.randint(1, 4))

		reservation_name = create_reservation(
			guest=next_guest(),
			property=property_name,
			rooms=[
				{
					"room_type": room["room_type"],
					"room": room["name"],
					"arrival": arrival,
					"departure": departure,
					"adults": random.choice([1, 1, 2]),
					"children": random.choice([0, 0, 0, 1]),
				}
			],
			source=random.choice(["Direct", "Phone", "Email", "Walk-in"]),
		)
		confirm_reservation(reservation_name)

		if room["status"] != "Occupied":
			continue

		reservation = frappe.get_doc("Reservation", reservation_name)
		result = check_in(reservation_name, reservation.rooms[0].name)
		_add_demo_folio_charges(result["folio"], room, arrival)


def _add_demo_folio_charges(folio_name, room, arrival):
	folio = frappe.get_doc("Hotel Folio", folio_name)
	rate = frappe.db.get_value("Room Type", room["room_type"], "base_rate") or 0

	nights_so_far = max(1, frappe.utils.date_diff(nowdate(), arrival))
	for n in range(nights_so_far):
		folio.append(
			"items",
			{
				"posting_date": add_days(arrival, n),
				"description": f"Room Charge -- {room['name']}",
				"rate": rate,
				"qty": 1,
				"amount": rate,
			},
		)
	if random.random() > 0.4:
		service_name, _, service_rate = random.choice(SERVICES)
		folio.append(
			"items",
			{
				"posting_date": nowdate(),
				"description": service_name,
				"hotel_service": service_name,
				"rate": service_rate,
				"qty": 1,
				"amount": service_rate,
			},
		)

	# paid_amount is derived from the payments table now, not directly settable.
	pay_fraction = random.choice([0, 0.5, 1.0])
	if pay_fraction:
		amount_due = round(sum(i.amount for i in folio.items), 2)
		folio.append(
			"payments",
			{
				"posting_date": nowdate(),
				"amount": round(amount_due * pay_fraction, 2),
				"payment_method": random.choice(["Cash", "Card", "Bank Transfer", "Online"]),
			},
		)
	folio.save(ignore_permissions=True)


def _make_housekeeping_tasks(rooms):
	# Rooms seeded directly as Dirty (not reached via the checkout service,
	# which would have created one itself) still need a real task so the
	# Housekeeping Dashboard has believable starting data instead of relying
	# on get_housekeeping_board()'s orphan-room safety net.
	for room in rooms:
		if room["status"] == "Dirty":
			create_task(room["name"], priority=random.choice(["Low", "Normal", "Normal", "High"]))
