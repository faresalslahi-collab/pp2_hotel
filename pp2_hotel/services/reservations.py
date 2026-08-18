import frappe

from pp2_hotel.services.rate_plan import get_effective_rate
from pp2_hotel.services.room_status import set_room_status


def create_reservation(guest, property, rooms, source="Direct", notes=None):
	"""rooms: list of dicts with room_type, room (optional), arrival, departure,
	adults, children, rate (optional -- defaults to the Rate Plan covering
	`arrival`, or Room Type.base_rate if none covers it).
	"""
	for row in rooms:
		if not row.get("rate"):
			row["rate"] = get_effective_rate(row["room_type"], row.get("arrival"))

	doc = frappe.get_doc(
		{
			"doctype": "Reservation",
			"guest": guest,
			"property": property,
			"source": source,
			"notes": notes,
			"rooms": rooms,
		}
	).insert(ignore_permissions=True)
	return doc.name


def confirm_reservation(reservation):
	doc = frappe.get_doc("Reservation", reservation)
	if doc.status not in ("Draft", "Confirmed"):
		frappe.throw(frappe._("Only a Draft reservation can be confirmed."))
	doc.status = "Confirmed"
	doc.save(ignore_permissions=True)
	for row in doc.rooms:
		if row.room:
			set_room_status(row.room, "Reserved")
	return doc.name


def cancel_reservation(reservation, reason):
	if not reason:
		frappe.throw(frappe._("A reason is required to cancel a Reservation."))
	doc = frappe.get_doc("Reservation", reservation)
	if doc.status in ("Cancelled", "No Show", "Completed"):
		frappe.throw(frappe._("This Reservation is already {0}.").format(doc.status))
	_release_reserved_rooms(doc)
	doc.status = "Cancelled"
	doc.notes = f"{doc.notes}\n\nCancelled: {reason}" if doc.notes else f"Cancelled: {reason}"
	doc.save(ignore_permissions=True)
	return doc.name


def mark_no_show(reservation, reason):
	if not reason:
		frappe.throw(frappe._("A reason is required to mark a Reservation as No Show."))
	doc = frappe.get_doc("Reservation", reservation)
	if doc.status != "Confirmed":
		frappe.throw(frappe._("Only a Confirmed reservation can be marked No Show."))
	_release_reserved_rooms(doc)
	doc.status = "No Show"
	doc.notes = f"{doc.notes}\n\nNo Show: {reason}" if doc.notes else f"No Show: {reason}"
	doc.save(ignore_permissions=True)
	return doc.name


def _release_reserved_rooms(doc):
	# Skip lines that already checked in -- that's an occupied room, not a
	# cancellation/no-show, and must never be silently reset to Available.
	for row in doc.rooms:
		if row.room and not row.hotel_stay:
			if frappe.db.get_value("Room", row.room, "status") == "Reserved":
				set_room_status(row.room, "Available")
