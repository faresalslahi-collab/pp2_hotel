import frappe

from pp2_hotel.services import dashboard as dashboard_service


@frappe.whitelist()
def get_front_desk_kpis(property=None):
	return dashboard_service.get_front_desk_kpis(property)


@frappe.whitelist()
def get_room_grid(property=None):
	return dashboard_service.get_room_grid(property)
