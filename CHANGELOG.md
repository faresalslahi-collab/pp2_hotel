# Changelog

All notable changes to PP2 Hotel PMS are recorded here, by phase (see the
product brief's own instruction: architecture and schema first, one
deliverable slice per phase, stop for review before continuing).

## Phase 0 -- Bootstrap (2026-08-17)

Not a build phase -- clearing the ground for one. This bench had an earlier,
independently-built hotel PMS app, `hospitality_pms` (v16.4.0, 354 passing
backend tests, full Vue frontend, Night Audit, idempotent financial
posting), covering nearly the same product brief. At the user's explicit
request, confirmed before each destructive step:

- `bench --site mysite.local uninstall-app hospitality_pms` -- dropped its
  tables (37 folios, 4 Night Audits, guest/reservation records, a
  3,217-row integration queue, per its own BUILD_LOG.md, all gone).
- `bench remove-app hospitality_pms` -- archived (not deleted) to
  `archived/apps/hospitality_pms-2026-08-17`.
- `bench new-app pp2_hotel` + `install-app` -- fresh app scaffold.

No backup was taken first (declined explicitly) -- this phase is
unrecoverable by design.

## Phase 1 -- Foundation & Front Desk Dashboard (2026-08-17)

Architecture, design system, layout, nested sidebar, Front Desk Dashboard,
Room Grid and Room Drawer -- the exact slice the product brief's own
section 31 calls out as "build this, then stop for review" before
Reservations/Stay/Folio/Checkout/Housekeeping/Maintenance.

### Added

- Nine DocTypes across six Frappe modules -- Hotel Setup (Property, Floor,
  Room Type), Hotel Rooms (Room), Hotel Guests (Guest), Hotel Front Office
  (Hotel Stay), Hotel Billing (Hotel Folio, Folio Item), Hotel Services
  (Hotel Service). See DATABASE.md for the full schema, including every
  doctype from the brief's section 29 not yet built and which phase it's
  planned for.
- `services/stay.py`: Room-status sync on Hotel Stay lifecycle transitions
  -- see ROOM_STATUS_ENGINE.md.
- `services/dashboard.py`, `services/rooms.py` + thin `api/dashboard.py`,
  `api/rooms.py` wrappers: `get_front_desk_kpis`, `get_room_grid`,
  `get_room_detail`.
- `fixtures/role.json`: the eleven section-17 hotel roles.
- `demo/seed.py`: idempotent local demo data -- one property, 3 floors, 3
  room types, 23 rooms across a believable status mix, 8 guests, matching
  Hotel Stay/Hotel Folio records for occupied/reserved rooms.
- Vue 3 + TypeScript frontend (`frontend/`) on the same stack as this
  bench's `qcore`/`gcc_hr` apps (frappe-ui, Pinia, Vue Router, Tailwind
  with an `app.*` token namespace, lucide icons), served at `/pp2_hotel`:
  full nested/collapsible sidebar (new component work -- `gcc_hr`'s own
  sidebar is flat), Front Desk Dashboard with KPI row + Room Grid, and a
  Room Drawer showing live guest/stay/folio-balance data for
  occupied/reserved rooms. Every other sidebar destination resolves to a
  `ComingSoon` placeholder rather than a dead link.
- `README.md`, `ARCHITECTURE.md`, `DATABASE.md`, `PERMISSIONS.md`,
  `ROOM_STATUS_ENGINE.md` (this app's domain doc, mirroring `qcore`'s
  `COMPLIANCE_ENGINE.md`).

### Known issue hit and fixed during this phase

A leftover `Property Setter` record (`Guest-naming_series-options`, value
`HPMS-GST-.#####`) from the uninstalled `hospitality_pms` app's own `Guest`
doctype silently overrode this app's `Guest.naming_series` options, because
Property Setter is a core, app-agnostic doctype that `uninstall-app` does
not clean up. First symptom: newly-created Guest records named themselves
`HPMS-GST-00059` onward (continuing that app's old counter) instead of
`GST-2026-00001`. Not a Redis-cache issue, despite matching symptoms --
flushing the cache reproduced the same stale value every time because the
*source* the cache was correctly mirroring was itself stale. Fixed by
deleting the Property Setter and reseeding. See ARCHITECTURE.md's
"Relationship to `hospitality_pms`" section for the general hazard this
points at for any future doctype-name reuse.

### Deviations from the product brief (and why)

- Reservation/Reservation Room are documented (DATABASE.md) but not built
  this phase -- the Dashboard/Grid/Drawer only need to read an *existing*
  Hotel Stay, not the booking workflow that would normally produce one.
  Phase 1's demo data creates Hotel Stay records directly as a stand-in.
- Housekeeping/Maintenance/Payment Allocation doctypes are documented but
  not built, per the brief's own section-27 build order (they come after
  Reservations, Checkout).
- `Hotel Folio.tax_rate` defaults to 0, set explicitly per document (demo
  data uses 15) rather than a system-wide Saudi VAT default, per the
  brief's section 18 instruction not to hard-code jurisdiction logic into
  the core.

### Validation

| Check | Result |
|---|---|
| `bench --site mysite.local migrate` | clean |
| Roles fixture sync | all 11 roles present |
| `bench execute pp2_hotel.demo.seed.run` | idempotent, seeds 1 property / 23 rooms / 8 guests / 8 stays / 6 folios |
| API endpoints, via `frappe.call` and again over real authenticated HTTP (login + CSRF) | correct shapes and values both ways |
| Frontend `yarn build` (`vite build` + `vue-tsc --noEmit`) | clean |
| `bench --site mysite.local run-tests --app pp2_hotel` | **blocked bench-wide**, not a pp2_hotel defect -- ERPNext's shared `BootStrapTestData` fails on a pre-existing duplicate `Price List "Standard Buying"` row and aborts before any test runs; reproduced identically running `gcc_hr`'s own tests. `test_dashboard.py`, `test_rooms.py`, `test_hotel_stay.py`, `test_hotel_folio.py` exist and their assertions were verified by hand (`bench console`, rolled back) instead: bad-date rejection, Checked-In-to-Occupied and Checked-Out-to-Dirty room sync, Folio totals recomputed from items (ignoring a deliberately wrong `subtotal`/`total` passed in), balance updates on payment, guest/property fetched from stay -- all as expected. Worth fixing the shared Price List row separately so `bench run-tests` works bench-wide again. |
| Manual browser smoke (headless Chromium via Playwright, real login) | **pass** -- Dashboard KPI row matches seeded data, Room Grid renders all 23 rooms grouped by floor with correct status colors (cross-checked room-by-room against the API response and the live DOM text, not just the screenshot), clicking an occupied room (103) opens the Drawer with real guest/check-in/check-out/balance, clicking an available room (102) shows the "No active stay" empty state, sidebar sections (Front Desk, Reservations) expand independently and show their children. One screenshot showed room 107's number rendering as a stray "1" under its Maintenance badge; the live DOM text and the API both confirmed "107" was correct throughout -- a headless-renderer font/antialiasing artifact in that one PNG capture, not an application bug. No console errors originated from the pp2_hotel app itself (the errors present are pre-existing, unrelated Frappe Desk issues -- a locale bug in `desk.bundle.js` and socket.io 404s from not running the realtime service locally). Verification also required a stub `libasound.so.2` (this sandbox has no audio library and no root to install one) and a temporary `bench serve` process -- neither is part of the app; both were local-only and are torn down after this phase's review.

### Next phase

Reservations (booking workflow, Reservation Calendar, Availability) and
proper check-in orchestration that creates Hotel Stay from a confirmed
Reservation, per the brief's own section-27 order.

## Phase 2 -- Reservations & Check-In (2026-08-18)

The booking -> check-in loop: a Reservation can be created, confirmed,
checked in (creating a real Hotel Stay + Hotel Folio), cancelled, or marked
No Show, and the Front Desk Dashboard/Room Grid/Room Drawer built in
Phase 1 now reflect real bookings instead of directly-seeded Hotel Stays.

### Added

- Two DocTypes in a new `Hotel Reservations` module: **Reservation**
  (naming series, guest/property, status lifecycle, derived arrival/
  departure) and **Reservation Room** (child, room type + optional room +
  dates + rate + `hotel_stay` traceability pointer). See DATABASE.md.
- `services/reservations.py` (create/confirm/cancel/mark_no_show -- cancel
  and no-show both require a non-empty reason), `services/availability.py`
  (room-type availability over a date range via one `frappe.qb` join, no
  double counting), `services/checkin.py` (the only legal way to create a
  Hotel Stay -- see the schema-change note below; refuses a Cancelled/No
  Show/Completed reservation, not just an already-checked-in line),
  `services/front_desk.py`
  (Arrivals/Departures/In-House Guests worklists, cross-doctype joins over
  Reservation Room + Reservation + Hotel Stay + Hotel Folio) + their thin
  `api/*.py` wrappers.
- Frontend: New Reservation, All Reservations, Reservation Detail (a new,
  not-nav-tree-generated route), Availability, and the three Front Desk
  worklist pages (Arrivals with a Check In action, Departures, In-House
  Guests), plus a reusable `CheckInDialog.vue` and `DataTable.vue`.
- Property extended with `default_tax_rate`, used to seed new Hotel
  Folios at check-in.

### Schema changes to Phase 1 doctypes

