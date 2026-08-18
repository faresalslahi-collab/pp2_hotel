import frappe
from frappe.utils import flt, today

from pp2_hotel.services import housekeeping
from pp2_hotel.services.rate_plan import get_effective_rate
from pp2_hotel.services.room_status import set_room_status


def move_room(hotel_stay, to_room, reason=None):
	stay = frappe.get_doc("Hotel Stay", hotel_stay)
	if stay.status != "Checked In":
		frappe.throw(frappe._("Only a Checked In stay can be moved to a different room."))

	from_room = stay.room
	if to_room == from_room:
		frappe.throw(frappe._("The destination room must be different from the current room."))

	to_room_doc = frappe.get_doc("Room", to_room)
	if to_room_doc.property != stay.property:
		frappe.throw(frappe._("The destination room must be in the same property as the stay."))
	if to_room_doc.status != "Available":
		frappe.throw(frappe._("Room {0} is not Available.").format(to_room))

	max_occupancy = frappe.db.get_value("Room Type", to_room_doc.room_type, "max_occupancy")
	if max_occupancy and (flt(stay.adults) + flt(stay.children)) > max_occupancy:
		frappe.throw(
			frappe._("Room {0} allows a maximum of {1} guests.").format(to_room, max_occupancy)
		)

	movement_date = today()
	old_rate = stay.rate
	new_rate = get_effective_rate(to_room_doc.room_type, movement_date)

	movement = frappe.get_doc(
		{
			"doctype": "Room Movement",
			"hotel_stay": stay.name,
			"movement_date": movement_date,
			"from_room": from_room,
			"to_room": to_room,
			"old_rate": old_rate,
			"new_rate": new_rate,
			"reason": reason,
		}
	).insert(ignore_permissions=True)

	stay.room = to_room
	stay.rate = new_rate
	stay.save(ignore_permissions=True)  # on_update() -> sync_room_status() marks to_room Occupied

	# The vacated room needs cleaning before it's sellable again -- identical
	# to what services.checkout.check_out() already does for a room a guest
	# leaves at the end of their stay, just triggered by a mid-stay move
	# instead of a departure.
	set_room_status(from_room, "Dirty")
	housekeeping.create_task(from_room)

	return {
		"movement": movement.name,
		"from_room": from_room,
		"to_room": to_room,
		"old_rate": old_rate,
		"new_rate": new_rate,
		"rate_difference": movement.rate_difference,
	}
