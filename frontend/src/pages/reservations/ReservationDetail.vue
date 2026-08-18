<script setup lang="ts">
// Not nav-tree-generated -- wired directly into router/index.ts's appRoutes
// alongside Dashboard. `name` arrives as a route prop (props: true); since
// vue-router reuses this component instance across reservation-to-
// reservation navigation (same route record, different :name), the doc
// resource's `.name` is re-pointed and reloaded on change rather than
// re-creating the resource, which is what createDocumentResource's own
// [doctype, name] cache keys off of anyway.
import { computed, ref, watch } from 'vue'
import { createDocumentResource, createListResource, createResource, Button, toast } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ReasonPromptDialog from '@/components/ui/ReasonPromptDialog.vue'
import ReservationStatusPill from '@/components/hotel/ReservationStatusPill.vue'
import CheckInDialog from '@/components/hotel/CheckInDialog.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import { getErrorMessage } from '@/utils/errors'
import type { Reservation, ReservationRoom, CheckInResult } from '@/types/hotel'

const props = defineProps<{ name: string }>()

const doc = createDocumentResource({ doctype: 'Reservation', name: props.name })

watch(
	() => props.name,
	(newName) => {
		if (!newName || newName === doc.name) return
		doc.name = newName
		doc.reload()
	},
)

const reservation = computed<Reservation | null>(() => doc.doc)

// Reservation/ReservationRoom carry no currency field of their own -- the
// Property doctype's default_currency is the source of truth (same lookup
// Availability.vue does), so this fetches it once the reservation's
// property is known, purely to label the Rate column correctly.
const propertyResource = createListResource({
	doctype: 'Property',
	fields: ['name', 'default_currency'],
	filters: {},
	auto: false,
})
watch(
	() => reservation.value?.property,
	(propertyName) => {
		if (!propertyName) return
		propertyResource.update({ filters: { name: propertyName } })
		propertyResource.reload()
	},
	{ immediate: true },
)
const currency = computed<string>(() => propertyResource.data?.[0]?.default_currency ?? '')

const actionError = ref<string | null>(null)

const confirmAction = createResource({
	url: 'pp2_hotel.api.reservations.confirm_reservation',
	method: 'POST',
	auto: false,
})
async function confirmReservation() {
	actionError.value = null
	try {
		await confirmAction.submit({ reservation: props.name })
		toast.success('Reservation confirmed.')
		doc.reload()
	} catch (error) {
		actionError.value = getErrorMessage(error, 'Could not confirm this reservation.')
	}
}

const cancelDialogOpen = ref(false)
const cancelAction = createResource({
	url: 'pp2_hotel.api.reservations.cancel_reservation',
	method: 'POST',
	auto: false,
})
async function onCancelConfirm(reason: string) {
	actionError.value = null
	try {
		await cancelAction.submit({ reservation: props.name, reason })
		toast.success('Reservation cancelled.')
		cancelDialogOpen.value = false
		doc.reload()
	} catch (error) {
		actionError.value = getErrorMessage(error, 'Could not cancel this reservation.')
	}
}

const noShowDialogOpen = ref(false)
const noShowAction = createResource({
	url: 'pp2_hotel.api.reservations.mark_no_show',
	method: 'POST',
	auto: false,
})
async function onNoShowConfirm(reason: string) {
	actionError.value = null
	try {
		await noShowAction.submit({ reservation: props.name, reason })
		toast.success('Reservation marked as no-show.')
		noShowDialogOpen.value = false
		doc.reload()
	} catch (error) {
		actionError.value = getErrorMessage(error, 'Could not mark this reservation as a no-show.')
	}
}

const checkInOpen = ref(false)
const checkInLine = ref<ReservationRoom | null>(null)

function openCheckIn(line: ReservationRoom) {
	checkInLine.value = line
	checkInOpen.value = true
}
function closeCheckIn() {
	checkInOpen.value = false
}
function onCheckedIn(_result: CheckInResult) {
	toast.success('Guest checked in.')
	doc.reload()
}
</script>

