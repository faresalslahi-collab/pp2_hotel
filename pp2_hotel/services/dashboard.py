import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum
from frappe.utils import flt, today


def _property_filter(property=None):
	return {"property": property} if property else {}


def get_front_desk_kpis(property=None):
	filters = _property_filter(property)
	business_date = today()

	stay_filters = dict(filters)
	arrivals_today = frappe.db.count(
		"Hotel Stay", {**stay_filters, "arrival": business_date, "status": ["!=", "Checked Out"]}
	)
	departures_today = frappe.db.count(
		"Hotel Stay", {**stay_filters, "departure": business_date, "status": "Checked In"}
	)
	in_house_stays = frappe.get_all(
		"Hotel Stay",
		filters={**stay_filters, "status": "Checked In"},
		fields=["adults", "children"],
	)
	in_house_guests = sum(flt(s.adults) + flt(s.children) for s in in_house_stays)

	room_status_counts = {
		row.status: row.count
		for row in frappe.get_all(
			"Room",
			filters=filters,
			group_by="status",
			fields=["status", {"COUNT": "name", "as": "count"}],
		)
	}

	return {
		"arrivals_today": arrivals_today,
		"departures_today": departures_today,
		"in_house_guests": in_house_guests,
		"available_rooms": room_status_counts.get("Available", 0),
		"occupied_rooms": room_status_counts.get("Occupied", 0),
		"dirty_rooms": room_status_counts.get("Dirty", 0),
		"out_of_order_rooms": room_status_counts.get("Out of Order", 0),
		"todays_revenue": get_todays_revenue(property, business_date),
		"currency": _default_currency(property),
	}


def get_todays_revenue(property=None, posting_date=None):
	posting_date = posting_date or today()
	folio_item = DocType("Folio Item")
	folio = DocType("Hotel Folio")

	query = (
		frappe.qb.from_(folio_item)
		.join(folio)
		.on(folio_item.parent == folio.name)
		.select(Sum(folio_item.amount))
		.where(folio_item.posting_date == posting_date)
	)
	if property:
		query = query.where(folio.property == property)

	result = query.run()
	return flt(result[0][0]) if result and result[0][0] else 0.0


def _default_currency(property=None):
	if property:
		currency = frappe.db.get_value("Property", property, "default_currency")
		if currency:
			return currency
	return frappe.db.get_default("currency") or "USD"


def get_room_grid(property=None):
	filters = _property_filter(property)
	rooms = frappe.get_all(
		"Room",
		filters=filters,
		fields=["name", "room_number", "floor", "room_type", "status", "property"],
		order_by="room_number asc",
	)
	if not rooms:
		return rooms

	room_names = [r.name for r in rooms]
	stays = frappe.get_all(
		"Hotel Stay",
		filters={"room": ["in", room_names], "status": ["in", ["Checked In", "Reserved"]]},
		fields=["name", "room", "guest", "status"],
	)
	stay_by_room = {s.room: s for s in stays}

	guest_names = list({s.guest for s in stays})
	guest_name_map = _name_map("Guest", guest_names, "guest_name")

	floor_names = list({r.floor for r in rooms if r.floor})
	floor_name_map = _name_map("Floor", floor_names, "floor_name")

	room_type_names = list({r.room_type for r in rooms if r.room_type})
	room_type_map = _name_map("Room Type", room_type_names, "room_type_name")

	grid = []
	for room in rooms:
		stay = stay_by_room.get(room.name)
		grid.append(
			{
				"name": room.name,
				"room_number": room.room_number,
				"floor": floor_name_map.get(room.floor),
				"room_type": room_type_map.get(room.room_type, room.room_type),
				"status": room.status,
				"guest_name": guest_name_map.get(stay.guest) if stay else None,
				"stay": stay.name if stay else None,
			}
		)
	return grid


def _name_map(doctype, names, value_field):
	if not names:
		return {}
	rows = frappe.get_all(doctype, filters={"name": ["in", names]}, fields=["name", value_field])
	return {row.name: row.get(value_field) for row in rows}
