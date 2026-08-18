import frappe

from pp2_hotel.services import availability as availability_service


@frappe.whitelist()
def get_availability(property, room_type, arrival, departure):
	return availability_service.get_availability(property, room_type, arrival, departure)
