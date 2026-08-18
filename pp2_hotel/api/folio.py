import frappe

from pp2_hotel.services import folio as folio_service


@frappe.whitelist()
def get_folio_detail(folio):
	return folio_service.get_folio_detail(folio)


@frappe.whitelist(methods=["POST"])
def add_charge(folio, description, amount, hotel_service=None, qty=1, rate=None, posting_date=None):
	return folio_service.add_charge(folio, description, amount, hotel_service, qty, rate, posting_date)


@frappe.whitelist(methods=["POST"])
def add_payment(folio, amount, payment_method, reference=None, notes=None, posting_date=None):
	return folio_service.add_payment(folio, amount, payment_method, reference, notes, posting_date)
