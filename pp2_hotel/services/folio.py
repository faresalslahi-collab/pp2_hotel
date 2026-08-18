import frappe
from frappe.utils import flt, today


def get_folio_detail(folio):
	doc = frappe.get_doc("Hotel Folio", folio)
	stay = frappe.db.get_value("Hotel Stay", doc.stay, ["room", "arrival", "departure"], as_dict=True)
	return {
		"name": doc.name,
		"stay": doc.stay,
		"guest": doc.guest,
		"guest_name": frappe.db.get_value("Guest", doc.guest, "guest_name"),
		"room": stay.room if stay else None,
		"room_number": frappe.db.get_value("Room", stay.room, "room_number") if stay else None,
		"arrival": stay.arrival if stay else None,
		"departure": stay.departure if stay else None,
		"status": doc.status,
		"currency": doc.currency,
		"subtotal": doc.subtotal,
		"tax_rate": doc.tax_rate,
		"tax_amount": doc.tax_amount,
		"total": doc.total,
		"paid_amount": doc.paid_amount,
		"balance": doc.balance,
		"checkout_override_reason": doc.checkout_override_reason,
		"sales_invoice": doc.sales_invoice,
		"items": [
			{
				"name": i.name,
				"posting_date": i.posting_date,
				"description": i.description,
				"hotel_service": i.hotel_service,
				"rate": i.rate,
				"qty": i.qty,
				"amount": i.amount,
			}
			for i in doc.items
		],
		"payments": [
			{
				"name": p.name,
				"posting_date": p.posting_date,
				"amount": p.amount,
				"payment_method": p.payment_method,
				"reference": p.reference,
				"notes": p.notes,
			}
			for p in doc.payments
		],
	}


def add_charge(folio, description, amount, hotel_service=None, qty=1, rate=None, posting_date=None):
	doc = frappe.get_doc("Hotel Folio", folio)
	if doc.status == "Closed":
		frappe.throw(frappe._("Cannot add a charge to a closed folio."))
	doc.append(
		"items",
		{
			"posting_date": posting_date or today(),
			"description": description,
			"hotel_service": hotel_service,
			"rate": rate if rate is not None else amount,
			"qty": qty,
			"amount": amount,
		},
	)
	doc.save(ignore_permissions=True)
	return doc.name


def add_payment(folio, amount, payment_method, reference=None, notes=None, posting_date=None):
	if flt(amount) <= 0:
		frappe.throw(frappe._("Payment amount must be greater than zero."))
	doc = frappe.get_doc("Hotel Folio", folio)
	if doc.status == "Closed":
		frappe.throw(frappe._("Cannot add a payment to a closed folio."))
	doc.append(
		"payments",
		{
			"posting_date": posting_date or today(),
			"amount": amount,
			"payment_method": payment_method,
			"reference": reference,
			"notes": notes,
		},
	)
	doc.save(ignore_permissions=True)
	return doc.name
