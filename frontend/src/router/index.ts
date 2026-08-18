import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { NAV_TREE } from './nav'
import { useSessionStore } from '@/stores/session'

// Every route this phase ships is generated from NAV_TREE (router/nav.ts)
// so the sidebar and the router table can never drift out of sync -- add a
// destination to the nav tree and it automatically gets a route here,
// rendered by ComingSoon.vue unless it's one of the real screens built out
// this phase or last (Dashboard, plus Phase 2's Reservations/Front Desk
// screens below).
//
// Phase 2 ships six real screens that were previously ComingSoon stubs --
// listed here so the generation loop can swap in the real lazy-loaded
// component without hand-duplicating the NAV_TREE traversal that already
// exists for every other destination.
const PHASE2_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/reservations': () => import('@/pages/reservations/ReservationList.vue'),
	'/reservations/new': () => import('@/pages/reservations/NewReservation.vue'),
	'/reservations/availability': () => import('@/pages/reservations/Availability.vue'),
	'/front-desk/arrivals': () => import('@/pages/front-desk/Arrivals.vue'),
	'/front-desk/departures': () => import('@/pages/front-desk/Departures.vue'),
	'/front-desk/in-house-guests': () => import('@/pages/front-desk/InHouseGuests.vue'),
}

// Front Desk > Room Status -- wired during the Phase 13 nav audit. The
// RoomGrid/RoomDrawer pair Dashboard.vue already uses is fully
// self-contained and property-agnostic, so this is a standalone page
// composing the same two components without the KPI row, not new
// backend work. See RoomStatus.vue's own comment.
const NAV_AUDIT_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/front-desk/room-status': () => import('@/pages/front-desk/RoomStatus.vue'),
	'/front-desk/guest-search': () => import('@/pages/front-desk/GuestSearch.vue'),
}

// Phase 4 swaps in three of the five stubbed Housekeeping routes -- Room
// Status and Housekeeping Reports stay ComingSoon (out of scope this phase,
// see the product spec's "What NOT to build" section).
const PHASE4_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/housekeeping': () => import('@/pages/housekeeping/HousekeepingDashboard.vue'),
	'/housekeeping/cleaning-tasks': () => import('@/pages/housekeeping/CleaningTasks.vue'),
	'/housekeeping/room-inspection': () => import('@/pages/housekeeping/RoomInspections.vue'),
}

// Phase 5 ships all eight of the Reports section's routes. Four of them --
// Occupancy, Revenue, ADR, RevPAR -- share a single component
// (OccupancyRevenueReport.vue) rather than four near-duplicate files, since
// the backend's get_occupancy_revenue_report already returns all four
// metrics from one call (see that file's top-of-file comment).
const PHASE5_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/reports/occupancy': () => import('@/pages/reports/OccupancyRevenueReport.vue'),
	'/reports/revenue': () => import('@/pages/reports/OccupancyRevenueReport.vue'),
	'/reports/adr': () => import('@/pages/reports/OccupancyRevenueReport.vue'),
	'/reports/revpar': () => import('@/pages/reports/OccupancyRevenueReport.vue'),
	'/reports/guest-ledger': () => import('@/pages/reports/GuestLedger.vue'),
	'/reports/outstanding-balances': () => import('@/pages/reports/OutstandingBalances.vue'),
	'/reports/payment-report': () => import('@/pages/reports/PaymentReport.vue'),
	'/reports/housekeeping-report': () => import('@/pages/reports/HousekeepingReport.vue'),
	// Same report reachable from a second nav path (Housekeeping section, not
	// just Reports) -- same two-destinations-one-component pattern as Phase
	// 10's Reservation Calendar. Fixed 2026-08-17 during the Phase 13 audit --
	// this second nav entry had been silently falling through to ComingSoon
	// since Phase 5 shipped.
	'/housekeeping/reports': () => import('@/pages/reports/HousekeepingReport.vue'),
}

