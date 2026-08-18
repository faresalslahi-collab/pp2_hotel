import frappe
from frappe.utils import flt

from pp2_hotel.services.housekeeping import create_task
from pp2_hotel.services.invoicing import generate_invoice

# Roles trusted to check a guest out with money still owed on the folio --
# same "reason required and recorded" convention as
# services.reservations.cancel_reservation/mark_no_show.
OVERRIDE_ROLES = {"System Manager", "Hotel Administrator", "Hotel Manager", "Front Desk Manager"}

BALANCE_EPSILON = 0.005  # avoid blocking checkout on float rounding noise


def check_out(stay, override_reason=None):
	stay_doc = frappe.get_doc("Hotel Stay", stay)
	if stay_doc.status != "Checked In":
		frappe.throw(frappe._("Only a Checked In stay can be checked out."))

	folio_name = frappe.db.get_value("Hotel Folio", {"stay": stay})
	folio = frappe.get_doc("Hotel Folio", folio_name) if folio_name else None
	balance = flt(folio.balance) if folio else 0.0
	overridden = False

	if balance > BALANCE_EPSILON:
		if not override_reason:
			frappe.throw(
				frappe._("Outstanding balance of {0} must be settled before checkout.").format(balance)
			)
		if not set(frappe.get_roles(frappe.session.user)) & OVERRIDE_ROLES:
			frappe.throw(frappe._("You do not have permission to check out with an outstanding balance."))
		overridden = True

	if folio:
		if overridden:
			folio.checkout_override_reason = override_reason
		folio.status = "Closed"
		folio.save(ignore_permissions=True)

	stay_doc.status = "Checked Out"
	stay_doc.save(ignore_permissions=True)

	# The room is now Dirty (services.stay.sync_room_status, triggered by the
	# save above) -- put it on the housekeeping board in the same breath
	# rather than leaving that as a second, easy-to-forget step.
	create_task(stay_doc.room)

	# A Company/accounts misconfiguration must never block a front desk
	# agent from physically checking a guest out -- invoice generation is
	# best-effort here, not a gate. See services/invoicing.py for the actual
	# Sales Invoice construction and its own idempotency/currency guards.
	invoice, invoice_error = None, None
	if folio:
		try:
			invoice = generate_invoice(folio.name)
		except Exception as e:
			frappe.log_error(title="pp2_hotel: invoice generation failed at checkout", message=frappe.get_traceback())
			invoice_error = str(e)

	return {
		"stay": stay_doc.name,
		"folio": folio.name if folio else None,
		"overridden": overridden,
		"invoice": invoice,
		"invoice_error": invoice_error,
	}
