import type { Component } from 'vue'
import {
	Home,
	Bell,
	Calendar,
	Users,
	BedDouble,
	Wallet,
	Sparkles,
	Wrench,
	UtensilsCrossed,
	BarChart3,
	Settings,
} from 'lucide-vue-next'

export interface NavChild {
	label: string
	route: string
	// Leaf items don't render their own icon in the tree (only top-level
	// sections do, both inline and in the collapsed icon-only rail) -- a
	// per-child icon for ~60 leaf items added a lot of picking-arbitrary-
	// icons noise for no real navigational benefit. Kept optional on the
	// type in case a later phase wants one for a specific item.
	icon?: Component
	roles?: string[]
}

export interface NavItem {
	label: string
	icon: Component
	route?: string
	roles?: string[]
	children?: NavChild[]
}

// Role-gated nav, first pass: granular per-DocType permissions aren't built
// yet on the backend, so for now an item either has no `roles` restriction
// (visible to everyone who can reach the app) or restricts to
// ["System Manager", "Hotel Administrator"]. This still exercises the real
// mechanism (AppSidebar.vue filters the array so unauthorized routes are
// never even rendered, not just CSS-hidden) so wiring per-role/per-DocType
// visibility later is a data change here, not a rework.
const ADMIN_ROLES = ['System Manager', 'Hotel Administrator']

export const NAV_TREE: NavItem[] = [
	{ label: 'Dashboard', icon: Home, route: '/' },
	{
		label: 'Front Desk',
		icon: Bell,
		children: [
			// Same screen as the top-level "Dashboard" link -- Front Desk
			// Dashboard *is* Dashboard.vue, just also reachable from inside
			// its own section per the nav spec.
			{ label: 'Front Desk Dashboard', route: '/' },
			{ label: 'Arrivals', route: '/front-desk/arrivals' },
			{ label: 'Departures', route: '/front-desk/departures' },
			{ label: 'In-House Guests', route: '/front-desk/in-house-guests' },
			{ label: 'Room Status', route: '/front-desk/room-status' },
			{ label: 'Reservation Calendar', route: '/front-desk/reservation-calendar' },
			{ label: 'Guest Search', route: '/front-desk/guest-search' },
		],
	},
	{
		label: 'Reservations',
		icon: Calendar,
		children: [
			{ label: 'All Reservations', route: '/reservations' },
			{ label: 'New Reservation', route: '/reservations/new' },
			{ label: 'Reservation Calendar', route: '/reservations/calendar' },
			{ label: 'Availability', route: '/reservations/availability' },
			{ label: 'Group Reservations', route: '/reservations/group' },
			{ label: 'Cancellations', route: '/reservations/cancellations' },
			{ label: 'No Shows', route: '/reservations/no-shows' },
		],
	},
	{
		label: 'Guests',
		icon: Users,
		children: [
			{ label: 'Guest Profiles', route: '/guests' },
			{ label: 'Companies', route: '/guests/companies' },
			{ label: 'Guest History', route: '/guests/history' },
			{ label: 'Documents', route: '/guests/documents' },
			{ label: 'Preferences', route: '/guests/preferences' },
		],
	},
	{
		label: 'Rooms',
		icon: BedDouble,
		children: [
			{ label: 'Room Overview', route: '/rooms' },
			{ label: 'Room Types', route: '/rooms/types' },
			{ label: 'Rooms', route: '/rooms/list' },
			{ label: 'Floors', route: '/rooms/floors' },
			{ label: 'Room Availability', route: '/rooms/availability' },
			{ label: 'Room Movement', route: '/rooms/movement' },
			{ label: 'Out of Order', route: '/rooms/out-of-order' },
		],
	},
	{
		label: 'Billing & Folio',
		icon: Wallet,
		children: [
			{ label: 'Folios', route: '/billing/folios' },
			{ label: 'Open Folios', route: '/billing/open-folios' },
			{ label: 'Room Charges', route: '/billing/room-charges' },
			{ label: 'Service Charges', route: '/billing/service-charges' },
			{ label: 'Payments', route: '/billing/payments' },
			{ label: 'Advance Payments', route: '/billing/advance-payments' },
			{ label: 'Payment Allocation', route: '/billing/payment-allocation' },
			{ label: 'Checkout', route: '/billing/checkout' },
		],
	},
	{
		label: 'Housekeeping',
		icon: Sparkles,
		children: [
			{ label: 'Housekeeping Dashboard', route: '/housekeeping' },
			{ label: 'Cleaning Tasks', route: '/housekeeping/cleaning-tasks' },
			{ label: 'Room Inspection', route: '/housekeeping/room-inspection' },
			{ label: 'Room Status', route: '/housekeeping/room-status' },
			{ label: 'Housekeeping Reports', route: '/housekeeping/reports' },
		],
	},
	{
		label: 'Maintenance',
		icon: Wrench,
		children: [
			{ label: 'Maintenance Dashboard', route: '/maintenance' },
			{ label: 'Maintenance Requests', route: '/maintenance/requests' },
			{ label: 'Out of Order Rooms', route: '/maintenance/out-of-order' },
			{ label: 'Maintenance History', route: '/maintenance/history' },
		],
	},
	{
		label: 'Services',
		icon: UtensilsCrossed,
		children: [
			{ label: 'Hotel Services', route: '/services' },
			{ label: 'Room Service', route: '/services/room-service' },
			{ label: 'Laundry', route: '/services/laundry' },
			{ label: 'Minibar', route: '/services/minibar' },
			{ label: 'Other Charges', route: '/services/other-charges' },
		],
	},
	{
		label: 'Reports',
		icon: BarChart3,
		children: [
			{ label: 'Occupancy', route: '/reports/occupancy' },
			{ label: 'Revenue', route: '/reports/revenue' },
			{ label: 'ADR', route: '/reports/adr' },
			{ label: 'RevPAR', route: '/reports/revpar' },
			{ label: 'Guest Ledger', route: '/reports/guest-ledger' },
			{ label: 'Outstanding Balances', route: '/reports/outstanding-balances' },
			{ label: 'Payment Report', route: '/reports/payment-report' },
			{ label: 'Housekeeping Report', route: '/reports/housekeeping-report' },
		],
	},
	{
		label: 'Configuration',
		icon: Settings,
		roles: ADMIN_ROLES,
		children: [
			{ label: 'Property', route: '/configuration/property' },
			{ label: 'Floors', route: '/configuration/floors' },
			{ label: 'Room Types', route: '/configuration/room-types' },
			{ label: 'Rate Plans', route: '/configuration/rate-plans' },
			{ label: 'Taxes', route: '/configuration/taxes' },
			{ label: 'Payment Methods', route: '/configuration/payment-methods' },
			{ label: 'Hotel Services', route: '/configuration/hotel-services' },
			{ label: 'System Settings', route: '/configuration/system-settings' },
			// Phase 12: not in the brief's original nav -- added because
			// Property User (property-scoped access, see PERMISSIONS.md
			// section 3) needs *some* way to be managed by System Manager/
			// Hotel Administrator without dropping into Frappe Desk for a
			// routine admin task, the same reasoning every other doctype in
			// this section already gets a real screen for.
			{ label: 'Property Access', route: '/configuration/property-access' },
		],
	},
]
