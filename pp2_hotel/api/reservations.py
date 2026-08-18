import frappe

from pp2_hotel.services import reservations as reservations_service


@frappe.whitelist(methods=["POST"])
def create_reservation(guest, property, rooms, source="Direct", notes=None):
	if isinstance(rooms, str):
		rooms = frappe.parse_json(rooms)
	return reservations_service.create_reservation(guest, property, rooms, source, notes)


@frappe.whitelist(methods=["POST"])
def confirm_reservation(reservation):
	return reservations_service.confirm_reservation(reservation)


@frappe.whitelist(methods=["POST"])
def cancel_reservation(reservation, reason):
	return reservations_service.cancel_reservation(reservation, reason)


@frappe.whitelist(methods=["POST"])
def mark_no_show(reservation, reason):
	return reservations_service.mark_no_show(reservation, reason)
