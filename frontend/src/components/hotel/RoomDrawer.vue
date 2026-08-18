<script setup lang="ts">
// A custom fixed-panel + Teleport transition, not frappe-ui's <Dialog> --
// Dialog centers a modal card, and fighting its layout to get a full-height
// right-edge slide-over with a scrolling body and a pinned header/footer
// would have meant overriding most of its internals anyway. Committing to
// one approach per the spec rather than half-building both.
import { computed, ref, watch } from 'vue'
import { createResource, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { X } from 'lucide-vue-next'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import AddChargeDialog from '@/components/hotel/AddChargeDialog.vue'
import AddPaymentDialog from '@/components/hotel/AddPaymentDialog.vue'
import CheckoutDialog from '@/components/hotel/CheckoutDialog.vue'
import MoveRoomDialog from '@/components/hotel/MoveRoomDialog.vue'
import ReportIssueDialog from '@/components/hotel/ReportIssueDialog.vue'
import OrderServiceDialog from '@/components/hotel/OrderServiceDialog.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import type { RoomDetail, CheckoutResult, RoomMovementResult } from '@/types/hotel'

const props = defineProps<{ open: boolean; roomName: string | null }>()
// 'checked-out'/'moved'/'reported' bubble up so pages that embed this drawer
// (Dashboard's RoomGrid, primarily -- see Dashboard.vue) know to refresh
// their own room list: a checkout, a room move, and a Report Issue on a
// vacant room (-> Maintenance) can all change room status outside of this
// drawer's own detailResource.
const emit = defineEmits<{ close: []; 'checked-out': []; moved: []; reported: [] }>()
const router = useRouter()

const detailResource = createResource({
	url: 'pp2_hotel.api.rooms.get_room_detail',
	params: { room: props.roomName ?? '' },
	auto: false,
})

// Re-fetch whenever the drawer opens for a (possibly new) room -- watching
// the pair together rather than just roomName means re-opening the drawer
// for the same room (e.g. closed then re-clicked) still gets a fresh fetch.
watch(
	() => [props.open, props.roomName] as const,
	([open, roomName]) => {
		if (open && roomName) {
			detailResource.update({ params: { room: roomName } })
			detailResource.reload()
		}
	},
	{ immediate: true },
)

const detail = computed<RoomDetail | null>(() => detailResource.data ?? null)

// Guest Profile still has no backing flow this phase -- rendered disabled
// with a "Coming soon" tooltip, untouched from Phase 2. Check-out / Add
// Charge / Payment / View Folio / Move Room are real as of Phase 3/6; see
// the per-action enabled computeds and open*/goToFolio handlers below.
const canCheckOut = computed(() => detail.value?.stay?.status === 'Checked In')
// Same guard as Check-out -- a room can only be moved mid-stay, and this
// drawer's own get_room_detail only ever surfaces a stay in "Checked In" or
// "Reserved" status (see canFolioActions's comment below).
const canMoveRoom = computed(() => detail.value?.stay?.status === 'Checked In')

// get_room_detail's own stay lookup only ever surfaces a stay with status
// "Checked In" or "Reserved" (see pp2_hotel.services.rooms.get_room_detail);
// a folio is only ever Closed by checkout, which happens exactly when that
// same stay flips to "Checked Out" -- a status this endpoint never returns.
// So `detail.folio` being present already guarantees it's Open; there's no
// separate folio-status field to check here.
const canFolioActions = computed(() => Boolean(detail.value?.folio))
const canViewFolio = computed(() => Boolean(detail.value?.folio))

function actionButtonClass(enabled: boolean): string {
	return enabled
		? 'w-full rounded-app-sm border border-app-border bg-app-bg px-3 py-2 text-[13px] font-medium text-app-text transition-colors hover:border-app-primary hover:bg-app-surface'
		: 'w-full cursor-not-allowed rounded-app-sm border border-app-border bg-app-bg px-3 py-2 text-[13px] font-medium text-app-disabled'
}

const checkoutOpen = ref(false)
const addChargeOpen = ref(false)
const addPaymentOpen = ref(false)
const moveRoomOpen = ref(false)
const reportIssueOpen = ref(false)
const orderServiceOpen = ref(false)

function openCheckout() {
	if (!canCheckOut.value) return
	checkoutOpen.value = true
}
function openMoveRoom() {
	if (!canMoveRoom.value) return
	moveRoomOpen.value = true
}
function openAddCharge() {
	if (!canFolioActions.value) return
	addChargeOpen.value = true
}
function openAddPayment() {
	if (!canFolioActions.value) return
	addPaymentOpen.value = true
}
function openOrderService() {
	if (!canFolioActions.value) return
	orderServiceOpen.value = true
}
function goToFolio() {
	const folioName = detail.value?.folio?.name
	if (!folioName) return
	emit('close')
	router.push(`/billing/folios/${folioName}`)
}

function onCharged() {
	toast.success('Charge added.')
	detailResource.reload()
}
function onPaid() {
	toast.success('Payment recorded.')
	detailResource.reload()
}
function onCheckedOut(result: CheckoutResult) {
	// Invoice generation is best-effort at checkout (see CheckoutResult's own
	// comment in types/hotel.ts) -- surface a distinct, non-blocking warning
	// rather than a plain success toast when it failed, so staff know a
	// manual retry from Folio Detail is needed.
	if (result.invoice_error) {
		toast.warning('Checked out. Invoice generation failed -- generate it manually from the Folio.')
	} else {
		toast.success('Guest checked out.')
	}
	// The room's identity in this drawer is now stale (Occupied -> Dirty), so
	// close it rather than reload-in-place -- and let the embedding page
	// (Dashboard's RoomGrid) know to refresh via the 'checked-out' emit.
	emit('checked-out')
	emit('close')
}
function onMoved(_result: RoomMovementResult) {
	// Same reasoning as onCheckedOut -- this room (the one the drawer is
	// showing) is now the *vacated* side of the move (Occupied -> Dirty), so
	// its identity here is stale too. MoveRoomDialog already toasts the
	// financial-impact summary itself.
	emit('moved')
	emit('close')
}
function onReported() {
	// Unlike checkout/move, this room's own identity isn't necessarily stale
	// -- an Occupied room stays Occupied (see services/maintenance.py) -- so
	// reload in place rather than force-closing, same as Add Charge/Payment.
	toast.success('Issue reported.')
	emit('reported')
	detailResource.reload()
}
function onOrdered() {
	// Doesn't change room status or the folio (the order is Pending, not
	// billed yet -- see services/service_orders.py), so no reload needed;
	// OrderServiceDialog.vue closes itself.
	toast.success('Order placed.')
}
</script>

<template>
	<Teleport to="body">
		<Transition name="pp2-slide-backdrop">
			<div v-if="open" class="fixed inset-0 z-40 bg-black/40" @click="emit('close')" />
		</Transition>
		<Transition name="pp2-slide-panel">
			<aside
				v-if="open"
				class="fixed inset-y-0 right-0 z-40 flex w-full max-w-md flex-col border-l border-app-border bg-app-surface shadow-xl"
				role="dialog"
				aria-modal="true"
			>
				<div class="flex h-14 shrink-0 items-center justify-between border-b border-app-border px-4">
					<p class="text-[14px] font-semibold leading-[20px] text-app-text">Room Details</p>
					<button
						type="button"
						class="text-app-muted hover:text-app-text"
						aria-label="Close room details"
						@click="emit('close')"
					>
						<X :size="20" />
					</button>
				</div>

				<div class="flex-1 overflow-y-auto p-4">
					<LoadingState v-if="detailResource.loading && !detailResource.data" :rows="6" />
					<ErrorState
						v-else-if="detailResource.error"
						title="Couldn't load room details"
						description="Something went wrong while loading this room."
						@retry="detailResource.reload()"
					/>
					<div v-else-if="detail" class="space-y-6">
						<div class="flex items-start justify-between gap-2">
							<div class="min-w-0">
								<p class="truncate text-[20px] font-semibold leading-[28px] text-app-text">
									{{ detail.room.room_number }}
								</p>
								<p class="truncate text-[13px] leading-[16px] text-app-muted">
									{{ detail.room.room_type }} &middot; {{ detail.room.floor }}
								</p>
							</div>
							<StatusBadge :status="detail.room.status" />
						</div>

						<div v-if="detail.stay" class="space-y-3 rounded-app-md border border-app-border p-3">
							<p class="text-[11px] font-semibold uppercase leading-[16px] tracking-wide text-app-muted">Guest</p>
							<p class="text-[14px] font-medium leading-[20px] text-app-text">{{ detail.stay.guest_name }}</p>
							<div class="grid grid-cols-2 gap-3">
								<div>
									<p class="text-[11px] uppercase leading-[16px] text-app-muted">Check-in</p>
									<p class="text-[13px] leading-[16px] text-app-text">{{ formatDate(detail.stay.arrival) }}</p>
								</div>
								<div>
									<p class="text-[11px] uppercase leading-[16px] text-app-muted">Check-out</p>
									<p class="text-[13px] leading-[16px] text-app-text">{{ formatDate(detail.stay.departure) }}</p>
								</div>
							</div>
							<div v-if="detail.folio" class="flex items-center justify-between border-t border-app-border pt-3">
								<p class="text-[13px] leading-[16px] text-app-muted">Balance</p>
								<p
									class="text-[15px] font-semibold leading-[20px]"
									:class="detail.folio.balance > 0 ? 'text-app-danger' : 'text-app-success'"
								>
									{{ formatCurrency(detail.folio.balance, detail.folio.currency) }}
								</p>
							</div>
						</div>
						<EmptyState
							v-else
							title="No active stay"
							description="This room has no guest currently checked in or reserved."
						/>

						<div>
							<p class="mb-2 text-[11px] font-semibold uppercase leading-[16px] tracking-wide text-app-muted">
								Actions
							</p>
							<div class="grid grid-cols-2 gap-2">
								<button
									type="button"
									:disabled="!canCheckOut"
									:class="actionButtonClass(canCheckOut)"
									@click="openCheckout"
								>
									Check-out
								</button>

								<button
									type="button"
									:disabled="!canMoveRoom"
									:class="actionButtonClass(canMoveRoom)"
									@click="openMoveRoom"
								>
									Move Room
								</button>

								<button
									type="button"
									:disabled="!canFolioActions"
									:class="actionButtonClass(canFolioActions)"
									@click="openAddCharge"
								>
									Add Charge
								</button>

								<button
									type="button"
									:disabled="!canFolioActions"
									:class="actionButtonClass(canFolioActions)"
									@click="openAddPayment"
								>
									Payment
								</button>

								<button
									type="button"
									:disabled="!canViewFolio"
									:class="actionButtonClass(canViewFolio)"
									@click="goToFolio"
								>
									View Folio
								</button>

								<div class="group relative">
									<button
										type="button"
										disabled
										class="w-full cursor-not-allowed rounded-app-sm border border-app-border bg-app-bg px-3 py-2 text-[13px] font-medium text-app-disabled"
									>
										Guest Profile
									</button>
									<span
										role="tooltip"
										class="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 -translate-x-1/2 whitespace-nowrap rounded-app-sm bg-app-text px-2 py-1 text-xs text-white opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100"
									>
										Coming soon
									</span>
								</div>

								<button
									type="button"
									:class="actionButtonClass(true)"
									@click="reportIssueOpen = true"
								>
									Report Issue
								</button>

								<button
									type="button"
									:disabled="!canFolioActions"
									:class="actionButtonClass(canFolioActions)"
									@click="openOrderService"
								>
									Order Service
								</button>
							</div>
						</div>
					</div>
				</div>
			</aside>
		</Transition>
	</Teleport>

	<CheckoutDialog
		:open="checkoutOpen"
		:stay="detail?.stay?.name ?? null"
		:folio="detail?.folio?.name ?? null"
		@close="checkoutOpen = false"
		@checked-out="onCheckedOut"
	/>
	<AddChargeDialog
		:open="addChargeOpen"
		:folio="detail?.folio?.name ?? null"
		@close="addChargeOpen = false"
		@charged="onCharged"
	/>
	<AddPaymentDialog
		:open="addPaymentOpen"
		:folio="detail?.folio?.name ?? null"
		@close="addPaymentOpen = false"
		@paid="onPaid"
	/>
	<MoveRoomDialog
		:open="moveRoomOpen"
		:stay="detail?.stay?.name ?? null"
		:property="detail?.room?.property ?? null"
		:currency="detail?.folio?.currency ?? ''"
		@close="moveRoomOpen = false"
		@moved="onMoved"
	/>
	<ReportIssueDialog
		:open="reportIssueOpen"
		:room="detail?.room?.name ?? null"
		@close="reportIssueOpen = false"
		@reported="onReported"
	/>
	<OrderServiceDialog
		:open="orderServiceOpen"
		:folio="detail?.folio?.name ?? null"
		:currency="detail?.folio?.currency ?? ''"
		@close="orderServiceOpen = false"
		@ordered="onOrdered"
	/>
</template>

<style scoped>
.pp2-slide-backdrop-enter-active,
.pp2-slide-backdrop-leave-active {
	transition: opacity 150ms ease;
}
.pp2-slide-backdrop-enter-from,
.pp2-slide-backdrop-leave-to {
	opacity: 0;
}

.pp2-slide-panel-enter-active,
.pp2-slide-panel-leave-active {
	transition: transform 150ms ease;
}
.pp2-slide-panel-enter-from,
.pp2-slide-panel-leave-to {
	transform: translateX(100%);
}
</style>
