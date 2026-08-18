# Copyright (c) 2026, Code Ocean and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PropertyUser(Document):
	def validate(self):
		existing = frappe.db.exists(
			"Property User", {"property": self.property, "user": self.user, "name": ["!=", self.name or ""]}
		)
		if existing:
			frappe.throw(frappe._("{0} already has access to {1}.").format(self.user, self.property))