- **Hotel Stay.status** dropped `Reserved` (`Checked In`/`Checked Out`
  only) -- it was a Phase 1 stand-in for a concept Reservation now owns
  properly. A new `reservation` field (read-only, traceability) was added.
  **Direct creation is now refused** unless `frappe.flags.
  via_checkin_service` is set (mirrors an integrity rule the old
  `hospitality_pms` app enforced the same way) -- `demo/seed.py` and every
  Phase 1 test that inserted a Hotel Stay directly were reworked
  accordingly (see `tests/factories.py:make_checked_in_stay()`).
- `services/stay.py`'s room-status map lost the `Reserved` entry;
  `services/reservations.py` now sets/releases `Room.status = "Reserved"`
  directly. See ROOM_STATUS_ENGINE.md for the full two-writer picture.

### Known issues hit and fixed during this phase

1. **A new Frappe module wasn't picked up by `bench migrate`.** Adding
   `Hotel Reservations` to `modules.txt` and creating its doctype folders
   produced a clean-looking 100% progress bar, but the tables never
   appeared -- `frappe.get_module_list()` read the file correctly, but the
   doctype sync loop (`frappe/model/sync.py:sync_for`) walks
   `frappe.local.app_modules`, a **Redis-cached** app-to-modules map built
   once and not invalidated by editing `modules.txt` on disk. Fixed with
   `frappe.cache.delete_value("app_modules")` (a plain `bench
   --site <site> clear-cache` also clears it -- `app_modules` isn't in
   `hooks.persistent_cache_keys` -- that's the simpler fix for next time:
   run `bench clear-cache` after adding a new module, before `migrate`).
2. **An unset Link field is sometimes SQL `NULL`, sometimes `''`.**
   `services/front_desk.py:get_arrivals_today()`'s join filtered
   `Reservation Room.hotel_stay == ""` to mean "not yet checked in" and
   silently returned nothing -- the field was actually stored as `NULL`.
   Fixed to match `.isnull() | (... == "")`; regression test in
   `api/test_front_desk.py`.
3. Checked `Property Setter`/`Document Naming Rule`/`Custom Field` for
   `Reservation`/`Reservation Room` before finalizing (both names also
   existed in the uninstalled `hospitality_pms` app) -- clean, no
   leftovers this time. See ARCHITECTURE.md.

### Validation

`bench --site mysite.local migrate` clean (after the cache fix above);
`demo/seed.py` reworked to go through `create_reservation` ->
`confirm_reservation` -> `check_in` instead of inserting Hotel Stay
directly, re-seeded cleanly (1 property, 23 rooms, 8 guests, 8
Reservations all Confirmed, 6 Hotel Stays, 6 Folios). `bench run-tests` is
still broken bench-wide (unchanged from Phase 1, not a pp2_hotel defect --
see that entry); every new test file (`test_reservations.py`,
`test_checkin.py`, `test_availability.py`, `test_front_desk.py`, plus the
reworked Phase 1 test files) was instead verified by hand via `bench
console` (rolled back or left uncommitted each time): the direct-creation
guard, confirm/cancel/no-show and their room-status side effects,
walk-in create+immediate-check-in, double-check-in rejection,
wrong-room-type rejection, availability decrementing only for Confirmed
overlapping demand (not Draft, not non-overlapping dates), and all three
front-desk worklists against real seeded data.

Frontend `yarn build` (`vite build` + `vue-tsc --noEmit`) clean. Manual
browser smoke (same stub-`libasound.so.2` + `bench serve` approach as
Phase 1) walked the full loop for real: New Reservation (new-guest path,
room type auto-filling its rate) -> "Create & Confirm" -> Reservation
Detail (Confirmed pill, "Unassigned" room, "Not checked in") -> Check In
dialog (room picker, listbox needed keyboard selection in the Playwright
driver -- click-based selection on this custom listbox was flaky under
Playwright's actionability retries; noted for future browser-driven checks
of this component, not an app defect, confirmed by capturing the actual
`checkin.check_in` network request/response) -> Reservation Detail now
shows "Checked In" for that room -> **Front Desk Dashboard's Room Grid
picked up the change with no reload of its own already open** (room 102
went `Available` -> `Occupied · Zainab Al-Otaibi`, KPIs updated) -> All
Reservations lists it -> Availability shows real per-room-type counts ->
Arrivals correctly excludes the now-checked-in line ("No arrivals today")
-> In-House Guests lists all 7 checked-in stays with real per-guest
balances. The reservation/stay/folio created during this walkthrough were
removed afterward (and room 102 reset to `Available`) so the site matches
the documented seed counts above -- 8 Reservations, 6 Hotel Stays, 6
Folios -- exactly.

### Addendum -- `bench run-tests --app pp2_hotel` now actually works

Both Phase 1 and Phase 2's entries above recorded the same workaround
("verified by hand via `bench console`") for a bench-wide
`DuplicateEntryError` on `Price List "Standard Buying"` that aborted the
test runner before any test ran. Root-caused properly this time instead of
worked around again: Frappe's test-record dependency walker
(`frappe/tests/utils/generators.py:get_missing_records_doctypes`) recurses
through every Link field on a doctype under test, including ones no
individual test actually populates. `Guest.customer` (-> ERPNext Customer)
and `Property.company` (-> ERPNext Company) both lead there, and importing
*either* ERPNext doctype's own `test_*.py` module triggers
`erpnext.tests.utils.ERPNextTestSuite`'s module-level `BootStrapTestData()`
side effect, which unconditionally inserts default Price Lists -- fine on
a fresh, dedicated test site, fatal on this bench's actual dev site where
a Company (and its Price Lists) already legitimately exist.

Fix: `IGNORE_TEST_RECORD_DEPENDENCIES = ["Customer"]` /
`["Company"]` in new `test_guest.py` / `test_property.py` files -- Frappe's
own supported mechanism for exactly this, no ERPNext core code touched, no
second site needed. Both files also gained real tests (Guest naming
series, mandatory `guest_name`, the `customer` link still works when
populated directly rather than through Frappe's auto-generation; Property
code uppercasing, uniqueness) rather than existing solely to carry the
ignore list.

Fixing this also caught two real, previously-invisible bugs, both fixed
alongside it:

1. **`Property.property_code` uppercasing never actually took effect.**
   `validate()` ran too late -- Frappe's `_sync_autoname_field()` (which
   keeps a `field:X`-autonamed doctype's field mirrored to `name`) runs
   *after* `validate()` and silently overwrote the uppercased value back
   to whatever was typed. Moved the normalization to `before_naming()`,
   which runs before `name` is captured. Worth checking any other
   `field:`-autonamed doctype for the same mistake before writing one.
2. `tests/factories.py:make_property()` hardcoded `property_name = "Test
   Property"` regardless of the `code` argument -- harmless until a test
   legitimately created two properties with different codes in the same
   test (`Property.property_name` is unique), which then failed with an
   unrelated-looking `UniqueValidationError`. Now derives the name from
   the code.

`bench run-tests --app pp2_hotel`: **37 tests, all passing.** Demo data
confirmed untouched afterward (`FrappeTestCase` rolls back). The
underlying ERPNext test-bootstrap fragility is unchanged for other apps in
this bench (`qcore`, `gcc_hr`) -- fixing it there would need the same
`IGNORE_TEST_RECORD_DEPENDENCIES` treatment on whichever of their doctypes
link to Company/Customer/other ERPNext masters, out of scope here since
those aren't pp2_hotel's files.

## Phase 3 -- Payments & Checkout

Closes the core guest lifecycle loop for the first time: Reservation →
Stay → Folio charges → Payment → Checkout. The Room Drawer has shipped
four permanently-disabled action buttons since Phase 1 (Check-out, Add
Charge, Payment, View Folio) with a "Coming soon" tooltip -- all four are
real now. `Move Room` and `Guest Profile` stay disabled; they're later
phases (Room Movement, Guest Profile).

### Added

- **Folio Payment** (new child table, Hotel Billing module): `posting_date`,
  `amount`, `payment_method` (`Cash / Card / Bank Transfer / Online /
  Other`), optional `reference`/`notes`. `Hotel Folio.paid_amount` is now
  the sum of this table (`paid_amount` changed from directly editable to
  `read_only: 1`), the same way `subtotal` is the sum of `items`. See
  DATABASE.md for why this -- not a category-splitting "Payment
  Allocation" screen -- is the right-sized version of the brief's section
  14 for what Folio can actually support today.
- `Hotel Folio.checkout_override_reason` (Small Text, read-only) -- set
  only when checkout closes a folio with an outstanding balance under an
  authorized override.
- `services/folio.py`: `add_charge`/`add_payment` (append a child row,
  save, refuse a `Closed` folio; `add_payment` also rejects a zero/negative
  amount) and `get_folio_detail` (guest name, room number, stay dates,
  itemized items/payments -- the read-side for the new Folio Detail page).
- `services/checkout.py`: `check_out(stay, override_reason=None)` --
  refuses a stay that isn't `Checked In`; blocks a positive balance unless
  `override_reason` is given *and* the caller holds `System Manager /
  Hotel Administrator / Hotel Manager / Front Desk Manager`
  (`OVERRIDE_ROLES`); a zero or negative balance (overpayment) always
  succeeds with no reason needed. On success: Folio → `Closed`, Hotel Stay
  → `Checked Out` (the existing `services.stay.sync_room_status` already
  turns the room `Dirty` from that transition -- no change needed there).
  See PERMISSIONS.md for how this authority check differs from an
  ordinary DocType permission.
- `api/folio.py`, `api/checkout.py` -- thin wrappers, same shape as every
  prior phase.
- Frontend: `AddChargeDialog`, `AddPaymentDialog`, `CheckoutDialog`
  (reused from both the Room Drawer and the new Folio Detail page) and
  `pages/billing/FolioDetail.vue` (`/billing/folios/:folio`, a new
  not-nav-tree-generated route, same pattern as `/reservations/:name`).

