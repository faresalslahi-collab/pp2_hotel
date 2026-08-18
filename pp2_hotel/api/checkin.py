import frappe

from pp2_hotel.services import checkin as checkin_service


@frappe.whitelist(methods=["POST"])
def check_in(reservation, reservation_room, room=None):
	return checkin_service.check_in(reservation, reservation_room, room)
