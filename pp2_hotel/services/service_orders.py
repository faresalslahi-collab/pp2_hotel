import frappe
from frappe.utils import flt, now_datetime

from pp2_hotel.services.folio import add_charge


def create_order(folio, hotel_service=None, description=None, qty=1, rate=None, service_type=None):
	folio_doc = frappe.get_doc("Hotel Folio", folio)
	if folio_doc.status != "Open":
		frappe.throw(frappe._("A service can only be ordered against an Open folio."))

	if hotel_service:
		service = frappe.get_doc("Hotel Service", hotel_service)
		description = description or service.service_name
		rate = rate if rate is not None else service.rate
		service_type = service_type or service.service_type

	if not description:
		frappe.throw(frappe._("A description is required (pick a Hotel Service or enter one manually)."))
	if not rate or flt(rate) <= 0:
		frappe.throw(frappe._("A positive rate is required (pick a Hotel Service or enter one manually)."))

	room = frappe.db.get_value("Hotel Stay", folio_doc.stay, "room")

	doc = frappe.get_doc(
		{
			"doctype": "Service Order",
			"folio": folio,
			"room": room,
			"hotel_service": hotel_service,
			"description": description,
			"qty": qty,
			"rate": rate,
			"service_type": service_type or "Other",
			"ordered_by": frappe.session.user,
		}
	).insert(ignore_permissions=True)
	return doc.name


def deliver_order(order):
	doc = frappe.get_doc("Service Order", order)
	if doc.status != "Pending":
		frappe.throw(frappe._("Only a Pending order can be delivered."))
	if frappe.db.get_value("Hotel Folio", doc.folio, "status") != "Open":
		frappe.throw(
			frappe._("This folio is already closed -- cancel this order instead of delivering it.")
		)

	doc.status = "Delivered"
	doc.delivered_at = now_datetime()
	doc.save(ignore_permissions=True)

	# The bill posts now, at delivery -- not at order time -- so a cancelled
	# order never touches the folio at all.
	add_charge(doc.folio, doc.description, doc.amount, hotel_service=doc.hotel_service, qty=doc.qty, rate=doc.rate)
	return doc.name


def cancel_order(order, reason):
	if not reason:
		frappe.throw(frappe._("A reason is required to cancel a Service Order."))
	doc = frappe.get_doc("Service Order", order)
	if doc.status != "Pending":
		frappe.throw(frappe._("Only a Pending order can be cancelled."))
	doc.status = "Cancelled"
	doc.cancellation_reason = reason
	doc.save(ignore_permissions=True)
	return doc.name


def get_service_board(property=None, service_type=None):
	filters = {"status": "Pending"}
	if service_type:
		filters["service_type"] = service_type

	orders = frappe.get_all(
		"Service Order",
		filters=filters,
		fields=["name", "room", "service_type", "description", "qty", "rate", "amount", "ordered_at"],
		order_by="creation asc",
	)

	room_filters = {}
	if property:
		room_filters["property"] = property
	room_names = list({o.room for o in orders})
	if room_names:
		room_filters["name"] = ["in", room_names]
	rooms = (
		frappe.get_all("Room", filters=room_filters, fields=["name", "room_number"]) if room_names else []
	)
	room_number_map = {r.name: r.room_number for r in rooms}
	valid_room_names = set(room_number_map.keys()) if property else None

	return [
		dict(o, room_number=room_number_map.get(o.room))
		for o in orders
		if valid_room_names is None or o.room in valid_room_names
	]
