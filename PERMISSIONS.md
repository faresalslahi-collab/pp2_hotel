# PP2 Hotel PMS Permissions

## 1. Role vocabulary (product brief section 17)

Eleven roles ship as a fixture (`fixtures/role.json`, re-synced on every
`bench migrate`): Hotel Administrator, Hotel Manager, Front Desk Manager,
Receptionist, Cashier, Housekeeping Manager, Housekeeper, Accountant,
Maintenance Manager, Maintenance Staff, Auditor. `System Manager` (Frappe's
built-in role) is always granted full access alongside `Hotel
Administrator` -- there's no separate "System Administrator" role to avoid
duplicating a built-in the way `qcore` avoided it for the same reason (see
`qcore`'s own ARCHITECTURE.md).

## 2. Frappe DocType permissions (role-based) -- current state

Phase 1 set a first-pass permission matrix on the nine doctypes it built;
later phases add their own doctypes on the same pattern:

| DocType | Full CRUD | Read/Write | Read only |
|---|---|---|---|
| Property | System Manager, Hotel Administrator | Hotel Manager | -- |
| Floor | System Manager, Hotel Administrator | Hotel Manager | -- |
| Room Type | System Manager, Hotel Administrator | Hotel Manager | Front Desk Manager, Receptionist |
| Room | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Receptionist, Housekeeping Manager, Housekeeper, Maintenance Manager, Maintenance Staff | Auditor |
| Guest | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Receptionist | Cashier |
| Reservation | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Receptionist | Cashier, Auditor |
| Hotel Stay | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Receptionist | Cashier, Auditor |
| Hotel Folio | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Cashier | Receptionist, Accountant, Auditor |
| Hotel Service | System Manager, Hotel Administrator | Hotel Manager | Front Desk Manager, Receptionist, Cashier |
| Housekeeping Task | System Manager, Hotel Administrator, Housekeeping Manager | Hotel Manager, Housekeeper | Front Desk Manager, Maintenance Manager, Auditor |
| Room Inspection | System Manager, Hotel Administrator | Hotel Manager, Housekeeping Manager | Housekeeper, Auditor |
| Rate Plan | System Manager, Hotel Administrator | Hotel Manager | Front Desk Manager, Receptionist |
| Room Movement | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Receptionist | Cashier, Auditor |
| Maintenance Request | System Manager, Hotel Administrator, Maintenance Manager | Hotel Manager, Maintenance Staff | Front Desk Manager, Housekeeping Manager, Auditor |
| Service Order | System Manager, Hotel Administrator | Hotel Manager, Front Desk Manager, Cashier | Receptionist, Accountant, Auditor |

This is a first pass, not a final matrix -- it exists so the eleven roles
mean something concrete rather than being decorative fixture data. A
Housekeeper can now actually *do* something with their permissions
(Phase 4 gave that role its first real doctype) -- they can create/update
Housekeeping Tasks but only read Room Inspections, deliberately: an
inspection is meant to be an independent QA check, not something the
person who did the cleaning records themselves. Phase 8 finally gives
Maintenance Manager/Staff a real doctype of their own (Maintenance
Request) -- Maintenance Staff can create/update requests, same DocType
permission level as Housekeeper has on Housekeeping Task. Unlike
checkout's balance override, `resolve_request`/`cancel_request` have no
extra role gate of their own -- reporting, starting, resolving and
cancelling a maintenance issue don't carry the same financial-risk
character that earns checkout its special `OVERRIDE_ROLES` check (see
below), so any authenticated user the DocType permission table already
lets through can call them, same as every Housekeeping transition. Note
that DocType-level `create`/`write` doesn't equal an unguarded write
path:
`confirm_reservation`/`cancel_reservation`/`mark_no_show`/`check_in`/
`add_charge`/`add_payment`/`check_out`/`start_cleaning`/`mark_clean`/
`inspect`/`report_maintenance`/`move_room`/`generate_invoice`/
`create_order`/`deliver_order`/`cancel_order` are all
service functions a Receptionist, Cashier or Housekeeper reaches
through, not raw document saves -- the interesting business rules (room
release on cancel, the check-in guard on Hotel Stay, the checkout
balance gate below, the stage-skipping guards on Housekeeping Task,
`move_room`'s Checked-In/Available/same-property/max-occupancy guards)
live there, not in the permission table.

**`services/invoicing.py` writes ERPNext's own Customer and Sales
Invoice doctypes via `ignore_permissions=True`**, same as every other
service function in this app writes pp2_hotel's own doctypes -- no
Front Desk/Cashier role is granted direct DocType permission on Customer
or Sales Invoice, because none of them ever touch those doctypes
directly; they only ever go through `check_out()`/`generate_invoice()`.
An Accountant reviewing/submitting the resulting Draft invoices does so
in ERPNext Desk under ERPNext's own Sales Invoice permission model,
which this app doesn't alter.

**Checkout's balance override is its own, narrower authority check, on
top of the table above.** Anyone with `write` on Hotel Stay can call
`services.checkout.check_out()`, but if the folio's balance is still
positive, the caller must *also* hold `System Manager`, `Hotel
Administrator`, `Hotel Manager`, or `Front Desk Manager` (`services/
checkout.py:OVERRIDE_ROLES`) -- a Receptionist or Cashier can check out a
fully-settled folio but cannot wave through an outstanding balance, even
with a reason typed in. This is enforced in `services/checkout.py`, not
via a DocType permission (Frappe's permission model has no "except when
this field is positive" concept), so it's documented here rather than in
the table above.

## 3. Property-scoped access (Phase 12)

**New doctype `Property User`** (`property`, `user`) -- the "user is a
member of this property" relationship this section used to say didn't
exist yet. Managed via `/configuration/property-access` (System
Manager/Hotel Administrator only) or Frappe Desk directly.

`pp2_hotel/permissions.py` registers `has_permission` and
`permission_query_conditions` in `hooks.py` for the seven doctypes that
carry a *direct* `property` field: `Room`, `Room Type`, `Floor`,
`Rate Plan`, `Hotel Stay`, `Hotel Folio`, `Reservation`. System Manager
and Hotel Administrator are exempt (see everything, matching every other
role-based check in this app); every other role only sees documents for
a Property they have a `Property User` record for -- a user with *no*
grants at all sees nothing property-scoped, fail closed rather than fail
open. Mirrors `qcore/utils/tenant.py`'s own tenant-isolation approach,
applied to properties instead of organizations, exactly as ARCHITECTURE.md's
"Multi-property readiness" section always said it would.

**Read the scope of this carefully -- it is real, but narrower than it
sounds.** `has_permission`/`permission_query_conditions` are hooks into
`frappe.get_list`/direct document access -- they gate Frappe Desk and the
Configuration UI's own `createListResource`-backed reads (Phase 11), both
of which go through that permission-checked path. **They do not reach the
custom Vue app's own dashboards, boards, and reports.** Every one of
those (Room Grid, Arrivals/Departures/In-House, the Housekeeping/
Maintenance/Service Orders boards, the Reservation Calendar, every Phase
5 Report) is a whitelisted `api.*` function that reads via
`frappe.get_all()` -- which is documented to skip permission checks
entirely, by design, and has been used that way in every single service
function in this app since Phase 1. Making the Vue app itself
property-scoped would mean adding an explicit property-membership check
inside each of those ~15 functions individually (or switching them to a
permission-respecting query path and accepting the performance/behavior
change that implies) -- a materially larger undertaking than a `hooks.py`
registration, and deliberately left for a future phase rather than
silently claimed here. With a single demo Property today, this
distinction has no visible effect either way; it will matter the moment
a second Property and a non-admin user both exist.

## 4. Role-based navigation (frontend)

The Vue app's sidebar (`frontend/src/router/nav.ts`) filters items against
`sessionStore.roles` from Frappe boot data -- unauthorized routes are
removed from the rendered tree entirely, not hidden with CSS, and the
filtering happens client-side for UX only (see `AppSidebar.vue`'s
`roles`-array pattern). This is **not** a security boundary by itself:
the real boundary is the DocType permission table above and the
`@frappe.whitelist()` API layer, both server-enforced. A user who
guesses a `ComingSoon` route by URL sees an empty page, not a data leak,
because none of those pages call any API yet.

## 5. Audit trail

`track_changes: 1` is set on every doctype except Hotel Service (a simple
rate-card master) and the child tables (Folio Item, Reservation Room --
child tables have no independent Version history in Frappe regardless of
the flag) -- Property, Floor, Room Type, Room, Guest, Hotel Stay, Hotel
Folio, Reservation, Housekeeping Task and Room Inspection all keep one.
Room Inspection doubles as its own audit trail by design (see
DATABASE.md -- a standalone record per inspection attempt, not a field
overwritten on re-inspection), so its Version history is closer to a
belt-and-suspenders than the primary record, unlike everywhere else.
A dedicated immutable audit log doctype (the brief doesn't call for one
explicitly the way `qcore`'s QC Audit Log does) is not planned unless a
later phase's requirements need one beyond what `track_changes` already
gives via the Version doctype.

A reason is mandatory for the two Reservation actions that give something
back (`services.reservations.cancel_reservation`/`mark_no_show` both
`frappe.throw()` if called without one) -- the same "reason required for
overrides/reversals" convention `qcore` documents in its own
PERMISSIONS.md. Phase 3 applies it a third time: `services.checkout.
check_out()` requires (and permanently records, on `Hotel
Folio.checkout_override_reason`) a reason whenever it closes a folio with
an outstanding balance under an override.

## 6. Configuration UI (Phase 11) enforces the table above directly

`MasterListPage.vue`/`MasterFormDialog.vue` (Property/Floor/Room Type/
Rate Plan/Hotel Service's first Vue screens) call Frappe's generic
`frappe.client.insert`/`save`/`delete` with no service-layer function in
between -- unlike every write path elsewhere in this app, there's no
extra business-rule gate to document here, because there isn't one:
whether a role can create/edit/delete through these screens is exactly
what the permission matrix in section 2 already says, no more and no
less. Hotel Manager can edit an existing Room Type there (the table's
"Read/Write" row) but has no `create`/`delete` on it -- only System
Manager/Hotel Administrator do -- and the Configuration UI enforces
exactly that split, since Frappe rejects the underlying
`frappe.client.insert`/`delete` call server-side regardless of what the
page renders. It doesn't add or relax anything the DocType permission
table doesn't already grant.
