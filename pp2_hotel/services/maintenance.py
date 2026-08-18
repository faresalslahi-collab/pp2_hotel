import frappe
from frappe.utils import now_datetime

from pp2_hotel.services import housekeeping
from pp2_hotel.services.room_status import set_room_status

ACTIVE_REQUEST_STATUSES = ("Open", "In Progress")

# A room in one of these statuses is vacant/on the sellable track -- taking
# it out of rotation with "Maintenance" makes sense. Occupied/Reserved means
# a guest is (or will be) there; the ticket still tracks the issue, but the
# room's own status is left alone rather than mislabeling it unsellable.
VACANT_STATUSES = ("Available", "Dirty", "Cleaning", "Clean")


def create_request(room, description, priority="Normal", reported_by=None):
	existing = frappe.db.get_value(
		"Maintenance Request", {"room": room, "status": ["in", ACTIVE_REQUEST_STATUSES]}, "name"
	)
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Maintenance Request",
			"room": room,
			"description": description,
			"priority": priority,
			"reported_by": reported_by or frappe.session.user,
		}
	).insert(ignore_permissions=True)

	if frappe.db.get_value("Room", room, "status") in VACANT_STATUSES:
		set_room_status(room, "Maintenance")

	return doc.name


def start_work(request):
	doc = frappe.get_doc("Maintenance Request", request)
	if doc.status != "Open":
		frappe.throw(frappe._("Only an Open request can be started."))
	doc.status = "In Progress"
	doc.started_at = now_datetime()
	doc.save(ignore_permissions=True)
	return doc.name


def resolve_request(request, resolution_notes=None):
	doc = frappe.get_doc("Maintenance Request", request)
	if doc.status not in ACTIVE_REQUEST_STATUSES:
		frappe.throw(frappe._("Only an Open or In Progress request can be resolved."))
	doc.status = "Resolved"
	doc.resolved_date = now_datetime()
	doc.resolution_notes = resolution_notes
	doc.save(ignore_permissions=True)

	# The room needs a once-over before it's sellable again -- identical
	# vacate-and-clean pattern to checkout/move_room. Only fires if this
	# ticket was actually the one holding the room out of rotation (the
	# occupied-room case in create_request() never touched it).
	if frappe.db.get_value("Room", doc.room, "status") == "Maintenance":
		set_room_status(doc.room, "Dirty")
		housekeeping.create_task(doc.room)

	return doc.name


def cancel_request(request, reason):
	if not reason:
		frappe.throw(frappe._("A reason is required to cancel a Maintenance Request."))
	doc = frappe.get_doc("Maintenance Request", request)
	if doc.status not in ACTIVE_REQUEST_STATUSES:
		frappe.throw(frappe._("Only an Open or In Progress request can be cancelled."))
	doc.status = "Cancelled"
	doc.cancellation_reason = reason
	doc.save(ignore_permissions=True)

	# Nothing was actually done to the room -- a mistaken/duplicate report
	# reverts straight back to Available, no cleaning cycle needed (unlike a
	# genuine resolve_request(), which assumes work happened).
	if frappe.db.get_value("Room", doc.room, "status") == "Maintenance":
		set_room_status(doc.room, "Available")

	return doc.name


def get_maintenance_board(property=None):
	requests = frappe.get_all(
		"Maintenance Request",
		filters={"status": ["in", ACTIVE_REQUEST_STATUSES]},
		fields=["name", "room", "status", "priority", "assigned_to", "reported_date"],
		order_by="creation asc",
	)

	room_filters = {}
	if property:
		room_filters["property"] = property
	room_names = list({r.room for r in requests})
	if room_names:
		room_filters["name"] = ["in", room_names]
	rooms = (
		frappe.get_all("Room", filters=room_filters, fields=["name", "room_number"]) if room_names else []
	)
	room_number_map = {r.name: r.room_number for r in rooms}
	valid_room_names = set(room_number_map.keys()) if property else None

	return [
		dict(r, room_number=room_number_map.get(r.room))
		for r in requests
		if valid_room_names is None or r.room in valid_room_names
	]
