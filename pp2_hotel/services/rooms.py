import frappe


def get_room_detail(room):
	room_doc = frappe.get_doc("Room", room)
	data = {
		"room": {
			"name": room_doc.name,
			"room_number": room_doc.room_number,
			"floor": frappe.db.get_value("Floor", room_doc.floor, "floor_name") if room_doc.floor else None,
			"room_type": frappe.db.get_value("Room Type", room_doc.room_type, "room_type_name"),
			"status": room_doc.status,
			"property": room_doc.property,
		},
		"stay": None,
		"folio": None,
	}

	stay_name = frappe.db.get_value(
		"Hotel Stay",
		{"room": room, "status": ["in", ["Checked In", "Reserved"]]},
		"name",
		order_by="arrival desc",
	)
	if not stay_name:
		return data

	stay = frappe.get_doc("Hotel Stay", stay_name)
	data["stay"] = {
		"name": stay.name,
		"guest": stay.guest,
		"guest_name": frappe.db.get_value("Guest", stay.guest, "guest_name"),
		"arrival": stay.arrival,
		"departure": stay.departure,
		"status": stay.status,
	}

	folio_name = frappe.db.get_value("Hotel Folio", {"stay": stay.name}, "name")
	if folio_name:
		folio = frappe.get_doc("Hotel Folio", folio_name)
		data["folio"] = {
			"name": folio.name,
			"subtotal": folio.subtotal,
			"tax": folio.tax_amount,
			"total": folio.total,
			"paid": folio.paid_amount,
			"balance": folio.balance,
			"currency": folio.currency,
		}

	return data
