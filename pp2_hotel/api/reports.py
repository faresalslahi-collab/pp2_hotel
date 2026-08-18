import frappe

from pp2_hotel.services import reports as reports_service


@frappe.whitelist()
def get_occupancy_revenue_report(property=None, start_date=None, end_date=None):
	return reports_service.get_occupancy_revenue_report(property, start_date, end_date)


@frappe.whitelist()
def get_guest_ledger(property=None, status=None):
	return reports_service.get_guest_ledger(property, status)


@frappe.whitelist()
def get_outstanding_balances(property=None):
	return reports_service.get_outstanding_balances(property)


@frappe.whitelist()
def get_payment_report(property=None, start_date=None, end_date=None):
	return reports_service.get_payment_report(property, start_date, end_date)


@frappe.whitelist()
def get_housekeeping_report(property=None, start_date=None, end_date=None):
	return reports_service.get_housekeeping_report(property, start_date, end_date)
