import frappe


def set_room_status(room, new_status, reason=None):
	"""Single writer-of-record for Room.status.

	Every service that changes a room's status (Hotel Stay lifecycle,
	Reservation confirm/cancel, Housekeeping) routes through here instead of
	calling frappe.db.set_value directly -- see ROOM_STATUS_ENGINE.md. `reason`
	is accepted for future callers that need to explain an override (none do
	yet); it's not persisted anywhere today.
	"""
	if frappe.db.get_value("Room", room, "status") != new_status:
		frappe.db.set_value("Room", room, "status", new_status)
