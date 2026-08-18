import frappe
from frappe.utils import flt, getdate, today


def get_effective_rate(room_type, on_date=None):
	"""The rate a Room Type should charge on a given date.

	An Active Rate Plan whose [start_date, end_date] covers `on_date` wins --
	Rate Plan.validate() guarantees at most one can ever match, so no
	tie-break rule is needed. Falls back to Room Type.base_rate when no plan
	covers the date (or none exists at all, which is every property today).
	"""
	on_date = getdate(on_date) if on_date else getdate(today())
	rate = frappe.db.get_value(
		"Rate Plan",
		{
			"room_type": room_type,
			"is_active": 1,
			"start_date": ["<=", on_date],
			"end_date": [">=", on_date],
		},
		"rate",
	)
	if rate is not None:
		return flt(rate)
	return flt(frappe.db.get_value("Room Type", room_type, "base_rate") or 0)