### Schema changes to Phase 1 doctypes

- `Hotel Folio.paid_amount`: editable → computed/`read_only`. Every place
  that used to set it directly (`test_hotel_folio.py`, `api/test_rooms.py`,
  `demo/seed.py`) now appends a `Folio Payment` row instead.

### Verification

`bench --site mysite.local migrate` clean. `bench run-tests --app
pp2_hotel` -- now a real, working command since this phase's earlier
addendum -- **48 tests, all passing** (11 new: `test_folio.py`,
`test_checkout.py`, plus the Phase 1 folio/room tests reworked for the
payments-table change). Demo data wiped and reseeded under the new schema
(1 property, 23 rooms, 8 reservations, 6 stays, 6 folios -- unchanged
counts, now with real `Folio Payment` rows instead of a bare
`paid_amount`).

Frontend `yarn build` clean. Manual browser smoke walked the whole loop on
a real occupied room (105, balance SAR 123 from the seed): Add Charge
(+SAR 50 "Extra Towels", balance correctly became SAR 180.5 with the 15%
tax applied) -> Add Payment (-SAR 100 Cash, balance SAR 80.5) -> both
updated live in the Room Drawer with a success toast each, no reload
needed -> View Folio navigated to `/billing/folios/FOL-2026-00006` showing
every charge/payment itemized exactly as entered, matching the brief's
section-12 mockup shape -> Check-out with the SAR 80.5 balance still
outstanding correctly showed the amber override panel (blocked without a
reason, blocked for a role outside `OVERRIDE_ROLES` even with one) ->
submitted as Administrator with a reason -> folio flipped to `Closed` with
the reason visibly displayed in an audit banner on the page (not hidden),
every folio action button correctly disabled afterward -> Dashboard's Room
Grid and KPI row updated with no manual refresh (room 105: `Occupied` ->
`Dirty`; Occupied 6->5, Dirty 3->4, In-House Guests 8->7). The extra
charge/payment/checkout created during this walkthrough were reverted by
hand afterward (folio reopened, items/payments trimmed back, stay/room
reset) so the site matches the documented seed numbers above exactly, same
housekeeping discipline as Phases 1-2's own browser-smoke entries.

## Phase 4 -- Housekeeping

A `Dirty` room has stayed `Dirty` forever since Phase 1 -- `Clean` and
`Inspected` have existed as `Room.status` options with no writer since the
very first migration. This phase gives them one, closes the loop
(`Dirty -> Cleaning -> Clean -> Inspected -> Available`), and -- since it's
the third service to write `Room.status` -- centralizes every room-status
write behind a single function, exactly as `ROOM_STATUS_ENGINE.md` said it
would once that moment arrived.

### Added

- **Housekeeping Task** and **Room Inspection** (new `Hotel Housekeeping`
  module). A task is created automatically by `services.checkout.
  check_out()` the instant a room goes `Dirty` -- no manual "create task"
  step -- and `services.housekeeping.create_task()` dedupes against an
  existing active task so it's safe to call defensively. Room Inspection
  is its own doctype (not a field on the task) because a task can be
  inspected, fail, and be inspected again -- each attempt is its own
  record. See DATABASE.md.
- `Room.status` gained `Cleaning`, between `Dirty` and `Clean` -- the
  brief's own Front Desk Dashboard mockup shows a room in exactly this
  state.
- **`services/room_status.py`**: `set_room_status(room, new_status,
  reason=None)`, now the single writer of `Room.status`.
  `services/stay.py` and `services/reservations.py` were refactored to
  call it instead of `frappe.db.set_value` directly -- a shape change to
  existing logic, not a behavior change; all of Phases 1-3's tests for
  those writers pass unmodified.
- **`services/housekeeping.py`**: `create_task`, `start_cleaning`
  (Pending -> In Progress, room -> Cleaning), `mark_clean` (In Progress ->
  Completed, room -> Clean), `inspect` (Passed: task -> Inspected, room ->
  Available; Failed: task re-queued to Pending with timestamps cleared,
  room back to Dirty), `report_maintenance` (room -> Maintenance, appends
  to the task's notes, task's own status untouched -- blocked, not
  discarded), and `get_housekeeping_board` (active-task worklist, with a
  documented safety net for a room that somehow ends up needing attention
  with no task at all).
