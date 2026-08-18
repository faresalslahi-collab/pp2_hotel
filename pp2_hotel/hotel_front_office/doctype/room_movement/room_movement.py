# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class RoomMovement(Document):
	def validate(self):
		if self.from_room == self.to_room:
			frappe.throw(frappe._("From Room and To Room cannot be the same."))
		self.rate_difference = flt(self.new_rate) - flt(self.old_rate)
