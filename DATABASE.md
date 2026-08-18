# PP2 Hotel PMS Database

Every DocType from the product brief's section-29 database design, in the
order it's expected to land. `[Phase 1 -- built]` entries exist in the
database today; `[Planned -- Phase N]` entries are documented here so the
full relationship design is on record before their Vue screens are written,
per the brief's own instruction not to build screens ahead of schema.

## Hotel Setup

### Property `[Phase 1 -- built, extended Phase 2]`

The top of the multi-property hierarchy. `autoname: field:property_code`.
Carries `company` (Link ERPNext Company) and `default_currency` so checkout
in a later phase can generate a Sales Invoice against the right company/
currency without guessing. Phase 2 adds `default_tax_rate` (Percent) --
prefills `Hotel Folio.tax_rate` when `services.checkin.check_in()` creates
a folio; still a per-property configured value, not a hardcoded system
default (brief section 18).

### Property User `[Phase 12 -- built]`

Not part of the brief's original section-29 schema -- added alongside
Phase 12's property-scoped `has_permission`/`permission_query_conditions`
mechanism (see PERMISSIONS.md section 3) as the "which users can see
which Property" relationship that mechanism needs. `property`, `user`,
both required; `validate()` rejects a duplicate `(property, user)` pair.
`autoname: hash` -- a plain membership record, no independent lifecycle.
Managed via `/configuration/property-access` or Frappe Desk.

### Floor `[Phase 1 -- built]`

Belongs to a Property (`autoname: hash`, `title_field: floor_name`). Exists
mainly to group Rooms for the Room Grid ("group by floor" in the frontend
spec) -- no independent business logic yet.

### Room Type `[Phase 1 -- built]`

Belongs to a Property (`autoname: format:{property}-{room_type_name}`).
`base_rate` is a display/default rate for the demo and for `Hotel
Stay.rate` snapshotting -- real rate management (seasonal/date-based
pricing) is `Rate Plan`, below.

### Rate Plan `[Phase 6 -- built]`

Per Room Type, date-range-aware pricing. `autoname: hash` (originally
Desk-managed like Floor -- Phase 11's Configuration UI gave it, Property,
Room Type, and Hotel Service their first Vue screens; see
ARCHITECTURE.md). `plan_name`, `property`, `room_type`,
`start_date`/`end_date`, `rate`, `is_active` (default checked).
`validate()` rejects `end_date < start_date` and rejects a date range
overlapping another *Active* Rate Plan for the same `room_type` --
`services.rate_plan.get_effective_rate(room_type, on_date)` therefore
always resolves to at most one match, falling back to `Room
Type.base_rate` when none covers the date (every property today, until
a Rate Plan is actually created). Consumed by
`services.reservations.create_reservation()` (rate defaults from the
line's `arrival` date) and `services.room_movement.move_room()` (rate
defaults from the move date) -- both one-line swaps of what used to be a
direct `base_rate` lookup, not new logic at either call site.

## Hotel Rooms

### Room `[Phase 1 -- built, extended Phase 4, Phase 8]`

`autoname: format:{property}-{room_number}` (property-qualified so the same
room number can exist at two properties without collision -- a gap the old
`hospitality_pms` app's simpler naming didn't need to worry about since we
started fresh). `status` is the single source of truth for room state --
`Available / Occupied / Dirty / Cleaning / Clean / Inspected / Reserved /
Out of Order / Maintenance`. Phase 4 added `Cleaning` (between `Dirty` and
`Clean` -- the brief's own Front Desk Dashboard mockup shows a room in
exactly this state) and, more importantly, gave `Clean`/`Inspected` their
first writer: Housekeeping. Phase 8 gives `Maintenance` its first real
writer too (`Maintenance Request`, below) -- `Out of Order` remains the
one state with no writer anywhere in this app, still Desk-only by design
(a separate, longer-term status from `Maintenance`'s active-repair
lifecycle). See ROOM_STATUS_ENGINE.md for the full writer-by-writer
picture, now centralized through `services/room_status.py`.

### Room Movement `[Phase 6 -- built]`

