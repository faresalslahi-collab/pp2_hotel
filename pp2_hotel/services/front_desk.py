import frappe
from frappe.utils import add_days, getdate, today


def get_arrivals_today(property=None):
	"""Confirmed Reservation Room lines arriving today that haven't checked
	in yet -- the Arrivals page's worklist, each row driving a Check In
	action.
	"""
	reservation_room = frappe.qb.DocType("Reservation Room")
	reservation = frappe.qb.DocType("Reservation")

	query = (
		frappe.qb.from_(reservation_room)
		.join(reservation)
		.on(reservation_room.parent == reservation.name)
		.select(
			reservation.name.as_("reservation"),
			reservation_room.name.as_("reservation_room"),
			reservation.guest,
			reservation_room.room_type,
			reservation_room.room,
			reservation_room.arrival,
			reservation_room.departure,
			reservation_room.adults,
			reservation_room.children,
		)
		.where(reservation.status == "Confirmed")
		.where(reservation_room.arrival == today())
		# An unset Link field can be stored as SQL NULL or '' depending on how
		# the row was written -- confirmed both occur here (NULL via .insert()
		# with the field simply omitted). Match either.
		.where(reservation_room.hotel_stay.isnull() | (reservation_room.hotel_stay == ""))
	)
	if property:
		query = query.where(reservation.property == property)

	rows = query.run(as_dict=True)
	guest_names = _name_map("Guest", list({r.guest for r in rows}), "guest_name")
	room_type_names = _name_map("Room Type", list({r.room_type for r in rows}), "room_type_name")
	for row in rows:
		row["guest_name"] = guest_names.get(row["guest"])
		row["room_type_name"] = room_type_names.get(row["room_type"])
	return rows


def get_departures_today(property=None):
	filters = {"departure": today(), "status": "Checked In"}
	if property:
		filters["property"] = property
	stays = frappe.get_all(
		"Hotel Stay", filters=filters, fields=["name", "guest", "room", "arrival", "departure"]
	)
	return _enrich_stays(stays)


def get_in_house(property=None):
	filters = {"status": "Checked In"}
	if property:
		filters["property"] = property
	stays = frappe.get_all(
		"Hotel Stay", filters=filters, fields=["name", "guest", "room", "arrival", "departure"]
	)
	return _enrich_stays(stays)


def get_reservation_calendar(property=None, start_date=None, end_date=None):
	"""Rooms x date-range grid data for the visual Reservation Calendar --
	every Confirmed Reservation Room line touching the window, plus the full
	room list to render even a room with nothing booked. `hotel_stay` set on
	a row is the same "already checked in" signal used everywhere else in
	this app (Arrivals excludes it, the Room Drawer's canCheckOut mirrors it)
	-- the frontend uses it to color an in-house booking differently from an
	upcoming one.
	"""
	end_date = getdate(end_date) if end_date else add_days(getdate(today()), 13)
	start_date = getdate(start_date) if start_date else getdate(today())

	room_filters = {}
	if property:
		room_filters["property"] = property
	rooms = frappe.get_all(
		"Room", filters=room_filters, fields=["name", "room_number", "room_type"], order_by="room_number asc"
	)
	room_type_names = _name_map("Room Type", list({r.room_type for r in rooms}), "room_type_name")
	for room in rooms:
		room["room_type_name"] = room_type_names.get(room.room_type)

	reservation_room = frappe.qb.DocType("Reservation Room")
	reservation = frappe.qb.DocType("Reservation")
	query = (
		frappe.qb.from_(reservation_room)
		.join(reservation)
		.on(reservation_room.parent == reservation.name)
		.select(
			reservation_room.name.as_("reservation_room"),
			reservation_room.room,
			reservation_room.arrival,
			reservation_room.departure,
			reservation_room.hotel_stay,
			reservation.name.as_("reservation"),
			reservation.guest,
		)
		.where(reservation.status == "Confirmed")
		.where(reservation_room.arrival <= end_date)
		.where(reservation_room.departure >= start_date)
	)
	if property:
		query = query.where(reservation.property == property)
	bookings = query.run(as_dict=True)

	guest_names = _name_map("Guest", list({b.guest for b in bookings}), "guest_name")
	for booking in bookings:
		booking["guest_name"] = guest_names.get(booking["guest"])
		booking["checked_in"] = bool(booking["hotel_stay"])

	return {"start_date": start_date, "end_date": end_date, "rooms": rooms, "bookings": bookings}


