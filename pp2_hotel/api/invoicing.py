import frappe

from pp2_hotel.services.invoicing import generate_invoice as _generate_invoice


@frappe.whitelist()
def generate_invoice(folio):
	return _generate_invoice(folio)
