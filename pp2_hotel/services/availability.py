import frappe
from frappe.query_builder import DocType


def get_availability(property, room_type, arrival, departure):
	total_rooms = frappe.db.count(
		"Room",
		{
			"property": property,
			"room_type": room_type,
			"status": ["not in", ["Out of Order", "Maintenance"]],
		},
	)

	reservation_room = DocType("Reservation Room")
	reservation = DocType("Reservation")
	committed = (
		frappe.qb.from_(reservation_room)
		.join(reservation)
		.on(reservation_room.parent == reservation.name)
		.select(reservation_room.name)
		.where(reservation.status == "Confirmed")
		.where(reservation.property == property)
		.where(reservation_room.room_type == room_type)
		.where(reservation_room.arrival < departure)
		.where(reservation_room.departure > arrival)
		.run()
	)

	return max(total_rooms - len(committed), 0)