Room-to-room transfer with a financial-impact summary (brief section
11), living in `Hotel Front Office` (a Hotel Stay lifecycle event, not
its own module). `autoname: naming_series:` (`RM-.YYYY.-.#####`).
`hotel_stay`, `guest` (`fetch_from: hotel_stay.guest`, read-only -- so
the history list is readable with no join, same reasoning as Reservation
Room's `hotel_stay` forward-pointer), `from_room`/`to_room`,
`movement_date` (default Today), `old_rate`/`new_rate`, `rate_difference`
(read-only, `new_rate - old_rate`, computed in `validate()`), `reason`
(optional). `services.room_movement.move_room()` allows moving into a
*different* Room Type on purpose (an upgrade/downgrade, not just a
same-type swap) -- that's the entire reason this phase pairs with Rate
Plan, since the new room's rate needs a real lookup, not just its flat
`base_rate`. Guards: only a `Checked In` stay can move; the destination
must be `Available` and in the same property; a destination Room Type's
`max_occupancy` (if set) can't be exceeded by the stay's current
adults+children. The vacated room goes `Dirty` and gets a Housekeeping
Task, identical to what checkout already does when a guest departs --
see ROOM_STATUS_ENGINE.md. Deliberately does not touch already-posted
Folio Items: this app has no automatic nightly-room-charge job (every
Room Charge line is posted manually via `add_charge`), so a move only
changes `Hotel Stay.rate` going forward -- informational for whatever
gets charged next, not a retroactive proration engine the brief doesn't
ask for.

## Hotel Guests

### Guest `[Phase 1 -- built]`

`autoname: naming_series:` (`GST-.YYYY.-.#####`). Optional `customer` Link
to ERPNext Customer. Phase 7 finally gives this field a real writer:
`services.invoicing.get_or_create_customer_for_guest()` leaves it alone if
already set (the corporate-billing override this field was always meant
for), otherwise auto-provisions an Individual Customer named after the
guest the first time an invoice is generated and persists it back here --
so a returning guest always bills to the same Customer record, not a
fresh one every stay.

### Guest Document `[Planned -- Phase 3, with Guest Profile]`

ID/passport scans, attached per Guest. Re-deferred past Phase 2 -- there's
still no Guest Profile screen to show them on, so building the doctype now
would be build-ahead-of-need.

### Guest Preference `[Planned -- Phase 3, with Guest Profile]`

Free-form or structured guest preferences (room location, pillow type,
etc.) surfaced on the Guest Profile page -- same reasoning as Guest
Document, re-deferred to whichever phase actually ships that screen.

## Hotel Reservations `[Phase 2 -- built]`

### Reservation

`autoname: naming_series:` (`RES-.YYYY.-.#####`). `guest`, `property`,
`status` (`Draft / Confirmed / Cancelled / No Show / Completed`), `source`
(`Walk-in / Phone / Email / Direct / Other`), `notes`, child table `rooms`
(Reservation Room). `arrival`/`departure` are read-only, derived in
`validate()` as the min/max across the room lines -- the same lesson
already on record here from real hospitality-PMS practice: *"Reservation
header dates derive from the room lines."* `Completed` exists in the
Select but nothing sets it yet (no Checkout phase to trigger it) --
documented now so the full status lifecycle is on record.

### Reservation Room (child)

`autoname: hash`. `room_type` (required), `room` (optional -- may be
assigned at booking or left for check-in time), `arrival`, `departure`,
`adults`, `children`, `rate` (defaults from `Room Type.base_rate` in
`services.reservations.create_reservation()`), `hotel_stay` (Link, set
once this line is checked in by `services.checkin.check_in()` -- the
forward pointer from booking to stay; `Hotel Stay` doesn't carry a reverse
child-table reference, `reservation` is enough for display).

**Not built this phase:** multi-room-per-*Stay* (`Stay Room`, below) --
each Reservation Room line becomes its own Hotel Stay on check-in, so a
2-room booking produces 2 Hotel Stays, not one Stay spanning two rooms.
Group Reservation and Cancellations/No Shows as their own list screens
are still `ComingSoon` -- cancel/no-show exist as *actions* on the
Reservation Detail page (`services.reservations.cancel_reservation`/
`mark_no_show`), just not their own filtered views yet. The visual
Reservation Calendar shipped in Phase 10, below -- see
`services.front_desk.get_reservation_calendar()`; no new doctype, a pure
read-side aggregation over Reservation Room the same way Phase 5's
Reports are over Hotel Folio.

## Hotel Front Office

### Hotel Stay `[Phase 1 -- built, orchestrated Phase 2]`

`autoname: naming_series:` (`HS-.YYYY.-.#####`). Fields: `guest`, `room`,
`property`, `reservation` (Phase 2, Link Reservation, read-only,
traceability display only), `arrival`, `departure`, `adults`, `children`,
`rate`, `status`. **`status` options changed in Phase 2**: `Reserved` was
dropped (`Checked In / Checked Out` only) -- it was a Phase 1 stand-in for
a held-but-not-arrived room, a concept `Reservation` now owns properly (a
Confirmed Reservation with no Hotel Stay yet). `validate()` still rejects
departure <= arrival, and Phase 2 adds a second guard: creation is refused
unless `frappe.flags.via_checkin_service` is set, so a Hotel Stay can only
come from `services.checkin.check_in()` -- mirrors an integrity rule the
old `hospitality_pms` app enforced the same way. `on_update()` still calls
`services.stay.sync_room_status()`, whose map lost the `Reserved` entry
accordingly -- see ROOM_STATUS_ENGINE.md.

### Stay Room `[Planned -- Phase 3, with Reservations]`

Supports one Hotel Stay spanning multiple physical rooms (brief's "multiple
rooms under one reservation" edge case). Phase 2's check-in normalises the
other direction instead (one Reservation Room line -> one Hotel Stay, one
room each), matching the real hospitality-PMS precedent recorded above for
Reservation. Revisit if a later phase needs a single Stay/Folio spanning
multiple physical rooms rather than one Stay per room.

## Hotel Billing

### Hotel Folio `[Phase 1 -- built, extended Phase 3, Phase 7]`

`autoname: naming_series:` (`FOL-.YYYY.-.#####`). One folio per Hotel Stay
(`stay` is `unique`) -- multi-folio-per-stay (e.g. splitting a group
booking's charges across folios) is a later-phase concern once Group
Reservation exists. `guest`/`property` are fetched (read-only) from `stay`.
`validate()` recomputes `subtotal` from `items`, `tax_amount = subtotal *
tax_rate / 100`, `total = subtotal + tax_amount`, **`paid_amount` from
`payments` (Phase 3 -- see below)**, `balance = total - paid_amount`.
`tax_rate` defaults to 0 and is set per-document (the demo seed sets 15
for realism) -- deliberately not a system-wide default, per the brief's
instruction not to hard-code a jurisdiction's tax rate into the core.

Phase 3 adds: `payments` (Table, Folio Payment -- see below), `status`
gains real meaning (`services.checkout.check_out()` sets `Closed`, and
`services.folio.add_charge`/`add_payment` both refuse to touch a `Closed`
folio), and `checkout_override_reason` (Small Text, read-only) -- set only
when checkout closed this folio over a positive balance under an
authorized override. `paid_amount` changed from directly editable to
`read_only: 1` -- it's computed exactly like `subtotal`, not trusted from
input; `test_hotel_folio.py`, `api/test_rooms.py` and `demo/seed.py` all
had a direct `paid_amount = ...` assignment reworked into a `payments` row
accordingly.

Phase 7 adds `sales_invoice` (Link -> Sales Invoice, read-only) -- set once
`services.invoicing.generate_invoice()` produces a real ERPNext Sales
Invoice for this folio (left as Draft, not auto-submitted; see
ARCHITECTURE.md's Phase 7 note and `services/invoicing.py`). Null for
every Open folio and for any Closed folio with zero charges (nothing to
invoice) or where invoicing hasn't been (re)triggered yet.

### Folio Item `[Phase 1 -- built]`

Child table of Hotel Folio. `posting_date`, `description`, optional
`hotel_service` link, `rate`, `qty`, `amount`. No independent permissions
(child tables inherit the parent's).

### Folio Payment `[Phase 3 -- built]`

Child table of Hotel Folio, same shape/permission story as Folio Item.
`posting_date`, `amount`, `payment_method` (`Cash / Card / Bank Transfer /
Online / Other`), optional `reference` (card last 4, transaction ID,
cheque number), optional `notes`. `Hotel Folio.paid_amount` is the sum of
this table, the same way `subtotal` is the sum of `items` -- this *is*
"Payment Allocation" scoped to what Folio can actually support today (a
real, audited, multi-payment ledger), not the brief's section-14 mockup of
splitting one payment across charge categories Folio doesn't have yet. See
CHANGELOG.md's Phase 3 entry for the full reasoning.

### Payment Allocation `[Planned -- category-split UI, if Folio ever gets categorized charges]`

The brief's section-14 mockup (one payment split across Room Charges/
Restaurant/Laundry) needs Folio Items to belong to a category/ledger head
first -- they're a flat list today. Phase 3 delivered the part of this
concept that's real now (Folio Payment, above); a dedicated allocation
screen is only worth building once there's something to allocate against.

## Hotel Services

### Hotel Service `[Phase 1 -- built]`

`autoname: field:service_name`. Simple rate card (`service_type`,
`rate`) used as the `hotel_service` link on Folio Item, and now also on
Service Order (Phase 9), below.

### Service Order `[Phase 9 -- built]`

The room-service/laundry/minibar order workflow (brief section 14)
DATABASE.md has pointed at "a later phase" since this doctype's own
Phase 1 entry. `autoname: naming_series:` (`SVO-.YYYY.-.#####`). `folio`
(reqd), `room` (reqd, denormalized from the folio's stay -- same
direct-`room`-field convention Housekeeping Task/Maintenance Request
already use), `status` (`Pending / Delivered / Cancelled`), `service_type`
(same vocabulary as Hotel Service's own field), optional `hotel_service`
link (same optional-service pattern as Folio Item), `description`, `qty`,
`rate`, `amount` (read-only, `rate * qty`), `ordered_by`/`ordered_at`,
`delivered_at` (read-only), `cancellation_reason`.

Deliberately decoupled from `services.folio.add_charge()`: an order only
bills the folio when `services.service_orders.deliver_order()` marks it
`Delivered` -- placing an order never touches the folio, so a cancelled
one (`cancel_order()`, reason required) leaves no trace on the bill.
`AddChargeDialog.vue`/`add_charge()` are untouched by this phase -- an
instant, no-delivery-step charge (a flat fee, a damage charge) is a
still-valid, different need from a guest service order.

## Hotel Housekeeping `[Phase 4 -- built]`

### Housekeeping Task

`autoname: naming_series:` (`HKT-.YYYY.-.#####`). `room` (reqd),
`assigned_to` (Link User, optional), `priority` (`Low / Normal / High`,
default `Normal`), `status` (`Pending / In Progress / Completed /
Inspected`, default `Pending`), `started_at`/`completed_at` (Datetime,
read-only, set by the service layer), `notes`. Created automatically by
`services.checkout.check_out()` the moment a room goes `Dirty` -- see
ARCHITECTURE.md's layering notes -- rather than requiring a manual
"create task" step; `services.housekeeping.create_task()` dedupes against
an existing `Pending`/`In Progress` task for the same room so this is safe
to call defensively from more than one place.

### Room Inspection

`autoname: hash`. `housekeeping_task` (reqd), `room` (fetched, read-only),
`inspector` (Link User), `inspection_date` (Datetime, default now),
`result` (`Passed / Failed`), `notes`. A standalone doctype rather than a
field on Housekeeping Task -- per the brief's section-29 database design
listing them separately, and because a task can legitimately be inspected
more than once (a `Failed` result re-queues the room and the *same* task
for another cleaning pass, so its full inspection history needs its own
records, not one overwritten field).

### Maintenance Request `[Phase 8 -- built]`

Lives in its own `Hotel Maintenance` module, mirroring Housekeeping's own
precedent. `autoname: naming_series:` (`MR-.YYYY.-.#####`). `room`,
`status` (`Open / In Progress / Resolved / Cancelled`), `priority`
(`Low / Normal / High / Urgent`), `description` (required -- what's
broken), `reported_by`/`assigned_to` (Link User), `reported_date`,
`started_at`/`resolved_date` (read-only), `resolution_notes`/
`cancellation_reason`.

`services.maintenance.create_request()` only takes the room out of
rotation (`Room.status = "Maintenance"`) when it's currently vacant
(`Available`/`Dirty`/`Cleaning`/`Clean`) -- an `Occupied`/`Reserved` room
stays exactly as it is, since a guest is still there and the room isn't
actually unsellable; the ticket still tracks the issue either way.
Dedupes against an existing `Open`/`In Progress` request per room, same
pattern as `Housekeeping Task`'s active-task dedupe. `resolve_request()`
sends a `Maintenance` room to `Dirty` plus a new Housekeeping Task
(needs a once-over before resale -- same vacate-and-clean pattern as
checkout/Room Movement); `cancel_request()` (reason required) reverts
straight to `Available` instead, since nothing was actually done to the
room. Phase 4's "Report Maintenance" quick action (still reachable from
an in-progress Housekeeping Task) now also creates one of these behind
the scenes via `services.housekeeping.report_maintenance()` -- see
CHANGELOG.md's Phase 8 entry -- instead of only leaving a note on the
task, as it did from Phase 4 through Phase 7.

## Naming conventions

No submittable DocTypes and no Frappe Workflow through Phase 4 --
lifecycle is a plain `status` Select field, matching `qcore`'s convention.
Master/reference data (Property, Room Type, Hotel Service) is
field-autonamed; transactional data (Guest, Hotel Stay, Hotel Folio,
Reservation, Housekeeping Task) uses a `naming_series:` field with exactly
one series option; Folio Item and Reservation Room (child tables) and Room
Inspection (a standalone doctype, hash-named because a task can be
inspected more than once -- see above) are all hash-named.

## A collision worth remembering

`Room`, `Property`, `Floor`, `Room Type`, `Guest`, `Reservation`/
`Reservation Room` (Phase 2), and `Housekeeping Task`/`Room Inspection`
(Phase 4) are all doctype names this app shares with the
previously-uninstalled `hospitality_pms` app. Checked before finalizing
Phase 4 the same way as every prior phase -- clean, no leftovers. See
ARCHITECTURE.md's "Relationship to `hospitality_pms`" section -- core,
app-agnostic records
(Property Setter above all) can silently outlive an `uninstall-app` and
attach themselves to a same-named doctype in a new app. Checked before
finalizing Phase 2 (`frappe.get_all("Property Setter", filters={"doc_type":
["in", ["Reservation", "Reservation Room"]]})`) -- clean, no leftovers this
time. Keep checking for any doctype name a future phase reuses.
