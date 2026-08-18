# PP2 Hotel PMS Room Status Engine

`Room.status` is the single field the entire UI reads to decide what a
room card looks like on the Room Grid, what the Room Drawer shows, what
the Housekeeping Dashboard's worklist contains, and what the Front Desk
Dashboard's KPI counts add up to. Keeping exactly one writer-of-record for
it, with a documented state machine, matters more than almost anything
else in this app -- a stale or double-written status is the one bug that
would make the dashboard visibly lie to a receptionist.

## The states

```
Available -- sellable, no one in it
Occupied  -- a guest is currently checked in
Dirty     -- guest departed (or a failed inspection), awaiting cleaning
Cleaning  -- housekeeping is actively cleaning it right now (Phase 4)
Clean     -- cleaned, not yet inspected
Inspected -- transient: set only en route to Available, see below
Reserved  -- held for an upcoming arrival, not yet checked in
Out of Order   -- unsellable, structural/long-term issue
Maintenance    -- unsellable, active repair in progress
```

Every state now has a real writer as of Phase 8 except `Out of Order`
(still Desk-only -- no screen sets it yet, deliberately: it's a separate,
longer-term status from `Maintenance`'s active-repair lifecycle, see
"Maintenance Requests" below). `Inspected` is worth calling
out: `Room.status` passes through it only in principle -- in practice
`services.housekeeping.inspect()` sets the *room* straight to `Available`
on a pass (the *task's* status becomes `Inspected`, which is a different
field on a different doctype). A room's own status realistically only
ever shows `Clean` or `Available` after inspection, never `Inspected`
itself; that value exists in the Select for schema completeness with the
brief's vocabulary, not because anything sets it today.

## Three writers, centralized as of Phase 4

This file said back in Phase 2 that the moment a third writer landed, or
two writers needed to touch the same status, a shared transition point
would be worth building instead of speculating about it. Housekeeping is
that moment -- it writes `Cleaning`/`Clean`/`Available`/back-to-`Dirty`/
`Maintenance`, overlapping with what Hotel Stay and Reservation already
owned. **`services/room_status.py:set_room_status(room, new_status,
reason=None)`** is now the one place `Room.status` is actually written
(a `frappe.db.set_value()` guarded by the same read-before-write check
every writer used individually before); `reason` is accepted for a future
caller that needs to explain an override (none exists yet) but isn't
persisted. This was a refactor to the *shape* of existing logic, not new
transition rules -- Phase 1-3's behavior for Hotel Stay/Reservation is
unchanged, just routed through one function instead of three separate
`frappe.db.set_value` call sites.

**`services/stay.py:sync_room_status()`**, called from
`HotelStay.on_update()`:

```
Hotel Stay.status  ->  Room.status
Checked In         ->  Occupied
Checked Out        ->  Dirty
```

Checkout deliberately leaves the room `Dirty`, not `Available` -- and, as
of Phase 3, `services.checkout.check_out()` also calls
`services.housekeeping.create_task()` in the same breath, so a room going
`Dirty` and a cleaning task existing for it are the same event, not a
front-desk action followed by a separate, easy-to-forget housekeeping one.

**`services/reservations.py`** owns `Reserved` and its release back to
`Available`: `confirm_reservation()` sets `Reserved` for lines with a
pre-assigned room; `cancel_reservation()`/`mark_no_show()` release it back
to `Available` -- but only if the line never checked in (`row.hotel_stay`
is still empty).

**`services/housekeeping.py`** owns the cleaning cycle:

```
Housekeeping Task.status transition        ->  Room.status
create_task() (Pending)                     no room change -- task exists,
                                             room is already Dirty
start_cleaning()  Pending -> In Progress    -> Cleaning
mark_clean()      In Progress -> Completed  -> Clean
inspect(Passed)   Completed -> Inspected    -> Available
inspect(Failed)   Completed -> Pending      -> Dirty (re-queued, same task)
report_maintenance()  (task status unchanged) -> Maintenance
```

A failed inspection re-queues the *same* Housekeeping Task (cleared
`started_at`/`completed_at`, back to `Pending`) rather than creating a new
one, and records a `Room Inspection` row either way (`Passed` or
`Failed`) -- the QA history survives even though the task loops back.
`report_maintenance()` deliberately does not change the task's own status:
reporting a room broken mid-clean blocks it without discarding the fact
that cleaning was in progress or already done.

## Room Movement (Phase 6) -- a second call site, not a new writer

`services/room_movement.py:move_room()` moves a Checked In stay to a
different room, and touches `Room.status` on *both* rooms -- but adds no
new writer function of its own, it just calls the existing ones a second
time from a new place:

```
services.room_movement.move_room()
  stay.room = to_room; stay.save()  -> Hotel Stay.on_update() ->
                                       sync_room_status() -> to_room: Occupied
  set_room_status(from_room, "Dirty")
  housekeeping.create_task(from_room)
```

The destination room going `Occupied` is the *existing* Hotel Stay
mechanism firing again -- `sync_room_status()` doesn't know or care
whether `stay.room` changed because of a check-in or a mid-stay move, it
just marks whatever `stay.room` currently is as `Occupied` for a
`Checked In` stay. The vacated room going `Dirty` and getting a
Housekeeping Task is a direct copy of what `services.checkout.
check_out()` already does when a guest departs at the end of a stay --
a mid-stay move vacates a room exactly the same way a checkout does, so
it gets the same treatment. No new transition rule, no new field on
`set_room_status()`, nothing added to the "three writers" list above.

## No bigger state machine yet, still deliberately

Three writers now exist, but still with no overlap in which statuses each
one owns (Hotel Stay: Occupied/Dirty; Reservation: Reserved; Housekeeping:
Cleaning/Clean/Available/Dirty/Maintenance -- the one shared value,
`Dirty`, is written by exactly two writers but never concurrently: Hotel
Stay sets it once at checkout, Housekeeping only ever sets it back to
`Dirty` from its *own* prior `Clean` state on a failed inspection) and no
concurrent-write scenario. A proper directed graph with validated
transitions (no jumping straight from `Occupied` to `Available`, for
instance) and lock-then-read guards -- the way `hospitality_pms` (this
bench's earlier, more hardened hotel PMS app, since uninstalled -- see
ARCHITECTURE.md) enforced this with an idempotency key on every
state-changing operation -- would still be speculation about a need this
codebase doesn't have yet. Revisit when `Out of Order` gets a real writer,
or when any writer needs to touch a status another writer already owns.

## Where the Folio balance fits in

`Hotel Folio.balance` (see DATABASE.md) is not part of the room status
machine -- it's read alongside `Room.status` in `services/rooms.py:
get_room_detail()` purely for display in the Room Drawer, and it gates
*checkout* (`services.checkout.check_out()`), not any room status
transition. A guest with an outstanding balance is still `Occupied`.
