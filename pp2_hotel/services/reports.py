import frappe
from frappe.utils import add_days, flt, get_datetime, getdate, today


def get_occupancy_revenue_report(property=None, start_date=None, end_date=None):
	end_date = getdate(end_date) if end_date else getdate(today())
	start_date = getdate(start_date) if start_date else add_days(end_date, -6)

	room_filters = {"status": ["!=", "Out of Order"]}
	if property:
		room_filters["property"] = property
	total_rooms = frappe.db.count("Room", room_filters)

	stay_filters = {"status": ["in", ["Checked In", "Checked Out"]]}
	if property:
		stay_filters["property"] = property
	stays = frappe.get_all("Hotel Stay", filters=stay_filters, fields=["arrival", "departure"])

	folio_item = frappe.qb.DocType("Folio Item")
	folio = frappe.qb.DocType("Hotel Folio")

	daily = []
	total_room_revenue = 0.0
	total_other_revenue = 0.0
	total_room_nights = 0

	d = start_date
	while d <= end_date:
		occupied = sum(1 for s in stays if s.arrival <= d < s.departure)
		occupancy_pct = (occupied / total_rooms * 100) if total_rooms else 0.0

		query = (
			frappe.qb.from_(folio_item)
			.join(folio)
			.on(folio_item.parent == folio.name)
			.select(folio_item.amount, folio_item.hotel_service)
			.where(folio_item.posting_date == d)
		)
		if property:
			query = query.where(folio.property == property)
		rows = query.run(as_dict=True)

		room_revenue = sum(flt(r.amount) for r in rows if not r.hotel_service)
		other_revenue = sum(flt(r.amount) for r in rows if r.hotel_service)

		daily.append(
			{
				"date": d,
				"occupied_rooms": occupied,
				"total_rooms": total_rooms,
				"occupancy_pct": round(occupancy_pct, 1),
				"room_revenue": round(room_revenue, 2),
				"other_revenue": round(other_revenue, 2),
				"total_revenue": round(room_revenue + other_revenue, 2),
			}
		)

		total_room_revenue += room_revenue
		total_other_revenue += other_revenue
		total_room_nights += occupied
		d = add_days(d, 1)

	days_count = (end_date - start_date).days + 1
	available_room_nights = total_rooms * days_count
	adr = (total_room_revenue / total_room_nights) if total_room_nights else 0.0
	revpar = (total_room_revenue / available_room_nights) if available_room_nights else 0.0
	occupancy_pct_period = (
		(total_room_nights / available_room_nights * 100) if available_room_nights else 0.0
	)

	return {
		"start_date": start_date,
		"end_date": end_date,
		"total_rooms": total_rooms,
		"occupancy_pct": round(occupancy_pct_period, 1),
		"adr": round(adr, 2),
		"revpar": round(revpar, 2),
		"total_revenue": round(total_room_revenue + total_other_revenue, 2),
		"room_revenue": round(total_room_revenue, 2),
		"other_revenue": round(total_other_revenue, 2),
		"daily": daily,
	}


def get_guest_ledger(property=None, status=None):
	filters = {}
	if property:
		filters["property"] = property
	if status:
		filters["status"] = status
	folios = frappe.get_all(
		"Hotel Folio",
		filters=filters,
		fields=["name", "stay", "guest", "status", "total", "paid_amount", "balance", "currency"],
		order_by="creation desc",
	)
	return _enrich_folios(folios)


def get_outstanding_balances(property=None):
	# Deliberately not filtered to status=Open -- a Closed folio with a
	# balance is exactly what a Phase 3 checkout override produces (a guest
	# who left owing money), and that's real accounts-receivable, not
	# something checkout should have hidden by closing the folio.
	filters = {"balance": [">", 0.005]}
	if property:
		filters["property"] = property
	folios = frappe.get_all(
		"Hotel Folio",
		filters=filters,
		fields=[
			"name",
			"stay",
			"guest",
			"status",
			"total",
			"paid_amount",
			"balance",
			"currency",
			"checkout_override_reason",
		],
		order_by="balance desc",
	)
	return _enrich_folios(folios)


