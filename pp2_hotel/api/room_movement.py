import frappe

from pp2_hotel.services.room_movement import move_room as _move_room


@frappe.whitelist()
def move_room(hotel_stay, to_room, reason=None):
	return _move_room(hotel_stay, to_room, reason)
