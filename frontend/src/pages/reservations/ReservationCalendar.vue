<script setup lang="ts">
// Visual rooms x dates timeline -- one component serving both
// /front-desk/reservation-calendar and /reservations/calendar (same
// destination reachable from two sidebar sections, same "Front Desk
// Dashboard is also just Dashboard.vue" duplication nav.ts already has
// elsewhere). Reads pp2_hotel.api.front_desk.get_reservation_calendar, a
// pure aggregation with no new doctype -- every Confirmed Reservation Room
// line touching a 14-day window, plus the full room list so an empty room
// still gets a row. A booking bar is colored by the same semantics the
// room-status palette already carries: room-reserved (upcoming, not yet
// checked in) vs. room-occupied (checked_in -- in-house right now).
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { addDaysIso, todayIso } from '@/utils/dates'
import { formatDate } from '@/utils/format'

const router = useRouter()

const WINDOW_DAYS = 14
const windowStart = ref(todayIso())

const calendarResource = createResource({
	url: 'pp2_hotel.api.front_desk.get_reservation_calendar',
	params: { start_date: windowStart.value, end_date: addDaysIso(windowStart.value, WINDOW_DAYS - 1) },
	auto: true,
})

watch(windowStart, (value) => {
	calendarResource.reload({ start_date: value, end_date: addDaysIso(value, WINDOW_DAYS - 1) })
})

function shiftWindow(days: number) {
	windowStart.value = addDaysIso(windowStart.value, days)
}
function goToToday() {
	windowStart.value = todayIso()
}

const days = computed<string[]>(() => {
	const start = windowStart.value
	return Array.from({ length: WINDOW_DAYS }, (_, i) => addDaysIso(start, i))
})

function daysBetween(fromIso: string, toIso: string): number {
	const from = new Date(`${fromIso}T00:00:00`)
	const to = new Date(`${toIso}T00:00:00`)
	return Math.round((to.getTime() - from.getTime()) / 86400000)
}

interface BookingBar {
	reservation: string
	guestName: string
	checkedIn: boolean
	// Relative to the per-room bar container's own nested grid (WINDOW_DAYS
	// columns, 1-indexed lines 1..WINDOW_DAYS+1) -- NOT the outer room-list
	// grid's column numbering, which has an extra leading label column.
	gridColumnStart: number
	gridColumnEnd: number
}

const rooms = computed(() => calendarResource.data?.rooms ?? [])
const bookings = computed(() => calendarResource.data?.bookings ?? [])

function barsForRoom(roomName: string): BookingBar[] {
	const start = windowStart.value
	return bookings.value
		.filter((b: Record<string, any>) => b.room === roomName)
		.map((b: Record<string, any>): BookingBar => {
			// Clamp to the visible window -- a booking spanning past either
			// edge still renders, just cut off at the edge column.
			const startOffset = Math.max(0, daysBetween(start, b.arrival))
			const endOffset = Math.min(WINDOW_DAYS, daysBetween(start, b.departure))
			return {
				reservation: b.reservation,
				guestName: b.guest_name,
				checkedIn: b.checked_in,
				gridColumnStart: startOffset + 1,
				gridColumnEnd: Math.max(startOffset + 2, endOffset + 1),
			}
		})
		.filter((bar: BookingBar) => bar.gridColumnStart <= WINDOW_DAYS)
}

function openReservation(reservation: string) {
	router.push(`/reservations/${reservation}`)
}
</script>

<template>
	<PageContainer>
		<div class="mb-6 flex flex-wrap items-center justify-between gap-3">
			<div>
				<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Reservation Calendar</h1>
				<p class="text-[13px] leading-[16px] text-app-muted">
					{{ formatDate(days[0]) }} &ndash; {{ formatDate(days[days.length - 1]) }}
				</p>
			</div>
			<div class="flex gap-2">
				<Button variant="outline" @click="shiftWindow(-WINDOW_DAYS)">&larr; Previous</Button>
				<Button variant="outline" @click="goToToday">Today</Button>
				<Button variant="outline" @click="shiftWindow(WINDOW_DAYS)">Next &rarr;</Button>
			</div>
		</div>

		<div class="mb-4 flex items-center gap-4 text-[12px] leading-[16px] text-app-muted">
			<span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-app-sm bg-app-room-reserved" /> Upcoming</span>
			<span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-app-sm bg-app-room-occupied" /> In-house</span>
		</div>

		<LoadingState v-if="calendarResource.loading && !calendarResource.data" :rows="8" />
		<ErrorState
			v-else-if="calendarResource.error"
			title="Couldn't load the calendar"
			description="Something went wrong while loading the reservation calendar."
			@retry="calendarResource.reload()"
		/>
		<EmptyState v-else-if="!rooms.length" title="No rooms configured" description="There are no rooms to show on the calendar." />
		<div v-else class="overflow-x-auto rounded-app-md border border-app-border bg-app-surface">
			<div
				class="grid min-w-[900px]"
				:style="{ gridTemplateColumns: `180px repeat(${WINDOW_DAYS}, minmax(64px, 1fr))` }"
			>
				<div class="sticky left-0 z-10 border-b border-r border-app-border bg-app-surface p-2 text-[11px] font-semibold uppercase text-app-muted">
					Room
				</div>
				<div
					v-for="day in days"
					:key="day"
					class="border-b border-app-border p-2 text-center text-[11px] font-semibold uppercase text-app-muted"
				>
					{{ formatDate(day) }}
				</div>

				<template v-for="room in rooms" :key="room.name">
					<div class="sticky left-0 z-10 border-b border-r border-app-border bg-app-surface p-2">
						<p class="truncate text-[13px] font-medium text-app-text">{{ room.room_number }}</p>
						<p class="truncate text-[11px] text-app-muted">{{ room.room_type_name }}</p>
					</div>
					<div
						class="relative col-span-full grid border-b border-app-border"
						:style="{ gridTemplateColumns: `repeat(${WINDOW_DAYS}, minmax(64px, 1fr))`, gridColumn: `2 / span ${WINDOW_DAYS}` }"
					>
						<button
							v-for="bar in barsForRoom(room.name)"
							:key="bar.reservation"
							type="button"
							class="my-1.5 truncate rounded-app-sm px-2 py-1 text-left text-[11px] font-medium text-white transition-opacity hover:opacity-90"
							:class="bar.checkedIn ? 'bg-app-room-occupied' : 'bg-app-room-reserved'"
							:style="{ gridColumn: `${bar.gridColumnStart} / ${bar.gridColumnEnd}` }"
							@click="openReservation(bar.reservation)"
						>
							{{ bar.guestName }}
						</button>
					</div>
				</template>
			</div>
		</div>
	</PageContainer>
</template>
