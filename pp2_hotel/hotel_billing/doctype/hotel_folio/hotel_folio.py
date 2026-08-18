# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class HotelFolio(Document):
	def validate(self):
		self.subtotal = sum(flt(item.amount) for item in self.items)
		self.tax_amount = flt(self.subtotal) * flt(self.tax_rate) / 100
		self.total = flt(self.subtotal) + flt(self.tax_amount)
		self.paid_amount = sum(flt(payment.amount) for payment in self.payments)
		self.balance = flt(self.total) - flt(self.paid_amount)
