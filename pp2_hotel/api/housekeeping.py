import frappe

from pp2_hotel.services import housekeeping as housekeeping_service


@frappe.whitelist()
def get_housekeeping_board(property=None):
	return housekeeping_service.get_housekeeping_board(property)


@frappe.whitelist(methods=["POST"])
def start_cleaning(task):
	return housekeeping_service.start_cleaning(task)


@frappe.whitelist(methods=["POST"])
def mark_clean(task):
	return housekeeping_service.mark_clean(task)


@frappe.whitelist(methods=["POST"])
def inspect(task, result, inspector=None, notes=None):
	return housekeeping_service.inspect(task, result, inspector, notes)


@frappe.whitelist(methods=["POST"])
def report_maintenance(task, description):
	return housekeeping_service.report_maintenance(task, description)
