import type { RoomStatus } from '@/components/ui/StatusBadge.vue'

export type { RoomStatus }

// pp2_hotel.api.dashboard.get_front_desk_kpis
export interface FrontDeskKpis {
	arrivals_today: number
	departures_today: number
	in_house_guests: number
	available_rooms: number
	occupied_rooms: number
	dirty_rooms: number
	out_of_order_rooms: number
	todays_revenue: number
	currency: string
}

// pp2_hotel.api.dashboard.get_room_grid (bare array response)
export interface RoomGridItem {
	name: string
	room_number: string
	floor: string
	room_type: string
	status: RoomStatus
	guest_name: string | null
	stay: string | null
}

// pp2_hotel.api.rooms.get_room_detail
export interface RoomDetailRoom {
	name: string
	room_number: string
	floor: string
	room_type: string
	status: RoomStatus
	property: string
}

export interface RoomDetailStay {
	name: string
	guest: string
	guest_name: string
	arrival: string
	departure: string
	status: string
}

export interface RoomDetailFolio {
	name: string
	subtotal: number
	tax: number
	total: number
	paid: number
	balance: number
	currency: string
}

export interface RoomDetail {
	room: RoomDetailRoom
	stay: RoomDetailStay | null
	folio: RoomDetailFolio | null
}

// Reservation doctype -- status/source are Select fields on the backend
// (see hotel_reservations/doctype/reservation/reservation.json), reproduced
// here verbatim rather than widened to `string` so ReservationStatusPill.vue
// can exhaustively map every value to a color.
export type ReservationStatus = 'Draft' | 'Confirmed' | 'Cancelled' | 'No Show' | 'Completed'
export type ReservationSource = 'Walk-in' | 'Phone' | 'Email' | 'Direct' | 'Other'

// Reservation Room child table row -- returned as `doc.rooms` on the parent
// Reservation document (createDocumentResource), and echoed back per-line in
// pp2_hotel.api.front_desk.get_arrivals_today (as a sibling shape, see
// ArrivalRow below). `hotel_stay` is set once pp2_hotel.api.checkin.check_in
// has run for this line; null/falsy means "not yet checked in".
export interface ReservationRoom {
	name: string
	room_type: string
	room: string | null
	arrival: string
	departure: string
	adults: number
	children: number
	rate: number
	hotel_stay: string | null
}

// Reservation doctype -- both the plain list-view fields (ReservationList.vue,
// via createListResource) and the full document (ReservationDetail.vue, via
// createDocumentResource, where `rooms` is populated) share this shape;
// `rooms`/`notes` are simply absent/undefined on the list-view projection.
export interface Reservation {
	name: string
	guest: string
	property: string
	arrival: string
	departure: string
	status: ReservationStatus
	source: ReservationSource
	notes?: string | null
	creation?: string
	rooms?: ReservationRoom[]
}

// pp2_hotel.api.front_desk.get_arrivals_today (bare array response)
export interface ArrivalRow {
	reservation: string
	reservation_room: string
	guest: string
	room_type: string
	room: string | null
	arrival: string
	departure: string
	adults: number
	children: number
	guest_name: string
	room_type_name: string
}

// pp2_hotel.api.front_desk.get_departures_today / get_in_house (same shape
// for both -- "every currently checked-in stay" vs. "departing today")
export interface StayListRow {
	name: string
	guest: string
	room: string
	arrival: string
	departure: string
	guest_name: string
	room_number: string
	balance: number
	currency: string
}

// pp2_hotel.api.checkin.check_in
export interface CheckInResult {
	hotel_stay: string
	folio: string
}

// Hotel Service doctype -- plain CRUD via createListResource (no custom
// endpoint), used by AddChargeDialog.vue's optional service picker.
export interface HotelServiceOption {
	name: string
	service_name: string
	rate: number
	// Optional -- AddChargeDialog.vue's own picker doesn't fetch this field
	// (it doesn't need it), OrderServiceDialog.vue's does (to default a new
	// Service Order's service_type).
	service_type?: string
}

export type PaymentMethod = 'Cash' | 'Card' | 'Bank Transfer' | 'Online' | 'Other'

export const PAYMENT_METHODS: PaymentMethod[] = ['Cash', 'Card', 'Bank Transfer', 'Online', 'Other']

// Hotel Folio doctype -- only ever Closed by pp2_hotel.services.checkout.check_out,
// which happens exactly when the underlying Hotel Stay's status flips to
// "Checked Out". get_room_detail's own stay lookup only ever surfaces stays
// with status in ["Checked In", "Reserved"], so a folio present on RoomDetail
// is always Open in practice -- see RoomDrawer.vue's canFolioActions comment.
export type FolioStatus = 'Open' | 'Closed'