def search_guests(query, property=None):
	"""Guest Search's backing lookup -- name/phone/email substring match,
	each hit enriched with whatever front-desk-relevant context already
	exists for it (an in-house room, an upcoming confirmed reservation) so
	staff can act on a result without a Guest Profile page to click into
	(none exists yet -- see DATABASE.md's Guest Document/Guest Preference
	entries). Distinct from NewReservation.vue's own guest picker, which
	only needs a name match to attach a guest to a new booking.
	"""
	query = (query or "").strip()
	if len(query) < 2:
		return []

	guests = frappe.get_all(
		"Guest",
		or_filters={
			"guest_name": ["like", f"%{query}%"],
			"phone": ["like", f"%{query}%"],
			"email": ["like", f"%{query}%"],
		},
		fields=["name", "guest_name", "phone", "email"],
		order_by="guest_name asc",
		limit=15,
	)
	if not guests:
		return guests

	guest_names = [g.name for g in guests]

	stay_filters = {"guest": ["in", guest_names], "status": "Checked In"}
	if property:
		stay_filters["property"] = property
	stay_by_guest = {
		s.guest: s
		for s in frappe.get_all("Hotel Stay", filters=stay_filters, fields=["name", "guest", "room"])
	}
	room_numbers = _name_map("Room", [s.room for s in stay_by_guest.values()], "room_number")

	# Confirmed AND still has at least one not-yet-checked-in room line --
	# same `hotel_stay.isnull() | == ""` check get_arrivals_today() uses, so
	# a guest who already checked in against every line of their own
	# reservation doesn't show as both "in-house" and "upcoming" at once.
	reservation_room = frappe.qb.DocType("Reservation Room")
	reservation = frappe.qb.DocType("Reservation")
	res_query = (
		frappe.qb.from_(reservation)
		.join(reservation_room)
		.on(reservation_room.parent == reservation.name)
		.select(reservation.name, reservation.guest, reservation.arrival)
		.where(reservation.status == "Confirmed")
		.where(reservation.guest.isin(guest_names))
		.where(reservation_room.hotel_stay.isnull() | (reservation_room.hotel_stay == ""))
		.orderby(reservation.arrival)
		.distinct()
	)
	if property:
		res_query = res_query.where(reservation.property == property)
	reservation_by_guest = {}
	for r in res_query.run(as_dict=True):
		# Earliest upcoming Confirmed reservation per guest, if more than one.
		reservation_by_guest.setdefault(r.guest, r)

	results = []
	for guest in guests:
		stay = stay_by_guest.get(guest.name)
		reservation = reservation_by_guest.get(guest.name)
		results.append(
			{
				"name": guest.name,
				"guest_name": guest.guest_name,
				"phone": guest.phone,
				"email": guest.email,
				"stay": stay.name if stay else None,
				"room": stay.room if stay else None,
				"room_number": room_numbers.get(stay.room) if stay else None,
				"reservation": reservation.name if reservation else None,
				"reservation_arrival": reservation.arrival if reservation else None,
			}
		)
	return results


def _enrich_stays(stays):
	if not stays:
		return stays
	guest_names = _name_map("Guest", list({s.guest for s in stays}), "guest_name")
	room_numbers = _name_map("Room", list({s.room for s in stays}), "room_number")
	folio_by_stay = {
		f.stay: f
		for f in frappe.get_all(
			"Hotel Folio",
			filters={"stay": ["in", [s.name for s in stays]]},
			fields=["stay", "balance", "currency"],
		)
	}
	for stay in stays:
		stay["guest_name"] = guest_names.get(stay["guest"])
		stay["room_number"] = room_numbers.get(stay["room"])
		folio = folio_by_stay.get(stay["name"])
		stay["balance"] = folio.balance if folio else None
		stay["currency"] = folio.currency if folio else None
	return stays


def _name_map(doctype, names, value_field):
	if not names:
		return {}
	rows = frappe.get_all(doctype, filters={"name": ["in", names]}, fields=["name", value_field])
	return {row.name: row.get(value_field) for row in rows}