// Phase 6 ships one of the two still-stubbed Rooms-section routes -- Room
// Movement's full history list. Rate Plan's own `/configuration/rate-plans`
// stays ComingSoon: it's Desk-managed config this phase (see
// ARCHITECTURE.md's "Build phases"), same as Property/Floor/Room Type.
const PHASE6_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/rooms/movement': () => import('@/pages/rooms/RoomMovementHistory.vue'),
}

// Phase 8 ships three of Maintenance's four stubbed routes -- Maintenance
// History stays ComingSoon, same reasoning as Housekeeping leaving two of
// its five unbuilt in Phase 4 (see MaintenanceRequests.vue's own comment).
// '/rooms/out-of-order' is the same Out of Order board reachable from a
// second nav path (Rooms section, not just Maintenance) -- same
// two-destinations-one-component pattern as Phase 10's Reservation
// Calendar, not new scope. Fixed 2026-08-17 during the Phase 13 audit --
// this second nav entry had been silently falling through to ComingSoon
// since Phase 8 shipped.
const PHASE8_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/maintenance': () => import('@/pages/maintenance/MaintenanceDashboard.vue'),
	'/maintenance/requests': () => import('@/pages/maintenance/MaintenanceRequests.vue'),
	'/maintenance/out-of-order': () => import('@/pages/maintenance/OutOfOrderRooms.vue'),
	'/rooms/out-of-order': () => import('@/pages/maintenance/OutOfOrderRooms.vue'),
}

// Phase 9 ships four of Services' five stubbed routes as one component
// (ServiceOrders.vue determines its own category filter from route.path --
// see its own comment) -- Other Charges stays ComingSoon, redundant with
// AddChargeDialog's existing free-text path.
const PHASE9_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/services': () => import('@/pages/services/ServiceOrders.vue'),
	'/services/room-service': () => import('@/pages/services/ServiceOrders.vue'),
	'/services/laundry': () => import('@/pages/services/ServiceOrders.vue'),
	'/services/minibar': () => import('@/pages/services/ServiceOrders.vue'),
}

// Phase 10 ships the Reservation Calendar -- one component reachable from
// two nav destinations (Front Desk and Reservations sections both link to
// it), same "Front Desk Dashboard is also just Dashboard.vue" duplication
// pattern nav.ts already has for the top-level Dashboard entry.
const PHASE10_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/front-desk/reservation-calendar': () => import('@/pages/reservations/ReservationCalendar.vue'),
	'/reservations/calendar': () => import('@/pages/reservations/ReservationCalendar.vue'),
}

// Phase 11 ships the first Vue screens for any Desk-only config doctype --
// Property, Floor, Room Type, Rate Plan, Hotel Service. Taxes/Payment
// Methods/System Settings stay ComingSoon: none of them have a backing
// master doctype of their own to manage (Folio Payment.payment_method is a
// hardcoded Select, not a separate master; there's no Tax doctype at all)
// -- inventing one now would be new schema, not a UI-only phase.
const PHASE11_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/configuration/property': () => import('@/pages/configuration/PropertyConfig.vue'),
	'/configuration/floors': () => import('@/pages/configuration/FloorsConfig.vue'),
	'/configuration/room-types': () => import('@/pages/configuration/RoomTypesConfig.vue'),
	'/configuration/rate-plans': () => import('@/pages/configuration/RatePlansConfig.vue'),
	'/configuration/hotel-services': () => import('@/pages/configuration/HotelServicesConfig.vue'),
}

// Phase 12: Property Access (Property User) isn't part of the brief's
// original nav -- see nav.ts's own comment for why it was added anyway.
const PHASE12_ROUTES: Record<string, RouteRecordRaw['component']> = {
	'/configuration/property-access': () => import('@/pages/configuration/PropertyAccessConfig.vue'),
}

