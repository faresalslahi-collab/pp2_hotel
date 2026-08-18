import frappe

from pp2_hotel.services import service_orders as service_orders_service


@frappe.whitelist()
def get_service_board(property=None, service_type=None):
	return service_orders_service.get_service_board(property, service_type)


@frappe.whitelist(methods=["POST"])
def create_order(folio, hotel_service=None, description=None, qty=1, rate=None, service_type=None):
	return service_orders_service.create_order(folio, hotel_service, description, qty, rate, service_type)


@frappe.whitelist(methods=["POST"])
def deliver_order(order):
	return service_orders_service.deliver_order(order)


@frappe.whitelist(methods=["POST"])
def cancel_order(order, reason):
	return service_orders_service.cancel_order(order, reason)