<template>
	<PageContainer>
		<LoadingState v-if="doc.get.loading && !doc.doc" :rows="8" />
		<ErrorState
			v-else-if="doc.get.error"
			title="Couldn't load reservation"
			description="Something went wrong while loading this reservation."
			@retry="doc.reload()"
		/>
		<div v-else-if="reservation" class="space-y-6">
			<div class="flex flex-wrap items-start justify-between gap-3">
				<div>
					<div class="flex items-center gap-2">
						<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">{{ reservation.name }}</h1>
						<ReservationStatusPill :status="reservation.status" />
					</div>
					<p class="text-[13px] leading-[16px] text-app-muted">{{ reservation.guest }} &middot; {{ reservation.property }}</p>
				</div>
				<div class="flex gap-2">
					<Button v-if="reservation.status === 'Draft'" variant="solid" :loading="confirmAction.loading" @click="confirmReservation">
						Confirm
					</Button>
					<template v-if="reservation.status === 'Confirmed'">
						<Button variant="outline" @click="noShowDialogOpen = true">Mark No Show</Button>
						<Button variant="outline" theme="red" @click="cancelDialogOpen = true">Cancel</Button>
					</template>
				</div>
			</div>

			<p v-if="actionError" class="text-[13px] leading-[16px] text-app-danger">{{ actionError }}</p>

			<div class="grid grid-cols-2 gap-4 rounded-app-md border border-app-border bg-app-surface p-4 sm:grid-cols-4">
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Source</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ reservation.source }}</p>
				</div>
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Arrival</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ formatDate(reservation.arrival) }}</p>
				</div>
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Departure</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ formatDate(reservation.departure) }}</p>
				</div>
				<div v-if="reservation.notes" class="sm:col-span-4">
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Notes</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ reservation.notes }}</p>
				</div>
			</div>

			<div>
				<h2 class="mb-3 text-[15px] font-semibold leading-[20px] text-app-text">Rooms</h2>
				<div class="overflow-x-auto rounded-app-md border border-app-border bg-app-surface">
					<table class="w-full text-left text-[13px] leading-[16px]">
						<thead>
							<tr class="border-b border-app-border">
								<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Room Type</th>
								<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Room</th>
								<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Arrival</th>
								<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Departure</th>
								<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Rate</th>
								<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Status</th>
								<th class="px-4 py-2.5"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-app-border">
							<tr v-for="line in reservation.rooms ?? []" :key="line.name">
								<td class="px-4 py-2.5 text-app-text">{{ line.room_type }}</td>
								<td class="px-4 py-2.5">
									<span v-if="line.room" class="text-app-text">{{ line.room }}</span>
									<span v-else class="text-app-muted">Unassigned</span>
								</td>
								<td class="px-4 py-2.5 text-app-text">{{ formatDate(line.arrival) }}</td>
								<td class="px-4 py-2.5 text-app-text">{{ formatDate(line.departure) }}</td>
								<td class="px-4 py-2.5 text-app-text">{{ formatCurrency(line.rate, currency) }}</td>
								<td class="px-4 py-2.5">
									<span
										class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-app-sm px-2 py-0.5 text-xs font-medium leading-4"
										:class="line.hotel_stay ? 'bg-app-success-surface text-app-success' : 'bg-app-border/50 text-app-muted'"
									>
										<span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="line.hotel_stay ? 'bg-app-success' : 'bg-app-muted'" />
										{{ line.hotel_stay ? 'Checked In' : 'Not checked in' }}
									</span>
								</td>
								<td class="px-4 py-2.5 text-right">
									<Button
										v-if="!line.hotel_stay && reservation.status === 'Confirmed'"
										variant="outline"
										@click="openCheckIn(line)"
									>
										Check In
									</Button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>

		<ReasonPromptDialog
			:open="cancelDialogOpen"
			title="Cancel Reservation"
			description="This cannot be undone. The reason is recorded on the reservation."
			confirm-label="Cancel Reservation"
			:loading="cancelAction.loading"
			@close="cancelDialogOpen = false"
			@confirm="onCancelConfirm"
		/>
		<ReasonPromptDialog
			:open="noShowDialogOpen"
			title="Mark No Show"
			description="The reason is recorded on the reservation."
			confirm-label="Mark No Show"
			:loading="noShowAction.loading"
			@close="noShowDialogOpen = false"
			@confirm="onNoShowConfirm"
		/>
		<CheckInDialog
			:open="checkInOpen"
			:reservation="reservation?.name ?? null"
			:reservation-room="checkInLine?.name ?? null"
			:room-type="checkInLine?.room_type ?? null"
			:pre-assigned-room="checkInLine?.room ?? null"
			@close="closeCheckIn"
			@checked-in="onCheckedIn"
		/>
	</PageContainer>
</template>