// pp2_hotel.api.folio.get_folio_detail -- one folio item (a charge/room-rate line)
export interface FolioDetailItem {
	name: string
	posting_date: string
	description: string
	hotel_service: string | null
	rate: number
	qty: number
	amount: number
}

// pp2_hotel.api.folio.get_folio_detail -- one recorded payment
export interface FolioDetailPayment {
	name: string
	posting_date: string
	amount: number
	payment_method: PaymentMethod
	reference: string | null
	notes: string | null
}

// pp2_hotel.api.folio.get_folio_detail
export interface FolioDetail {
	name: string
	stay: string
	guest: string
	guest_name: string
	room: string | null
	room_number: string | null
	arrival: string | null
	departure: string | null
	status: FolioStatus
	currency: string
	subtotal: number
	tax_rate: number
	tax_amount: number
	total: number
	paid_amount: number
	balance: number
	checkout_override_reason: string | null
	// Set once pp2_hotel.services.invoicing.generate_invoice() produces a
	// real ERPNext Sales Invoice for this folio (left as Draft, not
	// auto-submitted -- see services/invoicing.py). Null until then.
	sales_invoice: string | null
	items: FolioDetailItem[]
	payments: FolioDetailPayment[]
}

// pp2_hotel.api.checkout.check_out. Invoice generation is best-effort at
// checkout (a Company/accounts misconfiguration must never block a front
// desk agent from physically checking a guest out) -- `invoice` is null and
// `invoice_error` carries the reason when it failed, rather than the whole
// call throwing.
export interface CheckoutResult {
	stay: string
	folio: string | null
	overridden: boolean
	invoice: string | null
	invoice_error: string | null
}

// Housekeeping Task doctype's own status field -- distinct from RoomStatus.
// "Inspected" is a valid task status but never appears on the board (see
// HousekeepingBoardRow below): get_housekeeping_board only ever returns tasks
// that still need attention, so an Inspected task has already dropped off.
export type HousekeepingTaskStatus = 'Pending' | 'In Progress' | 'Completed' | 'Inspected'

// pp2_hotel.api.housekeeping.get_housekeeping_board (bare array response).
// Almost always a normal task row (`name` + `status` present). Rarely, a room
// ended up Dirty/Cleaning/Clean with no Housekeeping Task record at all --
// the backend defends against this by returning `name: null` and
// `orphan_room_status` instead of `status`, rather than crashing or omitting
// the room. HousekeepingDashboard.vue renders those rows read-only (no
// backend endpoint exists this phase to create a task for one).
export interface HousekeepingBoardRow {
	name: string | null
	room: string
	room_number: string
	status?: HousekeepingTaskStatus
	priority?: string
	assigned_to?: string | null
	started_at?: string | null
	completed_at?: string | null
	orphan_room_status?: RoomStatus
}

// Housekeeping Task doctype -- plain CRUD via createListResource
// (CleaningTasks.vue's full history list, unlike the Dashboard's
// active-only board).
export interface HousekeepingTask {
	name: string
	room: string
	status: HousekeepingTaskStatus
	priority: string
	assigned_to: string | null
	started_at: string | null
	completed_at: string | null
	creation: string
}

export type InspectionResult = 'Passed' | 'Failed'

// Room Inspection doctype -- plain CRUD via createListResource
// (RoomInspections.vue).
export interface RoomInspection {
	name: string
	housekeeping_task: string
	room: string
	result: InspectionResult
	inspector: string | null
	inspection_date: string
	notes: string | null
}

// pp2_hotel.api.room_movement.move_room
export interface RoomMovementResult {
	movement: string
	from_room: string
	to_room: string
	old_rate: number
	new_rate: number
	rate_difference: number
}

// Room Movement doctype -- plain CRUD via createListResource
// (RoomMovementHistory.vue), raw Link values shown as-is (guest/from_room/
// to_room), same convention as CleaningTasks.vue/RoomInspections.vue.
export interface RoomMovement {
	name: string
	hotel_stay: string
	guest: string
	movement_date: string
	from_room: string
	to_room: string
	old_rate: number
	new_rate: number
	rate_difference: number
	reason: string | null
}

// pp2_hotel.api.reports.get_occupancy_revenue_report -- one day's row in the
// `daily` breakdown array.
export interface OccupancyRevenueDailyRow {
	date: string
	occupied_rooms: number
	total_rooms: number
	occupancy_pct: number
	room_revenue: number
	other_revenue: number
	total_revenue: number
}

