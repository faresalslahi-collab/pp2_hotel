import frappe


def check_in(reservation, reservation_room, room=None):
	res = frappe.get_doc("Reservation", reservation)
	if res.status in ("Cancelled", "No Show", "Completed"):
		frappe.throw(frappe._("This Reservation is {0} and cannot be checked in.").format(res.status))
	row = next((r for r in res.rooms if r.name == reservation_room), None)
	if not row:
		frappe.throw(frappe._("Reservation Room row not found on this Reservation."))
	if row.hotel_stay:
		frappe.throw(frappe._("This room line has already been checked in."))

	target_room = row.room or room
	if not target_room:
		frappe.throw(frappe._("A room must be assigned before check-in."))

	room_doc = frappe.get_doc("Room", target_room)
	if room_doc.room_type != row.room_type:
		frappe.throw(frappe._("Room {0} is not a {1}.").format(target_room, row.room_type))
	if not row.room and room_doc.status != "Available":
		frappe.throw(frappe._("Room {0} is not Available.").format(target_room))

	frappe.flags.via_checkin_service = True
	try:
		stay = frappe.get_doc(
			{
				"doctype": "Hotel Stay",
				"guest": res.guest,
				"room": target_room,
				"property": res.property,
				"reservation": res.name,
				"arrival": row.arrival,
				"departure": row.departure,
				"adults": row.adults,
				"children": row.children,
				"rate": row.rate,
				"status": "Checked In",
			}
		).insert(ignore_permissions=True)
	finally:
		frappe.flags.via_checkin_service = False

	tax_rate = frappe.db.get_value("Property", res.property, "default_tax_rate") or 0
	currency = frappe.db.get_value("Property", res.property, "default_currency")
	folio = frappe.get_doc(
		{
			"doctype": "Hotel Folio",
			"stay": stay.name,
			"currency": currency,
			"tax_rate": tax_rate,
			"items": [],
		}
	).insert(ignore_permissions=True)

	row.room = target_room
	row.hotel_stay = stay.name
	if res.status == "Draft":
		res.status = "Confirmed"
	res.save(ignore_permissions=True)

	return {"hotel_stay": stay.name, "folio": folio.name}
