# PP2 Hotel PMS Architecture

PP2 Hotel PMS is a Frappe app (`apps/pp2_hotel`) whose primary operational UI
is a dedicated Vue 3 SPA (`apps/pp2_hotel/frontend`), not the standard Frappe
Desk. Frappe provides auth, the database/ORM, background jobs, realtime and
file storage; PP2 Hotel PMS adds the hospitality domain model, permission
rules and business DocTypes on top. ERPNext stays the system of record for
accounting -- this app never reimplements a ledger, invoice or payment
engine, it links to ERPNext's.

## Relationship to `hospitality_pms`

This bench previously had a different hotel PMS app, `hospitality_pms`,
covering much of the same ground with a mature, hardened implementation
(354 passing backend tests, idempotent financial posting, Night Audit,
durable ledgers). It was uninstalled and archived (not deleted --
`archived/apps/hospitality_pms-<date>` in this bench) at the user's explicit
request, in favour of a from-scratch build under a new name and product
brief. Nothing from its code was copied; its existence did, however, surface
one real hazard worth recording: **core Frappe doctype-agnostic records --
Property Setter, Document Naming Rule, Custom Field, Client Script, Server
Script -- are not removed by `bench uninstall-app`,** because they aren't
owned by any specific app. When a new app defines a DocType with the same
name as one the old app used (`Guest`, `Room`, `Property`, `Floor`, `Room
Type` all collided here), any leftover Property Setter etc. targeting that
name silently applies to the new doctype. Phase 1 hit exactly this: a
leftover `Property Setter` overrode `Guest.naming_series.options` to the old
app's `HPMS-GST-.#####` prefix. Fixed by deleting the stray Property Setter
(`bench console` -> `frappe.delete_doc("Property Setter", "Guest-naming_series-options")`)
and flushing the cache. If a future phase introduces a doctype name that
existed in `hospitality_pms`, check `Property Setter`/`Document Naming
Rule`/`Custom Field` for that name first.

## Why a separate SPA instead of Frappe Desk

Front-desk, housekeeping and cashier workflows need drawer/modal-driven,
few-clicks interactions (click a room -> guest/stay/balance/actions in one
panel) that Desk's generic list/form paradigm isn't built for. Desk remains
available (and is where Administrators do config/data-fix work), but the
day-to-day operational surface is the Vue app.

## Repository layout