// pp2_hotel.api.reports.get_occupancy_revenue_report -- backs
// OccupancyRevenueReport.vue, which is routed from all four of Occupancy,
// Revenue, ADR, and RevPAR (see that file's top-of-file comment and
// PHASE5_ROUTES in router/index.ts).
export interface OccupancyRevenueReport {
	start_date: string
	end_date: string
	total_rooms: number
	occupancy_pct: number
	adr: number
	revpar: number
	total_revenue: number
	room_revenue: number
	other_revenue: number
	daily: OccupancyRevenueDailyRow[]
}

// pp2_hotel.api.reports.get_guest_ledger (bare array response) and
// pp2_hotel.api.reports.get_outstanding_balances (bare array response, same
// enriched shape plus checkout_override_reason -- see below). Shares its
// stay/guest/folio fields with FolioDetail/StayListRow, but is its own type
// since it's a distinct backend projection.
export interface GuestLedgerRow {
	name: string
	stay: string
	guest: string
	status: FolioStatus
	total: number
	paid_amount: number
	balance: number
	currency: string
	guest_name: string
	room_number: string
	arrival: string
	departure: string
}

// pp2_hotel.api.reports.get_outstanding_balances (bare array response).
// Deliberately includes Closed folios with a nonzero balance (accounts
// receivable) -- see OutstandingBalances.vue.
export interface OutstandingBalanceRow extends GuestLedgerRow {
	checkout_override_reason: string | null
}

// pp2_hotel.api.reports.get_payment_report -- one payment row.
export interface PaymentReportRow {
	name: string
	posting_date: string
	amount: number
	payment_method: PaymentMethod
	reference: string | null
	folio: string
	guest: string
	stay: string
	currency: string
	guest_name: string
	room_number: string
}

// pp2_hotel.api.reports.get_payment_report -- one entry in the by-method
// summary tile row.
export interface PaymentReportByMethod {
	payment_method: PaymentMethod
	total: number
}

// pp2_hotel.api.reports.get_payment_report
export interface PaymentReport {
	start_date: string
	end_date: string
	payments: PaymentReportRow[]
	total: number
	by_method: PaymentReportByMethod[]
}

// pp2_hotel.api.reports.get_housekeeping_report
export interface HousekeepingReport {
	start_date: string
	end_date: string
	total_tasks: number
	pending_tasks: number
	in_progress_tasks: number
	completed_tasks: number
	inspections_passed: number
	inspections_failed: number
	pass_rate: number
	avg_turnaround_minutes: number | null
}

// Maintenance Request doctype's own status/priority fields.
export type MaintenanceRequestStatus = 'Open' | 'In Progress' | 'Resolved' | 'Cancelled'
export type MaintenancePriority = 'Low' | 'Normal' | 'High' | 'Urgent'

// pp2_hotel.api.maintenance.get_maintenance_board (bare array response) --
// active (Open/In Progress) tickets only, same active-only-board shape as
// HousekeepingBoardRow, but with no orphan-room safety net: a Maintenance
// Request is the only writer of a room's `Maintenance` status, so there's no
// equivalent "room ended up Maintenance with no ticket at all" case to guard.
export interface MaintenanceBoardRow {
	name: string
	room: string
	room_number: string
	status: MaintenanceRequestStatus
	priority: MaintenancePriority
	assigned_to: string | null
	reported_date: string
}

// Maintenance Request doctype -- plain CRUD via createListResource
// (MaintenanceRequests.vue's full history list, unlike the Dashboard's
// active-only board).
export interface MaintenanceRequest {
	name: string
	room: string
	status: MaintenanceRequestStatus
	priority: MaintenancePriority
	description: string
	reported_by: string | null
	assigned_to: string | null
	reported_date: string
	resolved_date: string | null
	resolution_notes: string | null
	cancellation_reason: string | null
}

// Service Order doctype's own status field.
export type ServiceOrderStatus = 'Pending' | 'Delivered' | 'Cancelled'

// pp2_hotel.api.service_orders.get_service_board (bare array response) --
// active (Pending) orders only, same active-only-board shape as
// HousekeepingBoardRow/MaintenanceBoardRow.
export interface ServiceOrderBoardRow {
	name: string
	room: string
	room_number: string
	service_type: string
	description: string
	qty: number
	rate: number
	amount: number
	ordered_at: string
}

// pp2_hotel.api.front_desk.search_guests (bare array response) -- `room`/
// `stay` set means currently checked in; `reservation` set (independently --
// a guest is never both at once, see search_guests()'s own not-yet-
// checked-in filter) means an upcoming Confirmed booking.
export interface GuestSearchResult {
	name: string
	guest_name: string
	phone: string | null
	email: string | null
	stay: string | null
	room: string | null
	room_number: string | null
	reservation: string | null
	reservation_arrival: string | null
}
