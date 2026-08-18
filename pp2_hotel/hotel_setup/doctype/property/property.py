# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class Property(Document):
	def before_naming(self):
		# autoname is "field:property_code" -- Frappe's _sync_autoname_field()
		# re-copies `name` back onto this field on every save, so normalizing
		# the case in validate() (which runs after naming) gets silently
		# clobbered back to whatever casing was typed. before_naming() runs
		# before set_new_name() reads this field, so it's the only hook that
		# actually sticks.
		self.property_code = (self.property_code or "").strip().upper()