- `api/housekeeping.py` -- thin wrappers, same shape as every prior phase.
- Frontend: Housekeeping Dashboard (the brief's section-15 worklist, one
  action per row matching the task's current stage), Cleaning Tasks and
  Room Inspection list pages (full history, unlike the Dashboard's
  active-only board), `InspectDialog`/`ReportMaintenanceDialog`, and a new
  `Cleaning` status token throughout (`StatusBadge`, Room Grid, Room
  Drawer all pick it up for free via the existing token system).
- `demo/seed.py` now runs the seeded `Dirty` rooms through
  `services.housekeeping.create_task()` too, so the Housekeeping Dashboard
  has believable starting data instead of relying solely on the orphan
  safety net above.

### Deviations from the product brief (and why)

- "Report Maintenance" does not create a Maintenance Request -- there's no
  such doctype yet. It does the operationally important part today (takes
  the room out of rotation, records why) without a full ticket lifecycle
  that deserves its own phase. See DATABASE.md's "Maintenance Request"
  entry.

### Known issues hit and fixed during this phase

1. **`FrappeTestCase` only rolls back the database once, at class
   teardown -- not between individual test methods.**
   `test_housekeeping.py`'s first draft shared one room across all its
   test methods (via `setUp()`, the pattern every prior test file in this
   app uses) and intermittently saw 2 `Room Inspection` rows where it
   expected 1: an earlier method in the same class had left its task in a
   state the next method's `create_task()` call happily reused, since
   methods in one `FrappeTestCase` class share a single uncommitted
   transaction. Fixed by giving each test method its own uniquely-numbered
   room instead of reusing one from `setUp()`. Audited every other test
   file in the app for the same exact-count-assertion pattern -- none were
   exposed, only this new file was. Documented as a house rule going
   forward: never assert an exact count against a fixture shared across
   test methods in the same class.
2. **`get_housekeeping_board()` kept showing a room after it was reported
   for maintenance.** Caught during browser testing, not by any backend
   test: `report_maintenance()` deliberately leaves the task's own status
   unchanged (`In Progress` stays `In Progress`, on purpose -- see
   DATABASE.md), so the board kept listing the room with "Mark Clean"/
   "Report Maintenance" buttons still active even though the room itself
   had already moved to `Maintenance` and was no longer housekeeping's to
   act on. Fixed by having `get_housekeeping_board()` check each room's
   *actual current status* (not just its task's status) and only surface
   rows still in `Dirty`/`Cleaning`/`Clean` -- a task can now legitimately
   sit at `In Progress` "forever" (until Maintenance hands the room back,
   presumably `Dirty` again for a fresh clean) without cluttering the
   active board. `test_room_reported_for_maintenance_drops_off_the_board`
   added.

### Verification

`bench --site mysite.local migrate` clean (module cache cleared with
`bench clear-cache` *before* migrating this time, per the Phase 2
addendum -- no repeat of that bug). `Property Setter`/`Document Naming
Rule`/`Custom Field` checked clean for `Housekeeping Task`/`Room
Inspection` (both names also existed in `hospitality_pms`). `bench
run-tests --app pp2_hotel`: **56 tests, all passing** (8 new in
`test_housekeeping.py`, 1 new in `test_checkout.py` for the auto-created
task). Demo data wiped and reseeded (1 property, 23 rooms, 8 reservations,
6 stays, 6 folios, 3 housekeeping tasks matching the 3 seeded `Dirty`
rooms -- unchanged counts elsewhere, new for this phase).

Frontend `yarn build` clean. Manual browser smoke walked the full cycle on
real seeded data: Start Cleaning (room 302 `Dirty` -> `Cleaning`) -> Mark
Clean (-> `Clean`) -> Inspect and fail it on purpose ("Bathroom mirror
still has streaks.") -- a distinct warning toast ("Inspection failed --
room sent back to Dirty and re-queued.") and the room correctly reappeared
at the top of the board as `Dirty` with `Start Cleaning` available again,
*same task*, not a duplicate -> ran it through again and passed the
inspection this time -> room dropped off the active board entirely and
showed `Available` on the Front Desk Dashboard (KPIs updated live:
Available 10->11, Dirty 3->2, no manual refresh). Report Maintenance on a
second room (304) surfaced the bug described above, which was fixed and
re-verified live in the same session (room correctly disappeared from the
board after the fix, leaving only the untouched third seeded room). All
test data (inspections, task states, room statuses) reverted by hand
afterward so the site matches the documented seed numbers exactly, same
housekeeping discipline as every prior phase's browser-smoke entry.

## Phase 5 -- Reports

Step 13 of the brief's own section-27 build order. Unlike every phase so
far, this one adds no new transactional workflow and no new schema --
it's a pure read-side aggregation layer over data every prior phase
already produces (Room, Hotel Stay, Hotel Folio/Folio Item/Folio Payment,
Housekeeping Task/Room Inspection).

### Added

- **`services/reports.py`**: `get_occupancy_revenue_report` (per-day
  occupied-room count over total sellable rooms excluding `Out of Order`,
  room vs. other revenue split using the existing `Folio Item.
  hotel_service` unset/set signal, ADR, RevPAR, plus a daily breakdown),
  `get_guest_ledger`, `get_outstanding_balances` (deliberately including
  `Closed` folios with a balance -- exactly what a Phase 3 checkout
  override produces, and real accounts-receivable a hotel needs to see,
  not something checkout should have hidden by closing the folio),
  `get_payment_report` (payment list + totals-by-method), and
  `get_housekeeping_report` (task counts, inspection pass rate, average
  turnaround from a task's creation to the inspection that passed it).
- `api/reports.py` -- five thin wrappers, same shape as every prior
  phase.
- Frontend: `OccupancyRevenueReport.vue` (routed from all four of
  `/reports/occupancy`, `/revenue`, `/adr`, `/revpar` -- one combined
  report, not four near-empty pages, since RevPAR = ADR x Occupancy% and
  real PMS reporting screens present them together), `GuestLedger.vue`,
  `OutstandingBalances.vue`, `PaymentReport.vue`, `HousekeepingReport.vue`.
  All reuse `DataTable.vue` and the Dashboard's KPI-tile pattern -- no new
  shared components needed.

### Known issues hit and fixed during this phase

1. **`FrappeTestCase`'s class-only-rollback gotcha (see Phase 4) struck
   again, in a new shape.** `test_reports.py`'s `TestOccupancyRevenueReport`
   and `TestPaymentReport` each had two test methods sharing one Property
   via `setUp()` and then asserting an aggregate (`total_rooms`,
   `report["total"]`) scoped to "the" property -- exactly the pattern the
   Phase 4 house rule warns about, just one level removed (a *report*
   assertion over shared fixtures, not a *record-count* assertion). Fixed
   the same way: each test method now creates its own uniquely-coded
   Property instead of sharing one from `setUp()`. `TestGuestLedgerAnd
   OutstandingBalances` and `TestHousekeepingReport` were audited and
   found safe (the former scopes every assertion to a specific folio name,
   the latter has only one test method).

### Verification

`bench --site mysite.local run-tests --app pp2_hotel`: **64 tests, all
passing** (8 new in `test_reports.py`). No migration needed -- no schema
change this phase.

Frontend `yarn build` clean (vite build + `vue-tsc --noEmit` both pass).
Manual browser smoke opened all eight Reports nav destinations against
real seeded demo data: Occupancy/Revenue/ADR/RevPAR all render identically
from the same `OccupancyRevenueReport.vue` (9.1% occupancy, SAR 306.25
ADR, SAR 27.84 RevPAR, SAR 5,185 total revenue for the default 7-day
window -- confirmed against the same numbers `bench console` produced
while building the backend); Guest Ledger and Outstanding Balances match
the seeded folios exactly (6 open folios with balances, Outstanding
Balances showing the same 6 since none are Closed-with-a-balance in the
current seed); Payment Report's SAR 3,647.5 total matches the sum of the
seeded `Folio Payment` rows across 4 payment methods; Housekeeping Report
shows 3 total tasks / 0 completed / 0% pass rate, matching the untouched
Phase 4 seed state (3 `Dirty` rooms, no cleaning cycle run since). No test
data was created during this pass (read-only report pages), so no cleanup
was required -- the first phase where browser verification didn't need a
teardown step.

## Phase 6 -- Room Movement & Rate Plan

Two items from ARCHITECTURE.md's "Build phases" list, shipped together
because they need each other: Room Movement (brief section 11 --
room-to-room transfer with a financial-impact summary) can move a guest
into a *different* Room Type, and pricing that move correctly needs Rate
Plan's date-range-aware rate lookup, not just a flat `base_rate`. Rate
Plan itself was deferred since Phase 1's DATABASE.md for exactly this
reason -- no consumer existed until now.

### Added

- **Rate Plan** (new doctype, `Hotel Setup` module). Per Room Type,
  date-range-aware pricing; `validate()` rejects an end date before the
  start date and any date range overlapping another *Active* Rate Plan
  for the same Room Type, so `services.rate_plan.get_effective_rate()`
  always resolves to at most one match (falling back to `Room
  Type.base_rate` otherwise). No dedicated Vue screen this phase --
  Desk-managed config, same as Property/Floor/Room Type today; its own
  screen is deferred to a later "Configuration UI" phase. Wired into
  `services.reservations.create_reservation()` (rate now defaults from
  the room line's `arrival` date through a Rate Plan, not straight from
  `base_rate`) and into Room Movement below -- both one-line swaps of an
  existing lookup, not new logic at either call site.
- **Room Movement** (new doctype, `Hotel Front Office` module -- a Hotel
  Stay lifecycle event, not its own module). `services.room_movement.
  move_room(hotel_stay, to_room, reason=None)` mirrors `services.
  checkout.check_out()`'s vacate-room pattern exactly: the destination
  room goes `Occupied` for free through the existing Hotel Stay
  `on_update()` -> `sync_room_status()` path (it doesn't know or care
  whether `stay.room` changed via check-in or a mid-stay move), and the
  vacated room goes `Dirty` plus gets a Housekeeping Task, identical to
  what a checkout already does when a guest departs. Guards: only a
  `Checked In` stay can move; the destination must be `Available` and in
  the same property; a destination Room Type's `max_occupancy` (if set)
  can't be exceeded by the stay's current adults+children. Deliberately
  does not touch already-posted Folio Items -- this app has no automatic
  nightly-room-charge job, so a move only changes `Hotel Stay.rate` going
  forward, informational for whatever gets charged next rather than a
  retroactive proration engine the brief doesn't ask for. See
  ROOM_STATUS_ENGINE.md's new "Room Movement" section for the full
  writer-by-writer picture.
- `api/room_movement.py` -- one thin wrapper, same shape as every prior
  phase.
- Frontend: `RoomDrawer.vue`'s "Move Room" button -- disabled with a
  "Coming soon" tooltip since Phase 1 -- is real now, the last of the
  original six action buttons to get a backing flow (only "Guest
  Profile" remains a stub). New `MoveRoomDialog.vue` (destination room
  picker scoped to `Available` rooms in the same property, not filtered
  to the same Room Type -- an upgrade/downgrade is the point) and
  `pages/rooms/RoomMovementHistory.vue` (`/rooms/movement`, plain
  history list, same shape as `CleaningTasks.vue`/`RoomInspections.vue`).

### Verification

`bench --site mysite.local migrate` clean. `Property Setter`/`Document
Naming Rule`/`Custom Field` checked clean for `Rate Plan`/`Room Movement`
(both names also existed in `hospitality_pms`). `bench --site
mysite.local run-tests --app pp2_hotel`: **79 tests, all passing** (7 new
in `test_rate_plan.py`, 1 new in `api/test_reservations.py`, 7 new in
`api/test_room_movement.py`) -- every new test method builds its own
uniquely-coded Property per the house rule from Phases 4/5, since both
Rate Plan's overlap validation and Room Movement's room-status side
effects are exactly the kind of state a shared `setUp()` fixture would
leak between methods.

Frontend `yarn build` clean (took ~5 minutes this run instead of the
usual ~40s, purely from CPU contention with `bench start`'s own esbuild
watcher -- not a bug, confirmed by watching actual CPU time rather than
assuming a hang). Manual browser smoke: created a temporary Rate Plan
(Deluxe Room, SAR 650, covering today) via `bench console`, opened room
104's drawer (an Occupied Standard Room, guest Nora Al-Farsi, rate SAR
350), confirmed "Move Room" -- disabled since Phase 1 -- is enabled now,
moved her into room 201 (an Available Deluxe Room). The success toast
and Room Movement history both showed the real recalculated rate (SAR
350 -> SAR 650, +SAR 300); room 104 dropped to `Dirty` with a new
Housekeeping Task on the Housekeeping Dashboard; room 201 showed
`Occupied` with Nora Al-Farsi on the Front Desk Dashboard, with no manual
refresh needed. One real finding from this pass, not from any backend
test:

**frappe-ui's `FormControl type="select"` renders a Headless-UI-style
Listbox, not a native `<select>`.** Playwright's synthetic click on the
`<li role="option">` timed out (same category of issue documented during
Phase 2 verification), and a raw DOM `.click()` dispatched via
`page.evaluate()` didn't register in Vue's state either -- the dropdown
stayed open on "Select a room…" both times. This is a test-harness
finding, not an application bug: fixed by using the listbox's built-in
ARIA typeahead (typing "201" while it's open jumps to the matching
option) instead of clicking or counting arrow-key presses. Documented
here because the same custom-listbox pattern will recur in any future
phase that adds another select-type dialog field.

All test data (the Room Movement record, the auto-created Housekeeping
Task, the temporary Rate Plan, the stay's room/rate, both rooms' status)
reverted by hand afterward -- confirmed the room-status histogram matches
the documented seed exactly (10 Available / 2 Reserved / 6 Occupied / 3
Dirty / 1 Maintenance / 1 Out of Order across 23 rooms) and only the 3
original seeded Housekeeping Tasks remain. `bench run-tests --app
pp2_hotel` re-confirmed green (79/79) after cleanup.

## Phase 7 -- ERPNext Sales Invoice Generation at Checkout

The first phase to actually exercise this app's own stated architecture
(README.md: "ERPNext remains the financial and enterprise system of
record") -- every phase so far built pp2_hotel's own operational
doctypes and left ERPNext untouched. Checkout already closes a Hotel
Folio; this phase makes that moment also produce a real ERPNext Sales
Invoice.

### Fixed

**The demo Property's `company` field had been silently auto-filled from
a stray, unrelated site-wide global default**, not ever set by
`demo/seed.py`. Root cause: Frappe applies `frappe.defaults.
get_global_default(fieldname)` to any Link field literally named
`company` when left unset -- even via a raw `frappe.get_doc({...}).
insert()`, not just Desk forms -- and this bench's global default
Company (`"glob (Demo)"`, cross-app test data unrelated to pp2_hotel)
silently filled it in at Property-insert time. Fixed by creating a
dedicated `PP2 Demo Hotel` Company (SAR, matching every figure already
verified across 6 phases), pointing the demo Property at it explicitly,
and having `demo/seed.py` set `company` going forward instead of leaving
it to chance. Also caught the same gotcha live inside a new test
(`test_generate_invoice_requires_a_configured_company` needed to force
`company` back to empty after insert to actually exercise the
"no company configured" path) -- documented in
[[project_bench_environment]] since it'll bite any future doctype in
this bench with a field named `company`, `currency`, or similar.

### Added

- **`services/invoicing.py`**: `get_or_create_customer_for_guest()` --
  respects `Guest.customer` if already set (the corporate-billing
  override DATABASE.md has documented since Phase 1), otherwise
  auto-provisions an Individual ERPNext Customer named after the guest
  and persists it back so a returning guest always bills to the same
  Customer. `generate_invoice(folio)` -- builds a real Sales Invoice
  with **no `item_code`** (confirmed live against this bench's ERPNext
  that `Sales Invoice Item` only requires `item_name`/`uom`/
  `conversion_factor`/`rate`/`income_account`/`cost_center`, not a real
  Item link -- one row per Folio Item, plus one tax row when the folio's
  flat `tax_rate` is positive), left as **Draft, not auto-submitted**
  (a first cut at this integration is far more expensive to correct if
  submitted -- an accountant reviews and submits it in ERPNext Desk).
  Idempotent (a second call returns the existing invoice, no duplicate);
  returns `None` for a Closed folio with zero charges; throws for a
  still-Open folio, a Property with no Company configured, or a
  folio/company currency mismatch.
- **`services/checkout.py::check_out()`** now calls `generate_invoice()`
  as its last step, wrapped in `try/except` -- a Company/accounts
  misconfiguration must never block a front desk agent from physically
  checking a guest out. The result gains `invoice`/`invoice_error`
  instead of the call ever raising on an invoicing failure.
- `Hotel Folio.sales_invoice` (new field, Link -> Sales Invoice,
  read-only) and `api/invoicing.py::generate_invoice` (thin wrapper, for
  a manual retry from Folio Detail when auto-generation failed).
- Frontend: Folio Detail shows the invoice reference (or "Not yet
  invoiced" with a "Generate Invoice" retry button once Closed); a
  distinct non-blocking warning toast, instead of a plain success one,
  when checkout succeeded but invoicing failed.

### Verification

`bench --site mysite.local migrate` clean (new field, no new doctype/
module). `bench run-tests --app pp2_hotel`: **87 tests, all passing** (7
new in `test_invoicing.py`, 1 new in `test_checkout.py`). Hit the
now-familiar `IGNORE_TEST_RECORD_DEPENDENCIES` gotcha a third time --
`Hotel Folio`'s new `sales_invoice` Link field pulled `Sales Invoice`
into the test-dependency walk, chaining into ERPNext's
`ERPNextTestSuite` bootstrap the same way `Guest.customer`/
`Property.company` did in Phase 1 -- fixed the same way, one line in
`test_hotel_folio.py`.

Frontend `yarn build` clean. Manual browser smoke: settled room 208's
outstanding SAR 174 balance via Record Payment, checked the guest out
normally (no override needed), and confirmed a real Draft Sales Invoice
(`ACC-SINV-2026-00019`) was created against a real auto-provisioned
Customer ("Sara Abdullah") with the exact right line items (two SAR 550
room charges, one SAR 60 Laundry charge) and tax (SAR 174, 15%) totaling
SAR 1,334 -- matching the folio exactly. Folio Detail correctly showed
the invoice reference and hid the "Generate Invoice" button once
invoiced. All test data reverted afterward: the Sales Invoice, the
auto-created Customer, the payment, the stay/room status, and -- caught
only on the post-cleanup room-status/task recount -- two Housekeeping
Tasks orphaned by an earlier manual verification pass whose test
Properties had already been deleted without deleting their tasks first.
Room-status histogram and the 3 seeded Housekeeping Tasks confirmed
matching the documented seed exactly afterward; `bench run-tests --app
pp2_hotel` re-confirmed green (87/87).

## Phase 8 -- Maintenance Requests

Phase 4's "Report Maintenance" quick action was documented from day one
as deliberately minimal -- "no ticket, just takes the room out of
rotation" -- because there was no Maintenance Request doctype yet.
DATABASE.md's own entry said this "deserves its own phase." This is also
the first real work for Maintenance Manager/Maintenance Staff, two of
the section-17 roles that had nothing to operate since Phase 1.

### Added

- **Maintenance Request** (new doctype, new `Hotel Maintenance` module,
  mirroring Housekeeping's own precedent). `naming_series`
  (`MR-.YYYY.-.#####`), `room`, `status` (`Open / In Progress / Resolved
  / Cancelled`), `priority` (`Low / Normal / High / Urgent`),
  `description`, `reported_by`/`assigned_to`, `reported_date`,
  `started_at`/`resolved_date`, `resolution_notes`/`cancellation_reason`.
- **`services/maintenance.py`**: `create_request()` dedupes against an
  existing active request per room (same pattern as `housekeeping.
  create_task`) and only takes the room out of rotation
  (`Room.status = "Maintenance"`) when it's currently vacant
  (`Available`/`Dirty`/`Cleaning`/`Clean`) -- an `Occupied`/`Reserved`
  room stays exactly as it is, since a guest is still there and the room
  isn't actually unsellable, but the ticket still tracks the issue
  either way. `resolve_request()` sends a `Maintenance` room to `Dirty`
  plus a new Housekeeping Task -- the same vacate-and-clean pattern
  checkout/Room Movement already established -- since it needs a
  once-over before resale. `cancel_request()` (reason required, same
  convention as `cancel_reservation`/`mark_no_show`) reverts straight to
  `Available` instead, since a mistaken report means nothing was
  actually done to the room. `Out of Order` remains untouched and
  unwritten by this phase, deliberately -- the separate, longer-term,
  Desk-only status DATABASE.md/ROOM_STATUS_ENGINE.md have documented
  since Phase 1, distinct from `Maintenance`'s active-repair lifecycle.
- **`services/housekeeping.py::report_maintenance()`** -- purely
  additive upgrade, not a breaking change: keeps its existing signature
  and behavior (still appends the note to the task, still leaves the
  task's own status untouched) and now also creates a real Maintenance
  Request, so reporting from the Housekeeping Dashboard produces a
  queryable ticket instead of only a buried freeform note.
- `api/maintenance.py` -- five thin wrappers, same shape as every prior
  phase.
- Frontend: `RoomDrawer.vue` gains a 7th action button, "Report Issue"
  -- enabled for *any* room regardless of occupancy (Guest Profile is
  now the only permanently-disabled stub left), opening the new
  `ReportIssueDialog.vue`. `MaintenanceDashboard.vue` (`/maintenance`,
  active-tickets board with Start Work/Resolve/Cancel per row, the
  latter two reusing `ReasonPromptDialog.vue` from Phase 2 -- extended
  with an optional `label` prop so "Resolution Notes" reads better than
  the generic "Reason" it was written for), `MaintenanceRequests.vue`
  (`/maintenance/requests`, full history -- this *is* the history view,
  so `/maintenance/history` stays `ComingSoon` rather than shipping a
  near-duplicate second list, same precedent as two of Housekeeping's
  five stubbed routes staying unbuilt in Phase 4), `OutOfOrderRooms.vue`
  (`/maintenance/out-of-order`, read-only).

### Verification

`bench --site mysite.local clear-cache` (new module) then `migrate`
clean. `Property Setter`/`Document Naming Rule` checked clean for
`Maintenance Request` (also existed in `hospitality_pms`). `bench
run-tests --app pp2_hotel`: **99 tests, all passing** (11 new in
`test_maintenance.py`, 1 new in `test_housekeeping.py`) -- green on the
first full run, no `FrappeTestCase`/`IGNORE_TEST_RECORD_DEPENDENCIES`
gotcha this time (every new test method already followed the established
house rules from the start).

Frontend `yarn build` clean (one real TypeScript catch: `DataTable`'s
slot rows are typed `Record<string, any>`, not the page's own
`MaintenanceBoardRow` interface -- `MaintenanceDashboard.vue`'s row
handlers needed the looser type, same as `HousekeepingDashboard.vue`'s
already do). Manual browser smoke exercised all four branches: reported
an issue on Occupied room 104 (stayed Occupied, ticket appeared on the
Maintenance Dashboard) then resolved it (still Occupied afterward --
nothing to revert, since it was never taken out of rotation); reported
one on Available room 101 (flipped to `Maintenance`) then cancelled it
(reverted straight back to `Available`, no task); reported one on
Available room 103 then resolved it (`Maintenance -> Dirty`, a new
Housekeeping Task appeared on the Housekeeping Dashboard, ticket left
the active Maintenance board). `/maintenance/requests` showed full
history including the resolved/cancelled ones; `/maintenance/out-of-order`
correctly listed the one seeded Out of Order room -- except its "Floor"
column showed Floor's raw hash-autonamed Link value (e.g. `s22j96do5g`),
meaningless to a human. Real bug, fixed by dropping that column rather
than adding a linked-field-display fetch pattern no other page in this
app uses. One test-harness-only finding, not an app bug: both
`RoomDrawer.vue`'s own `<aside>` and `ReportIssueDialog.vue`'s modal
carry `role="dialog"`, so a Playwright selector scoped to `[role="dialog"]
button:has-text(...)` matches both and needs `.last()` to hit the actual
modal's button. All test data reverted afterward; room-status histogram
and Housekeeping Task count confirmed matching the documented seed
exactly, and `bench run-tests --app pp2_hotel` re-confirmed green
(99/99) after the `OutOfOrderRooms.vue` fix.

## Phase 9 -- Guest Services (Room Service / Laundry / Minibar)

DATABASE.md's `Hotel Service` entry has said since Phase 1: "Room-
service/laundry/minibar order workflows (brief section 14) are
later-phase UI on top of this same master." The rate card and the
billing mechanism (`services.folio.add_charge`, `AddChargeDialog.vue`'s
optional Hotel Service picker) already existed -- this phase adds the
operational order-taking step in between: a guest calls down for
something, staff need to see it as a pending order before it's ever
billed, then mark it delivered.

### Added

- **Service Order** (new doctype, in the existing `Hotel Services`
  module -- one new doctype doesn't earn its own module, same restraint
  Room Movement showed landing in `Hotel Front Office` in Phase 6).
  `folio`, `room` (denormalized from the folio's stay), `status`
  (`Pending / Delivered / Cancelled`), `service_type`, optional
  `hotel_service` link, `description`, `qty`, `rate`, `amount`
  (read-only, `rate x qty`), `ordered_by`/`ordered_at`, `delivered_at`,
  `cancellation_reason`.
- **`services/service_orders.py`**: `create_order()` defaults
  description/rate/service_type from a Hotel Service when one's picked
  (still overridable), throws unless the target folio is `Open`.
  **`deliver_order()` is the only thing that ever calls `add_charge()`**
  -- the bill posts at delivery, not at order time, so `cancel_order()`
  (reason required, same convention as `cancel_reservation`/
  `mark_no_show`/`cancel_request`) leaves the folio completely untouched.
  `deliver_order()` throws a clear error if the folio closed (checkout
  happened) before the order could be delivered -- cancel it instead.
  `get_service_board()` -- active (`Pending`) orders, optional
  `service_type` filter, same shape as `get_housekeeping_board`/
  `get_maintenance_board`.
- `api/service_orders.py` -- four thin wrappers, same shape as every
  prior phase.
- Frontend: `RoomDrawer.vue`'s 8th and final action button, "Order
  Service" -- gated the same way as Add Charge/Payment (needs an Open
  folio). New `OrderServiceDialog.vue` (same Hotel-Service-picker-or-
  manual-entry pattern as `AddChargeDialog.vue`, but creates a Pending
  order instead of an instant charge) and `ServiceOrders.vue` (one
  component serving `/services`, `/services/room-service`, `/services/
  laundry`, `/services/minibar` -- determines its own category filter
  from the route path rather than a route-level prop, since the router's
  shared `PHASE#_ROUTES` maps are component-factories-only). `/services/
  other-charges` stays `ComingSoon` -- redundant with `AddChargeDialog`'s
  existing free-text path, no distinct workflow to build there.
- **Deliberately untouched**: `AddChargeDialog.vue`/`services.folio.
  add_charge()` -- an instant, no-delivery-step charge (a flat fee, a
  damage charge) is a genuinely different, still-valid need from a guest
  service order, not something this phase folds in or replaces.

### Verification

`bench --site mysite.local migrate` clean (new doctype, existing module
-- no `clear-cache` needed). `Property Setter`/`Document Naming Rule`
checked clean for `Service Order`. `bench run-tests --app pp2_hotel`:
**107 tests, all passing** (8 new in `test_service_orders.py`) -- green
on the first full run.

Frontend `yarn build` clean. Manual browser smoke: ordered a Hotel
Service on an occupied room from its Room Drawer, confirmed it appeared
as `Pending` on both `/services` and its category-filtered route,
delivered it and confirmed a real Folio Item appeared on that folio with
the exact right amount (rate x qty) and the order dropped off the active
board; separately ordered and cancelled another one and confirmed no
Folio Item was ever posted for it. All test data reverted afterward;
room-status histogram and Housekeeping Task count confirmed matching the
documented seed exactly.

## Phase 10 -- Reservation Calendar

No new doctype this phase -- a pure read-side aggregation over data every
prior phase already produces, the same shape Phase 5's Reports were over
Hotel Folio, this time over Reservation Room.

### Added

- **`services/front_desk.py::get_reservation_calendar(property=None,
  start_date=None, end_date=None)`** (default window: today + 13 days)
  -- every Confirmed Reservation Room line touching the window, plus the
  full Room list so an empty room still gets a row. Each booking carries
  `checked_in` (`hotel_stay` set or not), the same "already checked in"
  signal Arrivals/the Room Drawer already key off of.
  `api/front_desk.py::get_reservation_calendar` -- one thin wrapper.
- Frontend: `ReservationCalendar.vue` -- a rooms x dates grid (14-day
  window, Previous/Today/Next navigation), each booking rendered as a
  CSS-grid-column-spanning bar clicking through to Reservation Detail.
  Bar color reuses the existing room-status palette by meaning, not a
  new one: `room-reserved` (upcoming) vs. `room-occupied` (checked in).
  Routed from both `/front-desk/reservation-calendar` and `/reservations/
  calendar` -- the same "reachable from two sidebar sections" pattern
  the top-level Dashboard entry already has.

### Fixed

**`utils/dates.ts`'s `toIsoDate()`/`addDaysIso()` silently shifted every
date back by one day in any positive-UTC-offset timezone** -- including
this bench's own server timezone, Asia/Riyadh (UTC+3). Root cause:
`toIsoDate()` formatted via `date.toISOString().slice(0, 10)` (always
UTC), while `addDaysIso()` parsed `${isoDate}T00:00:00` (no offset
suffix, so JavaScript interprets it as *local* time) and called the
*local* `.setDate()`. Round-tripping local midnight through a UTC-based
formatter shifts it back a day whenever local time is ahead of UTC --
`addDaysIso(todayIso(), 0)` silently returned *yesterday*. Caught when
`ReservationCalendar.vue` displayed "today" as a visibly wrong date in
its grid header -- a mistake impossible to miss in prominent display
text, unlike a date `<input>`'s bound value. `NewReservation.vue`,
`Availability.vue`, and all three date-ranged Reports pages
(`OccupancyRevenueReport`/`PaymentReport`/`HousekeepingReport`) had the
exact same latent bug in their default arrival/departure/date-range
values since Phases 2 and 5 respectively -- confirmed via browser after
the fix: `NewReservation`'s and `Availability`'s date inputs now
correctly default to today/tomorrow (previously yesterday/today), and
Occupancy's default range now correctly ends today (previously
yesterday). Fixed once, at the root, by making `toIsoDate()` format from
the `Date` object's own local `getFullYear()`/`getMonth()`/`getDate()`
components instead of `toISOString()`, so it's consistent with
`addDaysIso()`'s already-local parsing -- no caller needed to change.

### Verification

`bench run-tests --app pp2_hotel`: **109 tests, all passing** (2 new in
`test_front_desk.py`, each with its own Property per the house rule --
`get_reservation_calendar`'s default 14-day window would otherwise pick
up other test methods' own bookings in that same shared-fixture class).
Frontend `yarn build` clean (one real TypeScript catch: a `.filter()`
chained after `.map()` needed the map callback's return type spelled out
explicitly, or the filter callback's parameter type couldn't be
inferred). Manual browser smoke: opened both calendar routes, confirmed
every seeded booking rendered as a bar in the right room row and correct
date position, in-house bookings showed the occupied color and upcoming
ones the reserved color, clicking a bar opened the right Reservation
Detail page, and Previous/Today/Next correctly shifted the visible
window -- this pass is what surfaced the date-utility bug above, fixed
in the same session, then re-verified (calendar, New Reservation,
Availability, and the Occupancy report all re-checked after the fix).
No test data was created during this pass (every page touched was
read-only), so no cleanup was required.

## Phase 11 -- Configuration UI

The first Vue screens for any Desk-only master doctype -- Property,
Floor, Room Type, Rate Plan, Hotel Service. **No new backend code at
all**: this phase is purely the frontend calling Frappe's own generic
`frappe.client.insert`/`save`/`delete`, relying entirely on each
doctype's DocType permission table (set in its own earlier phase) to
gate who can write it.

### Added

- **`components/config/MasterListPage.vue` + `MasterFormDialog.vue`** --
  one shared generic list+create+edit+delete shell instead of five
  near-duplicate bespoke CRUD pages. A `link`-type field fetches its
  options via `createListResource`, the same "select populated from a
  list fetch" pattern `AddChargeDialog.vue`/`OrderServiceDialog.vue`
  already use for picking a Hotel Service, generalized here instead of
  duplicated a third time.
- Five thin (~20-line) config pages supplying column/field config to
  `MasterListPage`: `PropertyConfig.vue` (company/currency/country/
  timezone/address stay Desk-only advanced fields -- only the fields
  staff actually touch day-to-day are exposed), `FloorsConfig.vue`,
  `RoomTypesConfig.vue`, `RatePlansConfig.vue` (Rate Plan shipped its
  schema back in Phase 6 with this exact screen deliberately deferred to
  "whichever phase actually ships Configuration UI"), `HotelServicesConfig.vue`.
- **Deliberately left `ComingSoon`**: `/configuration/taxes`,
  `/configuration/payment-methods`, `/configuration/system-settings` --
  none of them have a backing master doctype to manage yet
  (`Folio Payment.payment_method` is a hardcoded Select, not a separate
  master; there's no Tax doctype at all). Building one now would be new
  schema, not a UI-only phase.

### Fixed

Two real bugs in `MasterFormDialog.vue`, both caught by browser
verification (no backend test could have caught either -- there's no new
backend code this phase):

1. **Editing a record failed with a `TimestampMismatchError`** ("has
   been modified after you have opened it"). `frappe.client.save()` does
   an optimistic-lock check against the document's `modified` timestamp,
   which the form's minimal `{doctype, name, ...formData}` payload never
   included. Fixed by having `MasterListPage.vue` always fetch `modified`
   alongside each row's configured fields, round-tripped into the save
   payload.
2. **Fixing #1 immediately surfaced a second, worse failure**: "Value
   cannot be changed for Created On." A partial field dict sent to
   `frappe.client.save()` leaves every *other* standard field (`creation`,
   `owner`, ...) unset on the in-memory document Frappe builds from it --
   which reads as "changing `creation` to nothing" and gets rejected as
   an immutable-field violation. Fixed properly, not by chasing individual
   system fields one at a time: `MasterFormDialog.vue` now fetches the
   *complete* existing document via `frappe.client.get()` the moment the
   edit dialog opens, and saves `{...fullDocument, ...formData}` --
   every untouched field round-trips exactly as-is, only the form's own
   fields actually change.

### Verification

No new backend tests needed (no new backend code) -- `bench run-tests
--app pp2_hotel` re-confirmed green at its existing 109. Frontend `yarn
build` clean (one lint-level catch: an unused `ref` import left over
from an earlier draft of `MasterFormDialog.vue`). Manual browser smoke
exercised the full CRUD cycle end to end: created a Room Type, edited
its Base Rate (this is what first surfaced both bugs above), deleted it
(confirmed gone from both the list and, via `bench console`, the
database); created a Rate Plan referencing the demo Property and a Room
Type through the `link`-field selects, with realistic dates/rate, and
confirmed it rendered correctly in the list. All test data (the Room
Type, the Rate Plan) deleted afterward -- confirmed via `bench console`
that only the 3 originally-seeded Room Types remain and no stray Rate
Plans are left.

## Phase 12 -- Granular Permissions (Property-Scoped Access)

PERMISSIONS.md section 3 has said "not yet enforced" since Phase 1: a
`permission_query_conditions`/`has_permission` pair restricting a user
to only the Properties they're assigned to. This phase builds exactly
that, using the demo's real single-Property state to confirm the
mechanism itself (via tests spinning up two properties), not to change
anything about how the current demo behaves day to day.

### Added

- **Property User** (new doctype, `Hotel Setup` module) -- `property`,
  `user`, both required; rejects a duplicate `(property, user)` pair.
  Managed via a new `/configuration/property-access` screen (reusing
  Phase 11's `MasterListPage`/`MasterFormDialog`) or Frappe Desk. Not
  part of the brief's original nav tree -- added because granting/
  revoking property access needs *some* routine-admin-task screen, the
  same reasoning every other Configuration doctype already has one.
- **`pp2_hotel/permissions.py`**: `has_property_permission()` (shared
  across all seven scoped doctypes -- receives the actual document, so
  it just checks `doc.property` directly) and one
  `get_permission_query_conditions_*` wrapper per doctype (`Room`,
  `Room Type`, `Floor`, `Rate Plan`, `Hotel Stay`, `Hotel Folio`,
  `Reservation` -- the ones with a *direct* `property` field; doctypes
  only reachable via a `room` link, like Housekeeping Task or Service
  Order, are out of scope for this phase). System Manager/Hotel
  Administrator are exempt; every other role needs a `Property User`
  record or sees nothing property-scoped at all -- fail closed.
  Registered in `hooks.py`.

### Scope, stated plainly (see PERMISSIONS.md section 3 for the full
version)

These hooks gate `frappe.get_list`/direct document permission checks --
Frappe Desk, and Phase 11's Configuration UI (which reads via
`frappe.client`/`createListResource`, the permission-checked path).
**They do not restrict the custom Vue app's own dashboards, boards, or
reports** -- every `api.*` function in this app reads via
`frappe.get_all()`, documented to skip permission checks entirely, used
that way consistently since Phase 1. Making the Vue app itself
property-scoped would mean an explicit membership check inside each of
those ~15 functions individually, deliberately left for a future phase
rather than silently claimed here. With one demo Property today, this
distinction is invisible either way; it matters the moment a second
Property and a non-admin user both exist.

### Verification

`bench --site mysite.local clear-cache` (new `hooks.py` registrations)
then `migrate` clean (new doctype). `Property Setter`/`Document Naming
Rule` checked clean for `Property User`. `bench run-tests --app
pp2_hotel`: **114 tests, all passing** (5 new in `test_permissions.py`,
each building its own two Properties + a real test `User` -- property
membership is exactly the kind of state a shared fixture would leak
between methods). Manually verified via `bench console` before writing
formal tests: a fresh `Auditor`-role test user sees nothing property-
scoped with no `Property User` record; granting one flips `has_permission`
to `True` for that Property's Room only, not the other Property's;
`frappe.get_list` correctly filters a mixed-Property query down to just
the granted one; Administrator (System Manager) sees everything
regardless. Frontend `yarn build` clean. Browser smoke: opened
`/configuration/property-access`, created a grant for the demo Property
and a test scenario, confirmed it listed correctly, deleted it
afterward -- confirmed via `bench console` that no stray `Property User`
records or test `User` accounts remain.

## Phase 13 -- Final Testing Pass

The last phase on ARCHITECTURE.md's "Build phases" list. Every prior
phase shipped with its own test file verifying its feature in
isolation; nothing in the suite exercised the full guest lifecycle in
one continuous run, the kind of place a cross-phase interaction bug
(an integration point two phases both touch, built months apart in
this session) would hide even though every individual phase's own
tests stayed green.

### Added

- **`api/test_end_to_end.py::TestFullGuestLifecycle`** -- one test
  method, one guest, walking reservation -> confirm -> check-in (Phase
  2) -> a Service Order created then delivered (Phase 9, confirming the
  folio has zero items before delivery and exactly one after) -> a
  manual charge and payment (Phase 3) -> a Room Movement upgrade to a
  higher-rate room (Phase 6, confirming `Hotel Stay.rate` updates and
  the vacated room feeds Housekeeping) -> a full Housekeeping cycle on
  the vacated room (Phase 4) -> a Maintenance Request reported and
  resolved on that same now-`Available` room (Phase 8, confirming it
  goes back through Housekeeping once resolved) -> a final payment
  zeroing the balance -> checkout generating a real Draft Sales Invoice
  matching the folio's total exactly (Phase 7) -> a property-permission
  check confirming Administrator sees everything end to end with no
  `Property User` grant needed (Phase 12).

### Found while writing this

No application bugs -- every phase's integration point with its
neighbors held up exactly as documented. The one mistake was in the
test itself, caught before the first run: an early draft charged the
folio for the new room's rate after the Phase 6 Room Movement, as if
moving rooms auto-bills the difference. It doesn't -- Room Movement
only updates `Hotel Stay.rate` for whatever gets charged *next* (see
`services/room_movement.py`); it never touches the folio directly. The
corrected balance is just the Service Order charge plus the manual
Room Charge minus what had already been paid.

### Verification

`bench --site mysite.local run-tests --app pp2_hotel`: **115 tests, all
passing** (1 new). No schema changes, so no `migrate`/`clear-cache`
needed. This closes out all 13 build phases from ARCHITECTURE.md's
original phased-delivery plan.

### Addendum -- nav-route wiring audit

A closer look at `router/nav.ts` after the phase-completion claim above
found **32 of the 59 nav destinations still rendering `ComingSoon`** --
most are genuine, previously-undiscussed gaps (no phase ever built
Guest Profile/Guest Document/Guest Preference despite existing since
Phase 1/3, nor most of Billing's or Rooms' list/browse pages, nor the
Reservations sub-filters), not documentation drift. Two of the 32,
though, were real wiring bugs, not scope gaps -- the feature already
existed under a different nav path, but a second sidebar entry linking
to the same content had been silently falling through to `ComingSoon`
since the phase that built it:

- `/rooms/out-of-order` -- same board as `/maintenance/out-of-order`
  (built Phase 8). Now wired to the same `OutOfOrderRooms.vue`.
- `/housekeeping/reports` -- same report as `/reports/housekeeping-
  report` (built Phase 5). Now wired to the same `HousekeepingReport.vue`.

Both fixed in `router/index.ts` (added as extra keys in the existing
`PHASE8_ROUTES`/`PHASE5_ROUTES` maps, same "one component, two nav
paths" pattern Phase 10's Reservation Calendar already established).
`/housekeeping/room-status` was considered too but left `ComingSoon` --
no existing page actually renders that exact content, so wiring it to
something would be new scope, not a bug fix. The remaining ~30 stub
routes are a real, substantial gap in the original 13-phase build
covering the full product brief and would need their own scoping pass,
not a quick fix -- flagged to the user rather than assumed.

### Addendum -- Front Desk > Room Status wired up

The user then pointed out `/front-desk/room-status` and `/front-desk/
guest-search` both still showed `ComingSoon`. Investigated both before
touching either, since they turned out to need very different amounts
of work:

- **Room Status**: a pure reuse job, not new scope. `RoomGrid.vue`/
  `RoomDrawer.vue` (Phase 1) are already self-contained,
  property-agnostic components with their own data-fetching -- Dashboard.
  vue composes them alongside its KPI row, but nothing tied them to that
  page specifically. New `pages/front-desk/RoomStatus.vue` composes the
  same two components without the KPI row (title/subtitle only) and is
  now wired in `router/index.ts`. No new backend code. Verified in a
  real browser: floor-grouped grid renders identically to the Dashboard's
  own, clicking a room opens the same Room Drawer with the same
  status-gated actions.
- **Guest Search**: investigated, not built. The top-bar search input
  (`TopBar.vue`) is explicitly commented as "Visual only this phase --
  wiring a real cross-entity search ... is a later-phase concern once
  those endpoints exist" -- no search API exists anywhere in `api/` or
  `services/`, and there is no Guest Profile/Guest list page anywhere
  for search results to link to. This needs a new backend endpoint and
  real design decisions (what does "guest search" search — name only?
  phone/email? does a result open a not-yet-built Guest Profile, or
  something else?), so it was flagged back to the user rather than
  built on assumption.

`bench run-tests --app pp2_hotel`: 115 tests, all still passing (no
backend touched). `yarn build` clean.

### Addendum -- Guest Search built

The user asked again after the above, so it was scoped and built rather
than left `ComingSoon`. Search matches Guest name/phone/email
(`or_filters`, min 2 characters, 15-result cap). New
`services/front_desk.py::search_guests()` enriches each hit with
whatever front-desk context already exists for it: an in-house room (a
`Hotel Stay` with `status = "Checked In"`) or the earliest upcoming
`Confirmed` reservation that still has at least one not-yet-checked-in
`Reservation Room` line (same `hotel_stay.isnull() | == ""` join
`get_arrivals_today()` already uses, so a guest checked into every line
of their own reservation doesn't show as both in-house and upcoming at
once -- caught by a test, not by inspection: an early version used a
flat `Reservation.status == "Confirmed"` filter and showed a
just-checked-in guest as still "upcoming"). New
`pages/front-desk/GuestSearch.vue` reuses the debounce-via-`setTimeout`
pattern `NewReservation.vue`'s own guest picker already established (
`createListResource` has no built-in debounce). Since no Guest Profile
page exists to link a result to, a result with an in-house room opens
the existing Room Drawer and a result with an upcoming reservation
navigates to the existing Reservation Detail page -- a result with
neither just shows its contact details inline, same "reuse what already
exists, don't invent a new page as a side effect" discipline as Room
Status above.

4 new tests (name/phone/email match, the 2-character minimum, in-house
enrichment, upcoming-reservation enrichment) -- **119 tests, all
passing**. `yarn build` clean. Full browser verification: searched
"Sara" -> in-house badge with the correct room, clicked through to the
Room Drawer showing the correct balance; searched "Michael Chen" ->
"Arriving" badge with the correct date, clicked through to the correct
Reservation Detail page.

### Addendum -- sidebar scrollbar styling + Apps-screen check

The user then flagged two more things from screenshots: a scrollbar
showing inside the collapsed sidebar rail, and PP2 Hotel not appearing
on Frappe Desk's `/apps` icon grid.

- **Apps grid**: investigated via `bench console` -- `pp2_hotel` already
  has a correctly-configured `add_to_apps_screen` hook (same shape as
  `gcc_hr`'s, which does show), it's in `frappe.get_installed_apps()`,
  and `frappe.apps.get_apps()` (the exact function backing that screen)
  returns it correctly for Administrator. Not an app bug -- almost
  certainly a stale cached Desk session in the browser that was open
  before/during this session's changes. No code change; flagged back to
  the user with the verification, along with "hard refresh or re-login"
  as the fix rather than guessing at a code change with nothing to
  actually fix.
- **Sidebar scrollbar**: `AppSidebarNav.vue`'s `<nav>` (the collapsed
  icon rail and the expanded label view are the same element) is a
  legitimate `overflow-y-auto` scroll container -- it genuinely
  overflows on a short viewport with several sections expanded (11 top-
  level items, each with children). Could not exactly reproduce the
  user's screenshot's specific visual (their browser/OS's native,
  wide, high-contrast classic scrollbar with visible track-arrow
  buttons), but the underlying cause is real regardless: this app never
  styled its own scrollbars, so any container that does overflow falls
  back to whatever the browser/OS renders by default, which can look
  like a foreign, broken-looking element squeezed into the w-16
  collapsed rail. Added a `.pp2-scroll` utility class (`style.css`) --
  thin, design-token-colored (`--color-disabled` thumb, transparent
  track), applied to the sidebar nav and the main content area, not
  globally (frappe-ui's own imported components keep their own
  scrollbar styling untouched). Verified by forcing genuine overflow at
  a 500px-tall viewport with 6 sections expanded and cropping the
  screenshot at the scrollbar's exact pixel column -- confirmed thin,
  subtle, on-brand rendering instead of a thick native one.

`bench run-tests --app pp2_hotel`: 119 tests, all still passing (no
backend touched by the scrollbar fix). `yarn build` clean.

### Addendum -- the scrollbar's actual root cause

The `.pp2-scroll` styling above made a real overflow look better, but
the user's follow-up screenshot showed the exact same scrollbar was
still there -- and circling it made the real shape obvious: two
triangular arrow buttons either side of a short pill, sitting in a
horizontal band, not a vertical thumb running down the rail's right
edge. That's a **horizontal** scrollbar, not vertical, which pointed at
something more specific than "an unstyled generic overflow."

Confirmed via the DOM directly (`nav.scrollWidth: 167` vs
`nav.clientWidth: 63`, `getComputedStyle(nav).overflowX: 'auto'`) --
`AppSidebarNav.vue`'s `<nav>` only ever set `overflow-y: auto`, but the
CSS overflow spec computes `overflow-x` to `auto` too whenever it's left
at its initial `visible` while the other axis is non-`visible` (they
can't be independently visible/non-visible). The collapsed rail's own
per-item hover tooltip (`role="tooltip"`, `absolute left-full ...
whitespace-nowrap`) is real layout content -- `opacity-0` hides it
visually but doesn't remove it from flow -- and at ~104px wide it
comfortably exceeds the 64px collapsed rail, which is exactly the
104px gap between the observed 167px scrollWidth and 63px clientWidth.
So every collapsed-sidebar render had a permanent, always-present
horizontal overflow from its own tooltip markup, regardless of hover
state -- the `.pp2-scroll` styling made it look nicer but never
addressed why it existed.

**Fixed by removing the CSS-only tooltip entirely**: `AppSidebarNav.vue`
now tracks a single `hoveredTooltip` ref, set via `@mouseenter` (reading
the hovered icon's own `getBoundingClientRect()`) and cleared via
`@mouseleave`, and renders one tooltip `<Teleport to="body">` positioned
`fixed` from that rect. Being teleported out of `nav`'s subtree
entirely, it can no longer contribute to `nav`'s own scrollable-overflow
box no matter how wide its text is. Verified via the DOM again after
the fix: `scrollWidth === clientWidth` (63 = 63) both at rest and while
actively hovering a tooltip into view, and the tooltip's own parent
element is confirmed to be `<body>`, not `<nav>`. `.pp2-scroll`'s
styling stays in place as a real improvement for whenever the *expanded*
sidebar genuinely does overflow (many sections open on a short screen)
-- that overflow is real content, not a layout leak, and now renders
with the thin on-brand thumb instead of the browser default.

`bench run-tests --app pp2_hotel`: 119 tests, all still passing (no
backend touched). `yarn build` clean.

### Addendum -- app icon + the real reason it never showed on `/apps`

The user asked for a proper icon on Frappe Desk's Apps home screen (it
was still using the generic Frappe placeholder logo, same as `gcc_hr`'s
own hook). Added `public/images/pp2-hotel-logo.svg` -- the app's own
teal (`--color-primary` `#0f5c52`) rounded-square background with the
same `lucide` `BedDouble` glyph the sidebar's own header badge already
uses, so the Apps-screen tile and the in-app logo read as the same
brand mark. Updated `add_to_apps_screen`'s `logo` to
`/assets/pp2_hotel/images/pp2-hotel-logo.svg`.

While verifying it actually rendered, this **also explains the "PP2
Hotel doesn't show in the Apps grid" issue flagged earlier** in this
same phase -- the earlier verification (`frappe.apps.get_apps()`
returning `pp2_hotel` correctly via `bench console`) was real but
answered the wrong question, since that function turns out not to be
what drives this screen at all. Traced via the browser's own network
requests: the Apps grid is Frappe's `desktop` Page
(`frappe/desk/page/desktop/desktop.js`), which reads
`frappe.boot.desktop_icons` -- itself sourced from a real, persistent
**`Desktop Icon` doctype** with one record per app (`icon_type =
"App"`), auto-created *once* by `create_desktop_icons_from_installed_
apps()` (normally run as part of `bench install-app`'s own migration
step). Confirmed via `bench console`: `gcc_hr`/`qcore`/`erpnext`/`hrms`
all had their own `Desktop Icon` record; `pp2_hotel` had none at all --
it was added to this bench after that step already ran for the other
apps, so it was silently never backfilled. Fixed by calling Frappe's
own idempotent `create_desktop_icons_from_installed_apps()` directly
(it explicitly skips apps that already have a record, so safe to call
anytime), then clearing the `desktop_icons`/`bootinfo` Redis cache keys
so the already-logged-in Administrator session picks up the new icon
without a fresh login. Verified in a fresh, no-prior-cache browser
session: `pp2_hotel` now renders as its own teal bed-icon tile between
"Organization" and "Q-CORE" on `/apps`.

`bench run-tests --app pp2_hotel`: 119 tests, all still passing (no
backend touched). `yarn build` clean.
