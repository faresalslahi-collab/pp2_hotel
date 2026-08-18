# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class Reservation(Document):
	def validate(self):
		if not self.rooms:
			frappe.throw(frappe._("A Reservation needs at least one room line."))
		for row in self.rooms:
			if getdate(row.departure) <= getdate(row.arrival):
				frappe.throw(frappe._("Row #{0}: Departure must be after arrival.").format(row.idx))
		self.arrival = min(getdate(row.arrival) for row in self.rooms)
		self.departure = max(getdate(row.departure) for row in self.rooms)
