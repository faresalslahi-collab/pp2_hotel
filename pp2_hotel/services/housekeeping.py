import frappe
from frappe.utils import now_datetime

from pp2_hotel.services.room_status import set_room_status

ACTIVE_TASK_STATUSES = ("Pending", "In Progress")
NEEDS_ATTENTION_STATUSES = ("Dirty", "Cleaning", "Clean")


def create_task(room, assigned_to=None, priority="Normal"):
	existing = frappe.db.get_value(
		"Housekeeping Task", {"room": room, "status": ["in", ACTIVE_TASK_STATUSES]}, "name"
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Housekeeping Task",
			"room": room,
			"assigned_to": assigned_to,
			"priority": priority,
		}
	).insert(ignore_permissions=True)
	return doc.name


def start_cleaning(task):
	doc = frappe.get_doc("Housekeeping Task", task)
	if doc.status != "Pending":
		frappe.throw(frappe._("Only a Pending task can be started."))
	doc.status = "In Progress"
	doc.started_at = now_datetime()
	doc.save(ignore_permissions=True)
	set_room_status(doc.room, "Cleaning")
	return doc.name


def mark_clean(task):
	doc = frappe.get_doc("Housekeeping Task", task)
	if doc.status != "In Progress":
		frappe.throw(frappe._("Only a task In Progress can be marked Clean."))
	doc.status = "Completed"
	doc.completed_at = now_datetime()
	doc.save(ignore_permissions=True)
	set_room_status(doc.room, "Clean")
	return doc.name


def inspect(task, result, inspector=None, notes=None):
	if result not in ("Passed", "Failed"):
		frappe.throw(frappe._("Inspection result must be Passed or Failed."))
	doc = frappe.get_doc("Housekeeping Task", task)
	if doc.status != "Completed":
		frappe.throw(frappe._("Only a Completed task can be inspected."))

	frappe.get_doc(
		{
			"doctype": "Room Inspection",
			"housekeeping_task": doc.name,
			"inspector": inspector or frappe.session.user,
			"result": result,
			"notes": notes,
		}
	).insert(ignore_permissions=True)

	if result == "Passed":
		doc.status = "Inspected"
		doc.save(ignore_permissions=True)
		set_room_status(doc.room, "Available")
	else:
		# Re-queue: back to Pending with no start/complete timestamps, as if
		# cleaning never happened -- a failed inspection means it didn't.
		doc.status = "Pending"
		doc.started_at = None
		doc.completed_at = None
		doc.save(ignore_permissions=True)
		set_room_status(doc.room, "Dirty")
	return doc.name


def report_maintenance(task, description):
	if not description:
		frappe.throw(frappe._("A description is required to report maintenance."))
	doc = frappe.get_doc("Housekeeping Task", task)
	doc.notes = (
		f"{doc.notes}\n\nMaintenance reported: {description}"
		if doc.notes
		else f"Maintenance reported: {description}"
	)
	doc.save(ignore_permissions=True)
	set_room_status(doc.room, "Maintenance")

	# Phase 8: also produces a real, queryable Maintenance Request instead of
	# just this note on the task -- import deferred to avoid a module-load
	# cycle (services/maintenance.py imports this module for create_task()).
	from pp2_hotel.services.maintenance import create_request

	create_request(doc.room, description, reported_by=frappe.session.user)

	return doc.name


def get_housekeeping_board(property=None):
	tasks = frappe.get_all(
		"Housekeeping Task",
		filters={"status": ["!=", "Inspected"]},
		fields=["name", "room", "status", "priority", "assigned_to", "started_at", "completed_at"],
		order_by="creation asc",
	)

	room_filters = {}
	if property:
		room_filters["property"] = property
	room_names = list({t.room for t in tasks})
	if room_names:
		room_filters["name"] = ["in", room_names]
	rooms = (
		frappe.get_all("Room", filters=room_filters, fields=["name", "room_number", "status"])
		if room_names
		else []
	)
	room_number_map = {r.name: r.room_number for r in rooms}
	room_status_map = {r.name: r.status for r in rooms}

	# A task can still be In Progress/Completed while its room has moved on
	# to Maintenance (services.housekeeping.report_maintenance() leaves the
	# task's own status untouched, deliberately, so its cleaning history
	# survives) -- but the room is no longer housekeeping's to act on once
	# that happens, so it must drop off this board even though its task
	# technically isn't Inspected yet. Only surface rows whose room is
	# actually still in a housekeeping-relevant status.
	board = [
		dict(t, room_number=room_number_map.get(t.room))
		for t in tasks
		if room_status_map.get(t.room) in NEEDS_ATTENTION_STATUSES
	]

	# Safety net: a room could in principle end up Dirty/Cleaning/Clean
	# without an active task if something outside this service set that
	# status directly (a Desk edit, bypassing the app entirely) -- the board
	# must still surface it rather than silently hiding a room that needs
	# attention. Not expected in normal operation: every writer of these
	# three statuses in this app goes through create_task/start_cleaning/
	# mark_clean, which always keep a task in step.
	task_room_names = {t.room for t in tasks}
	orphan_filters = dict(room_filters)
	orphan_filters["status"] = ["in", list(NEEDS_ATTENTION_STATUSES)]
	orphan_filters["name"] = ["not in", list(task_room_names) or [""]]
	orphans = frappe.get_all("Room", filters=orphan_filters, fields=["name", "room_number", "status"])
	for room in orphans:
		board.append(
			{
				"name": None,
				"room": room.name,
				"room_number": room.room_number,
				"status": None,
				"priority": None,
				"assigned_to": None,
				"started_at": None,
				"completed_at": None,
				"orphan_room_status": room.status,
			}
		)

	return board
