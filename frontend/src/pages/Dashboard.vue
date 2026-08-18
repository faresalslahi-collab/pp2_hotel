<script setup lang="ts">
// The Front Desk Dashboard -- the hero screen of this phase. KPI row +
// RoomGrid + RoomDrawer wiring, per the product spec's section 7.
import { computed, ref } from 'vue'
import { createResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import RoomGrid from '@/components/hotel/RoomGrid.vue'
import RoomDrawer from '@/components/hotel/RoomDrawer.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { formatCurrency } from '@/utils/format'
import type { FrontDeskKpis, RoomGridItem } from '@/types/hotel'

const kpisResource = createResource({
	url: 'pp2_hotel.api.dashboard.get_front_desk_kpis',
	params: {},
	auto: true,
})

const kpis = computed<FrontDeskKpis | null>(() => kpisResource.data ?? null)

interface KpiTile {
	label: string
	value: string
	tone?: 'warning' | 'danger'
}

// Dirty Rooms / Out of Order get a warning/danger tint when non-zero --
// everything else stays neutral. Order matches the product spec's KPI row
// verbatim.
const kpiTiles = computed<KpiTile[]>(() => {
	const data = kpis.value
	if (!data) return []
	return [
		{ label: "Today's Arrivals", value: String(data.arrivals_today) },
		{ label: "Today's Departures", value: String(data.departures_today) },
		{ label: 'In-House Guests', value: String(data.in_house_guests) },
		{ label: 'Available Rooms', value: String(data.available_rooms) },
		{ label: 'Occupied Rooms', value: String(data.occupied_rooms) },
		{
			label: 'Dirty Rooms',
			value: String(data.dirty_rooms),
			tone: data.dirty_rooms > 0 ? 'warning' : undefined,
		},
		{
			label: 'Out of Order',
			value: String(data.out_of_order_rooms),
			tone: data.out_of_order_rooms > 0 ? 'danger' : undefined,
		},
		{ label: "Today's Revenue", value: formatCurrency(data.todays_revenue, data.currency) },
	]
})

const selectedRoom = ref<RoomGridItem | null>(null)
const drawerOpen = ref(false)
const roomGrid = ref<InstanceType<typeof RoomGrid> | null>(null)

function openRoom(room: RoomGridItem) {
	selectedRoom.value = room
	drawerOpen.value = true
}

function closeDrawer() {
	drawerOpen.value = false
}

// RoomDrawer emits 'checked-out' when a checkout succeeds -- the room's
// status just changed (Occupied -> Dirty) outside of RoomGrid's own
// roomsResource, so it needs an explicit reload. RoomGrid.vue already
// exposes exactly this via defineExpose({ reload }).
function onCheckedOut() {
	roomGrid.value?.reload()
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Front Desk Dashboard</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Today's arrivals, departures, and room status at a glance.
			</p>
		</div>

		<LoadingState v-if="kpisResource.loading && !kpisResource.data" :rows="4" />
		<ErrorState
			v-else-if="kpisResource.error"
			title="Couldn't load dashboard stats"
			description="Something went wrong while loading today's numbers."
			@retry="kpisResource.reload()"
		/>
		<div v-else-if="kpis" class="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
			<div v-for="tile in kpiTiles" :key="tile.label" class="rounded-app-md border border-app-border bg-app-surface p-3">
				<p class="truncate text-[12px] leading-[16px] text-app-muted">{{ tile.label }}</p>
				<p
					class="mt-1 truncate text-[20px] font-semibold leading-[28px]"
					:class="tile.tone === 'danger' ? 'text-app-danger' : tile.tone === 'warning' ? 'text-app-warning' : 'text-app-text'"
				>
					{{ tile.value }}
				</p>
			</div>
		</div>

		<div>
			<h2 class="mb-3 text-[15px] font-semibold leading-[20px] text-app-text">Room Grid</h2>
			<RoomGrid ref="roomGrid" @select-room="openRoom" />
		</div>

		<RoomDrawer
			:open="drawerOpen"
			:room-name="selectedRoom?.name ?? null"
			@close="closeDrawer"
			@checked-out="onCheckedOut"
			@moved="onCheckedOut"
			@reported="onCheckedOut"
		/>
	</PageContainer>
</template>