```
pp2_hotel/
  pp2_hotel/
    hotel_setup/            Frappe module: Property, Floor, Room Type,
                            Rate Plan (Phase 6), Property User (Phase 12)
      doctype/
        property/
        floor/
        room_type/
        rate_plan/
        property_user/
    hotel_rooms/             Frappe module: Room
      doctype/
        room/
    hotel_guests/             Frappe module: Guest
      doctype/
        guest/
    hotel_reservations/        Frappe module: Reservation, Reservation Room
      doctype/
        reservation/
        reservation_room/      (child table)
    hotel_front_office/        Frappe module: Hotel Stay, Room Movement
                                (Phase 6)
      doctype/
        hotel_stay/
        room_movement/
    hotel_billing/              Frappe module: Hotel Folio, Folio Item,
                                Folio Payment (Phase 3)
      doctype/
        hotel_folio/
        folio_item/            (child table)
        folio_payment/          (child table, Phase 3)
    hotel_services/              Frappe module: Hotel Service, Service
                                  Order (Phase 9)
      doctype/
        hotel_service/
        service_order/
    hotel_housekeeping/           Frappe module (Phase 4): Housekeeping Task,
                                  Room Inspection
      doctype/
        housekeeping_task/
        room_inspection/
    hotel_maintenance/            Frappe module (Phase 8): Maintenance Request
      doctype/
        maintenance_request/
    api/                          Whitelisted endpoints for the Vue frontend
                                  (thin -- validate input, call a service,
                                  shape the response)
      dashboard.py                get_front_desk_kpis, get_room_grid
      rooms.py                    get_room_detail
      reservations.py             create/confirm/cancel/mark_no_show
      checkin.py                  check_in
      availability.py              get_availability
      front_desk.py                 get_arrivals_today/get_departures_today/
                                    get_in_house/get_reservation_calendar
                                    (Phase 10)
      folio.py                       get_folio_detail, add_charge, add_payment
      checkout.py                    check_out
      housekeeping.py                 get_housekeeping_board, start_cleaning,
                                      mark_clean, inspect, report_maintenance
      reports.py                       Phase 5: five thin wrappers over
                                        services/reports.py
      room_movement.py                 Phase 6: move_room
      invoicing.py                      Phase 7: generate_invoice (also
                                        called automatically from
                                        checkout.py -- see below)
      maintenance.py                    Phase 8: get_maintenance_board,
                                        create_request, start_work,
                                        resolve_request, cancel_request
      service_orders.py                 Phase 9: get_service_board,
                                        create_order, deliver_order,
                                        cancel_order
    services/                     Authoritative domain logic
      dashboard.py                 KPI/room-grid aggregation
      rooms.py                     Room Drawer payload assembly
      room_status.py                Phase 4: the single writer of Room.status
                                    -- every other service below routes
                                    through this instead of calling
                                    frappe.db.set_value directly, see
                                    ROOM_STATUS_ENGINE.md
      stay.py                      Room-status sync on Hotel Stay lifecycle
                                    transitions
      reservations.py               Reservation lifecycle + the other half of
                                    the Reserved/Available room-status sync
      availability.py               Room-type availability over a date range
      checkin.py                    Reservation -> Hotel Stay + Hotel Folio
                                    orchestration (the only legal way to
                                    create a Hotel Stay)
      front_desk.py                  Arrivals/Departures/In-House worklists
                                    (cross-doctype joins over Reservation
                                    Room + Reservation + Hotel Stay + Folio),
                                    plus Phase 10's get_reservation_calendar
                                    -- rooms x a 14-day window of Confirmed
                                    Reservation Room lines, no new doctype
      folio.py                       add_charge/add_payment/get_folio_detail
      checkout.py                    Balance-gated checkout with an audited
                                    role-based override; also the integration
                                    point that auto-creates a housekeeping
                                    task the moment a room goes Dirty
      housekeeping.py                 The cleaning cycle: create_task ->
                                      start_cleaning -> mark_clean -> inspect
                                      (Passed -> Available, Failed -> re-queued
                                      Dirty) -> report_maintenance (Phase 8:
                                      now also calls maintenance.create_request)
      reports.py                       Phase 5: pure read-side aggregation --
                                        no new schema, no writes. Occupancy/
                                        Revenue/ADR/RevPAR (one combined
                                        report), Guest Ledger, Outstanding
                                        Balances, Payment Report, Housekeeping
                                        Report. Reads Room/Hotel Stay/Hotel
                                        Folio/Folio Item/Folio Payment/
                                        Housekeeping Task/Room Inspection --
                                        every doctype a prior phase already
                                        produces.
      rate_plan.py                      Phase 6: get_effective_rate --
                                        Active Rate Plan covering a date,
                                        else Room Type.base_rate
      room_movement.py                  Phase 6: move_room -- mirrors
                                        checkout's vacate-room pattern
                                        (vacated room -> Dirty + a
                                        Housekeeping Task), uses
                                        rate_plan.get_effective_rate for the
                                        destination room's rate
      invoicing.py                       Phase 7: get_or_create_customer_
                                        for_guest, generate_invoice -- no
                                        Item master needed, left as Draft
      maintenance.py                     Phase 8: create_request/start_work/
                                        resolve_request/cancel_request --
                                        create_request only flips Room.status
                                        to Maintenance for a vacant room (an
                                        Occupied one stays as-is);
                                        resolve_request/cancel_request reuse
                                        the same vacate-and-clean vs.
                                        revert-to-Available split
                                        cancel_reservation/checkout established
      service_orders.py                  Phase 9: create_order/deliver_order/
                                        cancel_order -- billing is decoupled
                                        from ordering (deliver_order calls
                                        folio.add_charge, create_order never
                                        does), so a cancelled order leaves no
                                        trace on the folio at all
    fixtures/
      role.json                    Section-17 role vocabulary (11 roles)
    demo/
      seed.py                      Idempotent local demo data -- not a fixture
    www/
      pp2_hotel.py, pp2_hotel.html  SPA entrypoint (auth-gated, boots the Vue app)
    permissions.py                Phase 12: has_property_permission +
                                  get_permission_query_conditions_* --
                                  registered per-doctype in hooks.py, not
                                  under services/ or api/ since it's not
                                  reached from the Vue frontend at all, only
                                  from Frappe's own permission-checking
                                  codepath (frappe.get_list, Desk). See its
                                  own module docstring for exactly what this
                                  restricts and what it doesn't.
    hooks.py

frontend/
  src/
    router/                        Routes + the full nested nav tree; dynamic
                                    (non-nav-tree) record routes added directly
                                    to appRoutes: /reservations/:name (Phase 2),
                                    /billing/folios/:folio (Phase 3)
    stores/                        Pinia: session (boot), ui (sidebar state)
    components/
      layout/                       AppShell, AppSidebar, TopBar, Breadcrumbs
      ui/                           LoadingState/EmptyState/ErrorState,
                                    StatusBadge, DataTable (Phase 2 -- the
                                    shared table behind every list page),
                                    ReasonPromptDialog (Phase 2 -- Cancel/
                                    Mark No Show's required-reason prompt)
      hotel/                        RoomCard, RoomGrid, RoomDrawer (its actions
                                    grid went from uniform-disabled to per-action
                                    enabled state across Phase 3/6/8 -- Guest
                                    Profile is the only permanently-disabled
                                    stub left), CheckInDialog (Phase 2),
                                    ReservationStatusPill (Phase 2 --
                                    Reservation.status colors, deliberately
                                    separate from StatusBadge's Room.status
                                    colors), AddChargeDialog/AddPaymentDialog/
                                    CheckoutDialog (Phase 3 -- shared between
                                    RoomDrawer and FolioDetail, not
                                    duplicated), MoveRoomDialog (Phase 6),
                                    ReportIssueDialog (Phase 8 -- the
                                    general-purpose "report an issue on any
                                    room" entry point, distinct from
                                    ReportMaintenanceDialog's Housekeeping-
                                    Task-scoped one from Phase 4),
                                    OrderServiceDialog (Phase 9 -- places a
                                    Pending Service Order, deliberately
                                    separate from AddChargeDialog's instant,
                                    no-delivery-step charge)
      config/                       Phase 11: MasterListPage + MasterFormDialog
                                    -- one generic list+create+edit+delete
                                    shell for the five simple master doctypes
                                    (Property, Floor, Room Type, Rate Plan,
                                    Hotel Service), shared instead of five
                                    near-duplicate bespoke CRUD pages. Calls
                                    Frappe's own generic frappe.client.insert/
                                    save/delete directly -- no new backend
                                    code this phase, each doctype's existing
                                    DocType permission table already gates
                                    who can write it. A `link`-type field
                                    fetches its options via createListResource,
                                    the same pattern AddChargeDialog.vue/
                                    OrderServiceDialog.vue already use for
                                    picking a Hotel Service, generalized.
    pages/
      reservations/                 Phase 2: NewReservation, ReservationList,
                                    ReservationDetail, Availability. Phase 10:
                                    ReservationCalendar (routed from both
                                    /front-desk/reservation-calendar and
                                    /reservations/calendar)
      front-desk/                   Phase 2: Arrivals, Departures, InHouseGuests
                                    (Departures/InHouseGuests reuse RoomDrawer
                                    for their row-click detail view rather than
                                    building a second one; Phase 3 wired their
                                    RoomDrawer's `checked-out` event to refresh
                                    these lists too, same fix as Dashboard's
                                    RoomGrid, since a checkout would otherwise
                                    leave a stale row behind)
      billing/                      Phase 3: FolioDetail (/billing/folios/:folio,
                                    Phase 7 added its Sales Invoice reference
                                    and "Generate Invoice" retry button)
      reports/                      Phase 5: OccupancyRevenueReport (routed
                                    from all four of /reports/occupancy,
                                    /revenue, /adr, /revpar -- one component,
                                    four nav entries), GuestLedger,
                                    OutstandingBalances, PaymentReport,
                                    HousekeepingReport.
      rooms/                        Phase 6: RoomMovementHistory
                                    (/rooms/movement).
      maintenance/                  Phase 8: MaintenanceDashboard
                                    (/maintenance), MaintenanceRequests
                                    (/maintenance/requests -- also doubles as
                                    the history view, see its own comment),
                                    OutOfOrderRooms (/maintenance/out-of-order,
                                    read-only).
      services/                     Phase 9: ServiceOrders -- one component
                                    routed from /services, /services/
                                    room-service, /services/laundry, /services/
                                    minibar (self-filters by reading
                                    route.path, not a route-level prop -- see
                                    its own comment).
      configuration/                Phase 11: PropertyConfig, FloorsConfig,
                                    RoomTypesConfig, RatePlansConfig,
                                    HotelServicesConfig -- each a thin
                                    ~20-line file supplying column/field
                                    config to MasterListPage. Phase 12:
                                    PropertyAccessConfig (Property User --
                                    not in the brief's original nav, added
                                    alongside the property-scoped permission
                                    mechanism itself). Everything else
                                    in the sidebar still routes to
                                    ComingSoon.vue -- including
                                    /configuration/taxes, /configuration/
                                    payment-methods, /configuration/
                                    system-settings, /maintenance/history and
                                    /services/other-charges, deliberately
                                    (see "Build phases").
```

