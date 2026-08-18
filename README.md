# PP2 Hotel PMS

A complete Hotel Property Management System built as a custom Frappe app on
**Frappe Framework v16** and **ERPNext v16**, with a dedicated **Vue 3**
operational frontend served at `/pp2_hotel`.

ERPNext remains the financial and enterprise system of record (Company,
Customer, Item, Sales Invoice, Payment Entry, Taxes). PP2 Hotel PMS owns the
day-to-day hospitality operations on top of it -- front desk, reservations,
billing, housekeeping, maintenance and guest services -- so nothing has to be
re-entered by hand between the two.

## Features

- **Front Desk & Rooms** -- live room status board grouped by floor, guest
  search, arrivals/departures worklists, and a room detail drawer with every
  guest-facing action in one place.
- **Reservations & Check-In** -- booking, confirmation, cancellation and
  no-show handling against real-time room availability, plus a visual
  reservation calendar.
- **Billing & Folio** -- a multi-payment guest folio that generates a real
  ERPNext Sales Invoice automatically at checkout, matching the folio exactly.
- **Room Movement & Rate Plans** -- move a guest between rooms mid-stay with
  automatic rate recalculation from date-range-aware rate plans.
- **Housekeeping** -- cleaning tasks and room inspections tied directly to
  room status, auto-triggered by checkout, room movement and maintenance.
- **Maintenance** -- repair request tracking that only pulls a room out of
  rotation when it's actually vacant.
- **Guest Services** -- order and deliver room service, laundry and minibar
  charges, billed to the folio only once delivered.
- **Reports & Analytics** -- occupancy, revenue, ADR, RevPAR, guest ledger,
  outstanding balances, payment history and housekeeping throughput.
- **Configuration UI** -- manage properties, floors, room types, rate plans
  and hotel services without leaving the app.
- **Property-Scoped Permissions** -- role- and property-based access control,
  ready for multiple properties from day one.

## Requirements

- Frappe Framework v16, ERPNext v16
- Python 3.14 (bench-managed)
- Node 24
- MariaDB, Redis

## Installation

1. Get the app into your bench:

   ```bash
   cd $PATH_TO_YOUR_BENCH
   bench get-app pp2_hotel https://github.com/codeoceanopen/pp2_hotel.git
   ```

2. Install it on a site:

   ```bash
   bench --site $SITE install-app pp2_hotel
   ```

3. Build the frontend (skip this if you're pulling a release with
   `pp2_hotel/public/frontend` already built):

   ```bash
   cd apps/pp2_hotel/frontend
   yarn install
   yarn build
   ```

4. Open `http://$SITE/pp2_hotel` and log in with a Frappe user that has one
   of the app's hotel roles (see PERMISSIONS.md).

### Demo data (optional)

Seeds a demo property, rooms, guests and reservations for local review:

```bash
bench --site $SITE execute pp2_hotel.demo.seed.run
```

Idempotent, and not a fixture -- this is throwaway data, not reference
configuration.

## Frontend development

```bash
cd apps/pp2_hotel/frontend
yarn install
yarn dev      # dev server, proxies API calls to the running bench
yarn build    # production build -- output lands in ../pp2_hotel/public/frontend
```

Frappe Desk remains available at `/app` for configuration, master data and
Administrator-level data fixes.

## Testing

```bash
bench --site $SITE run-tests --app pp2_hotel
```

## Further reading

- `ARCHITECTURE.md` -- how the app is put together
- `DATABASE.md` -- full schema reference
- `PERMISSIONS.md` -- the access-control model
- `ROOM_STATUS_ENGINE.md` -- how Room / Hotel Stay / Hotel Folio fit together
- `CHANGELOG.md` -- release history

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/pp2_hotel
pre-commit install
```

Pre-commit is configured to use ruff, eslint and prettier.

## License

MIT
