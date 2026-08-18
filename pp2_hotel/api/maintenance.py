import frappe

from pp2_hotel.services import maintenance as maintenance_service


@frappe.whitelist()
def get_maintenance_board(property=None):
	return maintenance_service.get_maintenance_board(property)


@frappe.whitelist(methods=["POST"])
def create_request(room, description, priority="Normal"):
	return maintenance_service.create_request(room, description, priority)


@frappe.whitelist(methods=["POST"])
def start_work(request):
	return maintenance_service.start_work(request)


@frappe.whitelist(methods=["POST"])
def resolve_request(request, resolution_notes=None):
	return maintenance_service.resolve_request(request, resolution_notes)


@frappe.whitelist(methods=["POST"])
def cancel_request(request, reason):
	return maintenance_service.cancel_request(request, reason)
