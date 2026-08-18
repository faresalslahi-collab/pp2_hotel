import frappe
from frappe.utils import flt, today


def get_or_create_customer_for_guest(guest):
	"""Guest.customer is the corporate-billing override (see DATABASE.md) --
	if it's already set, use it as-is. Otherwise auto-provision an Individual
	Customer named after the guest and persist it back onto the Guest, so a
	returning guest always bills to the same Customer record.
	"""
	guest_doc = frappe.get_doc("Guest", guest)
	if guest_doc.customer:
		return guest_doc.customer

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": guest_doc.guest_name,
			"customer_type": "Individual",
		}
	).insert(ignore_permissions=True)
	guest_doc.customer = customer.name
	guest_doc.save(ignore_permissions=True)
	return customer.name


def generate_invoice(folio):
	doc = frappe.get_doc("Hotel Folio", folio)
	if doc.status != "Closed":
		frappe.throw(frappe._("An invoice can only be generated for a Closed folio."))

	if doc.sales_invoice and frappe.db.exists("Sales Invoice", doc.sales_invoice):
		if frappe.db.get_value("Sales Invoice", doc.sales_invoice, "docstatus") != 2:  # not Cancelled
			return doc.sales_invoice

	if not doc.items:
		return None

	company = frappe.db.get_value("Property", doc.property, "company")
	if not company:
		frappe.throw(
			frappe._("Property {0} has no Company configured -- cannot generate an invoice.").format(doc.property)
		)

	company_currency = frappe.db.get_value("Company", company, "default_currency")
	if doc.currency != company_currency:
		frappe.throw(
			frappe._(
				"Folio currency ({0}) does not match Company currency ({1}) -- multi-currency invoicing isn't supported yet."
			).format(doc.currency, company_currency)
		)

	customer = get_or_create_customer_for_guest(doc.guest)
	income_account, cost_center, debit_to = frappe.db.get_value(
		"Company", company, ["default_income_account", "cost_center", "default_receivable_account"]
	)

	invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": customer,
			"company": company,
			"posting_date": today(),
			"currency": doc.currency,
			"conversion_rate": 1,
			"selling_price_list": "Standard Selling",
			"price_list_currency": doc.currency,
			"plc_conversion_rate": 1,
			"debit_to": debit_to,
			"items": [
				{
					"item_name": item.description,
					"description": item.description,
					"uom": "Unit",
					"conversion_factor": 1,
					"qty": item.qty,
					"rate": item.rate,
					"amount": item.amount,
					"income_account": income_account,
					"cost_center": cost_center,
				}
				for item in doc.items
			],
		}
	)
	if flt(doc.tax_rate) > 0:
		invoice.append(
			"taxes",
			{
				"charge_type": "On Net Total",
				"account_head": _tax_account(company),
				"description": frappe._("Tax"),
				"rate": doc.tax_rate,
				"cost_center": cost_center,
			},
		)
	invoice.insert(ignore_permissions=True)  # left as Draft -- see services/invoicing.py's module note

	doc.sales_invoice = invoice.name
	doc.save(ignore_permissions=True)
	return invoice.name


def _tax_account(company):
	# ERPNext's standard CoA always creates a "Duties and Taxes" group under
	# every new Company -- reuse it as the parent for one dedicated leaf
	# account rather than requiring separate tax configuration this phase.
	abbr = frappe.db.get_value("Company", company, "abbr")
	account_name = f"Output Tax - {abbr}"
	if frappe.db.exists("Account", account_name):
		return account_name
	parent = frappe.db.get_value(
		"Account", {"company": company, "account_name": "Duties and Taxes", "is_group": 1}, "name"
	)
	return frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": "Output Tax",
			"company": company,
			"parent_account": parent,
			"account_type": "Tax",
			"is_group": 0,
		}
	).insert(ignore_permissions=True).name