## Layering

```
Vue page -> composable/store -> resource -> whitelisted API -> service -> ORM
```

Business rules live in `services/`. Never in Vue, never duplicated in a
DocType controller. DocType `validate()`/`on_update()` may call a service
(see `hotel_stay.py` calling `services/stay.py`), never reimplement one.

## Multi-property readiness

`Room`, `Room Type`, `Hotel Stay` and `Hotel Folio` (via its `Hotel Stay`
link) all carry a `property` field now, and every Phase 1 API accepts an
optional `property` filter, even though there is currently one demo
property and property-scoped permission query conditions aren't wired yet
(that's a Permissions-phase concern -- see PERMISSIONS.md). This mirrors
`qcore`'s own tenant-isolation approach (`qcore/utils/tenant.py`), applied to
properties instead of organizations.

## Role vocabulary

The section-17 role list (Hotel Administrator, Hotel Manager, Front Desk
Manager, Receptionist, Cashier, Housekeeping Manager, Housekeeper,
Accountant, Maintenance Manager, Maintenance Staff, Auditor) ships as a
fixture (`fixtures/role.json`) now so the frontend's role-based nav
filtering has something real to check against. DocType-level permissions
for the Phase 1 doctypes are set per PERMISSIONS.md; a full per-role matrix
across every doctype is a later phase's work as more doctypes land.

## Build phases

Phase 1 covered architecture, design system, layout, sidebar, Front Desk
Dashboard, Room Grid and Room Drawer, backed by nine DocTypes (Property,
Floor, Room Type, Room, Guest, Hotel Stay, Hotel Folio, Folio Item, Hotel
Service). Phase 2 added the booking -> check-in loop: Reservation and
Reservation Room, `services/reservations.py`, `services/availability.py`
and `services/checkin.py` orchestrating Hotel Stay creation (which is now
refused outside that service), and the New Reservation / All Reservations
/ Reservation Detail / Availability / Arrivals / Departures / In-House
Guests screens. Phase 3 closed the core guest lifecycle loop: Folio
Payment (a real multi-payment ledger replacing Phase 1's single editable
`paid_amount`), `services/folio.py` (add_charge/add_payment) and
`services/checkout.py` (balance-enforced checkout with an audited
override path), plus the Room Drawer's long-disabled Check-out/Add
Charge/Payment/View Folio actions and a new Folio Detail page. Phase 4
added Housekeeping: Housekeeping Task and Room Inspection, `Room.status`
gained `Cleaning`, `services/checkout.py` now auto-creates a task the
moment a room goes `Dirty`, and `services/room_status.py` centralized
every room-status write behind one function (see ROOM_STATUS_ENGINE.md --
this was the third-writer moment that file had been anticipating since
Phase 2). Phase 5 added Reports: no new schema, a pure read-side
aggregation layer over every doctype the prior four phases already
produce (`services/reports.py`) -- Occupancy/Revenue/ADR/RevPAR (one
combined report, since RevPAR = ADR x Occupancy% and real PMS reporting
screens present them together), Guest Ledger, Outstanding Balances
(deliberately including Closed folios with a balance -- real accounts
receivable a Phase 3 checkout override produces), Payment Report, and
Housekeeping Report. Phase 6 paired Room Movement (brief section 11 --
room-to-room transfer with a financial-impact summary) with Rate Plan
(date-range-aware pricing per Room Type, deferred since Phase 1 for lack
of a consumer): a move can upgrade/downgrade the guest into a different
Room Type, and computing that move's real rate needs Rate Plan's
`get_effective_rate()`, not just a flat `base_rate`. Rate Plan ships as
schema + that lookup only -- its own `/configuration/rate-plans` screen
is deferred to "Configuration UI" below, same as Property/Floor/Room
Type today. Phase 7 is the first phase to actually exercise this app's
own stated architecture ("ERPNext remains the financial and enterprise
system of record") -- `services/invoicing.py` generates a real ERPNext
Sales Invoice (left as Draft, not auto-submitted) the moment
`services/checkout.py` closes a folio, using no `item_code` at all
(confirmed live against this bench's ERPNext that `Sales Invoice Item`
only requires `item_name`/`uom`/`conversion_factor`/`rate`/
`income_account`/`cost_center`) and auto-provisioning an ERPNext Customer
per guest the first time it's needed. Invoicing is best-effort at
checkout time, never blocking it -- a Company/accounts misconfiguration
must never stop a front desk agent from physically checking a guest out,
so a failure is caught, logged, and surfaced as a non-blocking warning
with a manual "Generate Invoice" retry on Folio Detail instead. This
phase also fixed a real, silent data-integrity gap it uncovered: the
demo Property's `company` field had been getting auto-filled from a
stray, unrelated site-wide global default (`frappe.defaults.
get_global_default("company")` -- Frappe applies this to any Link field
literally named `company`, even via a raw `frappe.get_doc({...}).insert()`,
not just Desk forms) rather than ever being set by `demo/seed.py`. Fixed
by creating a dedicated `PP2 Demo Hotel` Company (SAR, matching every
figure already verified across 6 phases) and having the seed script set
it explicitly going forward. Phase 8 gave Phase 4's "Report Maintenance"
quick action the real ticket doctype it was always meant to graduate
into (`Maintenance Request`, `services/maintenance.py`) -- the first
real work for the Maintenance Manager/Staff roles since Phase 1. The one
design wrinkle: a room can have an issue reported on it while a guest is
still in it, so `create_request()` only takes the room out of rotation
(`Room.status = "Maintenance"`) when it's vacant, leaving an
Occupied/Reserved room's status untouched while still tracking the
ticket -- the one place in this app where a room's vacancy, not just a
stay/reservation status, gates a room-status transition. Resolving a
ticket reuses the same vacate-and-clean pattern as checkout/Room
Movement (-> `Dirty` + a Housekeeping Task); cancelling one (a mistaken
report) reverts straight to `Available` instead, since no actual repair
happened. `Out of Order` remains the one room state with no writer
anywhere in this app, unchanged and deliberately so -- a separate,
longer-term status from `Maintenance`'s active-repair lifecycle.

Phase 9 built the room-service/laundry/minibar order workflow
(`Service Order`, `services/service_orders.py`) DATABASE.md's Hotel
Service entry has pointed at "a later phase" since Phase 1 -- the rate
card and the billing mechanism (`services.folio.add_charge`) already
existed, what was missing was the operational order-taking step in
between. Deliberately decoupled: placing an order never touches the
folio, only `deliver_order()` does (calling `add_charge` internally) --
so a cancelled order leaves no trace on the bill, and the existing
`AddChargeDialog.vue`/`add_charge()` path stays untouched for the
still-valid, different need of an instant, no-delivery-step charge.

Phase 10 built the visual Reservation Calendar -- no new doctype, a pure
read-side aggregation (`services.front_desk.get_reservation_calendar()`)
over Confirmed Reservation Room lines, the same "aggregate what already
exists" shape Phase 5's Reports used over Hotel Folio. One component
(`ReservationCalendar.vue`) serves both `/front-desk/reservation-calendar`
and `/reservations/calendar`, the same "reachable from two sidebar
sections" duplication the top-level Dashboard entry already has. A
booking bar's color reuses the existing room-status palette by meaning,
not a new one: `room-reserved` for an upcoming booking, `room-occupied`
for one already checked in (`hotel_stay` set).

Phase 11 built Configuration UI -- the first Vue screens for any
Desk-only master doctype (Property, Floor, Room Type, Rate Plan, Hotel
Service). No new backend code at all: `MasterListPage.vue`/
`MasterFormDialog.vue` call Frappe's own generic `frappe.client.insert/
save/delete` directly, relying entirely on each doctype's existing
DocType permission table (set in its own earlier phase) to gate who can
write it. One shared pair of components serves all five doctypes instead
of five near-duplicate bespoke CRUD pages -- each doctype's own page is
just ~20 lines of column/field configuration. Taxes, Payment Methods,
and System Settings stay `ComingSoon`: none of them have a backing
master doctype to manage yet (`Folio Payment.payment_method` is a
hardcoded Select, not a separate master; there's no Tax doctype at all),
and inventing one now would be new schema, not a UI-only phase.

Phase 12 built property-scoped access -- `Property User` (new doctype)
plus `pp2_hotel/permissions.py`'s `has_permission`/
`permission_query_conditions` pair, registered in `hooks.py` for the
seven doctypes carrying a direct `property` field. This closes the gap
PERMISSIONS.md section 3 has flagged as "not yet enforced" since Phase
1, exactly the mechanism that section always said it would need
(mirroring `qcore/utils/tenant.py`'s own tenant isolation). **Read
PERMISSIONS.md section 3's own "scope of this" note before assuming more
than what's actually true**: these hooks gate Frappe Desk and the
Configuration UI's `frappe.client`-based reads, not the custom Vue app's
own dashboards/boards/reports -- every one of those reads via
`frappe.get_all()`, which has skipped permission checks entirely, by
design, in every service function in this app since Phase 1. Extending
property-scoping to the Vue app itself would mean touching each of those
~15 functions individually, deliberately left for a future phase rather
than silently claimed here.

Phase 13 -- the final testing pass -- added
`api/test_end_to_end.py::TestFullGuestLifecycle`, a single continuous
scenario that walks one guest through every phase in sequence
(reservation -> confirm -> check-in -> a Service Order ordered then
delivered -> a manual charge and payment -> a Room Movement upgrade,
whose vacated room feeds Housekeeping -> a Maintenance Request on that
same room, which feeds Housekeeping again once resolved -> a final
payment to zero the balance -> checkout, generating a real Draft Sales
Invoice matching the folio exactly -> a permission check). Every prior
phase's own test file already verifies its feature in isolation; this
one exists to catch the cross-phase interaction bugs an isolated unit
test can't -- e.g. confirming a Room Movement's vacated room really
does feed the Housekeeping cycle Phase 4 built, or that a Service
Order's Phase-9 charge really does show up on the same folio Phase 7's
invoice generation later reads from. No bugs were found by it -- every
prior phase's integration points already held up -- so it stands as a
regression guard, not a phase that changed behavior. All 13 build
phases are now complete; see CHANGELOG.md for the full phase-by-phase
history and DATABASE.md for every doctype's shipping phase.
