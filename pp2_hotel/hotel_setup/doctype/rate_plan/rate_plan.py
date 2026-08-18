# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class RatePlan(Document):
	def validate(self):
		if getdate(self.end_date) < getdate(self.start_date):
			frappe.throw(frappe._("End Date cannot be before Start Date."))
		self._validate_no_overlap()

	def _validate_no_overlap(self):
		if not self.is_active:
			return
		# Two ranges overlap iff each starts on or before the other's end --
		# keeps get_effective_rate() always resolving to at most one match,
		# with no tie-break rule needed.
		overlapping = frappe.get_all(
			"Rate Plan",
			filters={
				"name": ["!=", self.name or ""],
				"room_type": self.room_type,
				"is_active": 1,
				"start_date": ["<=", self.end_date],
				"end_date": [">=", self.start_date],
			},
			pluck="name",
		)
		if overlapping:
			frappe.throw(
				frappe._("This date range overlaps an existing active Rate Plan ({0}) for this Room Type.").format(
					overlapping[0]
				)
			)
