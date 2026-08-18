import frappe

from pp2_hotel.services import rooms as rooms_service


@frappe.whitelist()
def get_room_detail(room):
	return rooms_service.get_room_detail(room)
