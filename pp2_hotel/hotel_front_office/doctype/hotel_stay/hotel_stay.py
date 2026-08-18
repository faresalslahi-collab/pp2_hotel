# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from pp2_hotel.services.stay import sync_room_status


class HotelStay(Document):
	def validate(self):
		if getdate(self.departure) <= getdate(self.arrival):
			frappe.throw(frappe._("Departure must be after arrival."))
		if self.is_new() and not frappe.flags.via_checkin_service:
			frappe.throw(
				frappe._("A Hotel Stay can only be created by checking in a Reservation.")
			)

	def on_update(self):
		sync_room_status(self)
