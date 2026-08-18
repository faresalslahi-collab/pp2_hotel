import frappe

from pp2_hotel.services import front_desk as front_desk_service


@frappe.whitelist()
def get_arrivals_today(property=None):
	return front_desk_service.get_arrivals_today(property)


@frappe.whitelist()
def get_departures_today(property=None):
	return front_desk_service.get_departures_today(property)


@frappe.whitelist()
def get_in_house(property=None):
	return front_desk_service.get_in_house(property)


@frappe.whitelist()
def get_reservation_calendar(property=None, start_date=None, end_date=None):
	return front_desk_service.get_reservation_calendar(property, start_date, end_date)


@frappe.whitelist()
def search_guests(query, property=None):
	return front_desk_service.search_guests(query, property)