def get_payment_report(property=None, start_date=None, end_date=None):
	end_date = getdate(end_date) if end_date else getdate(today())
	start_date = getdate(start_date) if start_date else add_days(end_date, -6)

	folio_payment = frappe.qb.DocType("Folio Payment")
	folio = frappe.qb.DocType("Hotel Folio")

	query = (
		frappe.qb.from_(folio_payment)
		.join(folio)
		.on(folio_payment.parent == folio.name)
		.select(
			folio_payment.name,
			folio_payment.posting_date,
			folio_payment.amount,
			folio_payment.payment_method,
			folio_payment.reference,
			folio.name.as_("folio"),
			folio.guest,
			folio.stay,
			folio.currency,
		)
		.where(folio_payment.posting_date >= start_date)
		.where(folio_payment.posting_date <= end_date)
	)
	if property:
		query = query.where(folio.property == property)
	rows = query.run(as_dict=True)
	rows.sort(key=lambda r: r["posting_date"], reverse=True)

	guest_names = _name_map("Guest", list({r["guest"] for r in rows}), "guest_name")
	stay_names = list({r["stay"] for r in rows})
	stays = (
		frappe.get_all("Hotel Stay", filters={"name": ["in", stay_names]}, fields=["name", "room"])
		if stay_names
		else []
	)
	stay_room = {s.name: s.room for s in stays}
	room_map = _name_map("Room", list(set(stay_room.values())), "room_number")

	for r in rows:
		r["guest_name"] = guest_names.get(r["guest"])
		r["room_number"] = room_map.get(stay_room.get(r["stay"]))

	by_method: dict[str, float] = {}
	for r in rows:
		by_method[r["payment_method"]] = by_method.get(r["payment_method"], 0.0) + flt(r["amount"])

	return {
		"start_date": start_date,
		"end_date": end_date,
		"payments": rows,
		"total": round(sum(flt(r["amount"]) for r in rows), 2),
		"by_method": [{"payment_method": k, "total": round(v, 2)} for k, v in by_method.items()],
	}


def get_housekeeping_report(property=None, start_date=None, end_date=None):
	end_date = getdate(end_date) if end_date else getdate(today())
	start_date = getdate(start_date) if start_date else add_days(end_date, -29)
	range_start = f"{start_date} 00:00:00"
	range_end = f"{end_date} 23:59:59"

	tasks = frappe.get_all(
		"Housekeeping Task",
		filters={"creation": ["between", [range_start, range_end]]},
		fields=["name", "room", "status", "creation"],
	)

	if property:
		room_names = list({t.room for t in tasks})
		rooms_in_property = (
			set(frappe.get_all("Room", filters={"name": ["in", room_names], "property": property}, pluck="name"))
			if room_names
			else set()
		)
		tasks = [t for t in tasks if t.room in rooms_in_property]

	task_names = [t.name for t in tasks]
	inspections = frappe.get_all(
		"Room Inspection",
		filters={
			"housekeeping_task": ["in", task_names or [""]],
			"inspection_date": ["between", [range_start, range_end]],
		},
		fields=["housekeeping_task", "result", "inspection_date"],
	)
	passed = sum(1 for i in inspections if i.result == "Passed")
	failed = sum(1 for i in inspections if i.result == "Failed")
	pass_rate = (passed / (passed + failed) * 100) if (passed + failed) else 0.0

	# Average turnaround: for a task that reached Inspected, time from its
	# creation to the inspection that actually passed it.
	passed_at_by_task = {i.housekeeping_task: i.inspection_date for i in inspections if i.result == "Passed"}
	durations = []
	for t in tasks:
		if t.status != "Inspected":
			continue
		passed_at = passed_at_by_task.get(t.name)
		if passed_at:
			delta = get_datetime(passed_at) - get_datetime(t.creation)
			durations.append(delta.total_seconds() / 60.0)
	avg_turnaround_minutes = round(sum(durations) / len(durations), 1) if durations else None

	return {
		"start_date": start_date,
		"end_date": end_date,
		"total_tasks": len(tasks),
		"pending_tasks": sum(1 for t in tasks if t.status == "Pending"),
		"in_progress_tasks": sum(1 for t in tasks if t.status == "In Progress"),
		"completed_tasks": sum(1 for t in tasks if t.status == "Inspected"),
		"inspections_passed": passed,
		"inspections_failed": failed,
		"pass_rate": round(pass_rate, 1),
		"avg_turnaround_minutes": avg_turnaround_minutes,
	}


def _enrich_folios(folios):
	if not folios:
		return folios
	guest_names = _name_map("Guest", list({f.guest for f in folios}), "guest_name")
	stay_names = list({f.stay for f in folios})
	stays = frappe.get_all(
		"Hotel Stay", filters={"name": ["in", stay_names]}, fields=["name", "room", "arrival", "departure"]
	)
	stay_map = {s.name: s for s in stays}
	room_map = _name_map("Room", list({s.room for s in stays}), "room_number")

	result = []
	for f in folios:
		stay = stay_map.get(f.stay)
		result.append(
			dict(
				f,
				guest_name=guest_names.get(f.guest),
				room_number=room_map.get(stay.room) if stay else None,
				arrival=stay.arrival if stay else None,
				departure=stay.departure if stay else None,
			)
		)
	return result


def _name_map(doctype, names, value_field):
	if not names:
		return {}
	rows = frappe.get_all(doctype, filters={"name": ["in", names]}, fields=["name", value_field])
	return {row.name: row.get(value_field) for row in rows}
