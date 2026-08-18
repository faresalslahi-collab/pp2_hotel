### PP2 Hotel PMS

A professional, production-ready Hotel Property Management System built as an
independent Frappe custom app on Frappe Framework v16 and ERPNext v16, with a
Vue 3 operational frontend served from the Frappe site at `/pp2_hotel`.

ERPNext remains the financial and enterprise system of record (Company,
Customer, Item, Sales Invoice, Payment Entry, Taxes). PP2 Hotel PMS owns the
operational hospitality domain: property/room/rate configuration, guests,
front office and stay, guest folio, reservations, checkout, room movement,
housekeeping, maintenance, guest services, and property-scoped access
control.

See ARCHITECTURE.md for how it's put together, CHANGELOG.md for what's
shipped so far (all 13 build phases complete -- see "Build phases" in
ARCHITECTURE.md), DATABASE.md for the full schema, PERMISSIONS.md for
the access-control model, and ROOM_STATUS_ENGINE.md for how Room / Hotel
Stay / Hotel Folio fit together.

This app replaces an earlier hotel PMS app that lived in this same bench
(`hospitality_pms`) -- see ARCHITECTURE.md's "Relationship to `hospitality_pms`"
section for why, and what was carried over as house style versus rebuilt.

### Requirements

- Frappe Framework v16, ERPNext v16
- Python 3.14 (bench-managed)
- Node 24
- MariaDB, Redis

### Installation

This app already lives in this bench at `apps/pp2_hotel` and is installed on
`mysite.local`. To install it on another site:

```bash
cd $PATH_TO_YOUR_BENCH
bench --site $SITE install-app pp2_hotel
```

### Frontend development

```bash
cd apps/pp2_hotel/frontend
yarn install
yarn dev      # dev server, proxies API calls to the running bench
yarn build    # production build -- also generates ../pp2_hotel/www/pp2_hotel.html
```

The operational frontend is served at `http://<site>/pp2_hotel`. Frappe Desk
remains available for configuration, master data and Administrator-level
data fixes.

### Demo data

```bash
bench --site $SITE execute pp2_hotel.demo.seed.run
```

Idempotent -- guarded by the demo Property's existence. Not a fixture: this
is throwaway data for local review, not reference configuration.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/pp2_hotel
pre-commit install
```

Pre-commit is configured to use ruff, eslint and prettier.

### License

mit
