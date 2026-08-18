# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class ServiceOrder(Document):
	def validate(self):
		self.amount = flt(self.rate) * flt(self.qty)