function comingSoonRoute(path: string, title: string): RouteRecordRaw {
	const realComponent =
		PHASE2_ROUTES[path] ??
		NAV_AUDIT_ROUTES[path] ??
		PHASE4_ROUTES[path] ??
		PHASE5_ROUTES[path] ??
		PHASE6_ROUTES[path] ??
		PHASE8_ROUTES[path] ??
		PHASE9_ROUTES[path] ??
		PHASE10_ROUTES[path] ??
		PHASE11_ROUTES[path] ??
		PHASE12_ROUTES[path]
	if (realComponent) {
		return {
			path,
			name: path,
			component: realComponent,
			meta: { title },
		}
	}
	return {
		path,
		name: path,
		component: () => import('@/pages/ComingSoon.vue'),
		// Static props (an object, not a function) -- vue-router just passes
		// these through as-is, no route params involved.
		props: { title, description: 'Coming in a later phase.' },
		meta: { title },
	}
}

const seenPaths = new Set<string>(['/'])
const generatedRoutes: RouteRecordRaw[] = []

for (const item of NAV_TREE) {
	if (item.route && !seenPaths.has(item.route)) {
		seenPaths.add(item.route)
		generatedRoutes.push(comingSoonRoute(item.route, item.label))
	}
	for (const child of item.children ?? []) {
		if (!seenPaths.has(child.route)) {
			seenPaths.add(child.route)
			generatedRoutes.push(comingSoonRoute(child.route, child.label))
		}
	}
}

// Everything is nested under AppShell (sidebar + top bar), using absolute
// (leading-slash) child paths -- Vue Router 4 still renders these through
// the parent's <router-view>, it just doesn't prefix the parent's own path
// onto them. Same layout-nesting pattern gcc_hr's frontend uses in this
// bench.
const appRoutes: RouteRecordRaw[] = [
	{
		path: '/',
		name: 'Dashboard',
		component: () => import('@/pages/Dashboard.vue'),
		meta: { title: 'Front Desk Dashboard' },
	},
	// Not nav-tree-generated -- a Reservation detail page is reached by
	// clicking into a specific record (from ReservationList, New
	// Reservation, or the front-desk list pages), never from a static
	// sidebar destination, so it has no NAV_TREE entry of its own.
	{
		path: '/reservations/:name',
		name: 'ReservationDetail',
		component: () => import('@/pages/reservations/ReservationDetail.vue'),
		props: true,
		meta: { title: 'Reservation' },
	},
	// Same reasoning as ReservationDetail above -- a Folio detail page is
	// reached only via RoomDrawer's View Folio action (or a direct URL),
	// never from a static sidebar destination. No Folios list page exists
	// this phase (see the product spec's "What NOT to build" section).
	{
		path: '/billing/folios/:folio',
		name: 'FolioDetail',
		component: () => import('@/pages/billing/FolioDetail.vue'),
		props: true,
		meta: { title: 'Folio' },
	},
	...generatedRoutes,
	{
		path: '/:pathMatch(.*)*',
		name: 'NotFound',
		component: () => import('@/pages/ComingSoon.vue'),
		props: { title: 'Not Found', description: 'This page does not exist.' },
		meta: { title: 'Not Found' },
	},
]

const router = createRouter({
	history: createWebHistory('/pp2_hotel'),
	routes: [
		{
			path: '/',
			component: () => import('@/components/layout/AppShell.vue'),
			children: appRoutes,
		},
	],
})

// No client-side login page this phase -- a Guest hitting /pp2_hotel is
// redirected server-side by www/pp2_hotel.py before the SPA shell is ever
// served (same pattern as qcore's www/qcore.py in this bench). This guard
// only has to make sure the session store is populated before any page
// renders and must never throw if boot globals are missing (backend may
// still be migrating in parallel) -- see stores/session.ts's bootstrap().
router.beforeEach(() => {
	const session = useSessionStore()
	if (!session.ready) session.bootstrap()
	return true
})

export default router
