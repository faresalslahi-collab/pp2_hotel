import frappe

from pp2_hotel.services import checkout as checkout_service


@frappe.whitelist(methods=["POST"])
def check_out(stay, override_reason=None):
	return checkout_service.check_out(stay, override_reason)
