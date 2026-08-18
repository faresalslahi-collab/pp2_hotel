<script setup lang="ts">
// Row click opens the existing RoomDrawer for that row's room -- same
// drawer-state wiring Dashboard.vue uses for RoomGrid, just triggered from a
// table row instead of a room card.
import { computed, ref } from 'vue'
import { createResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import RoomDrawer from '@/components/hotel/RoomDrawer.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import type { StayListRow } from '@/types/hotel'

const departuresResource = createResource({
	url: 'pp2_hotel.api.front_desk.get_departures_today',
	params: {},
	auto: true,
})

const rows = computed<StayListRow[]>(() => departuresResource.data ?? [])

const columns: DataTableColumn[] = [
	{ key: 'guest_name', label: 'Guest' },
	{ key: 'room_number', label: 'Room' },
	{ key: 'arrival', label: 'Arrival' },
	{ key: 'departure', label: 'Departure' },
	{ key: 'balance', label: 'Balance' },
]

const drawerOpen = ref(false)
const drawerRoomName = ref<string | null>(null)

// DataTable emits its row as a loosely-typed Record (see DataTable.vue's doc
// comment on why it doesn't share a generic across the four list pages).
function openRoom(row: Record<string, any>) {
	drawerRoomName.value = row.room
	drawerOpen.value = true
}

function closeDrawer() {
	drawerOpen.value = false
}

// A checkout from within this drawer removes the guest from today's
// departures -- reload so the row doesn't linger stale (same reasoning as
// Dashboard.vue's RoomGrid reload on this same event).
function onCheckedOut() {
	departuresResource.reload()
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Departures</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Guests expected to check out today.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="departuresResource.loading"
			:error="departuresResource.error"
			row-clickable
			empty-title="No departures today"
			empty-description="There are no guests checking out today."
			@retry="departuresResource.reload()"
			@row-click="openRoom"
		>
			<template #cell-arrival="{ row }">{{ formatDate(row.arrival) }}</template>
			<template #cell-departure="{ row }">{{ formatDate(row.departure) }}</template>
			<template #cell-balance="{ row }">{{ formatCurrency(row.balance, row.currency) }}</template>
		</DataTable>

		<RoomDrawer
			:open="drawerOpen"
			:room-name="drawerRoomName"
			@close="closeDrawer"
			@checked-out="onCheckedOut"
			@moved="onCheckedOut"
			@reported="onCheckedOut"
		/>
	</PageContainer>
</template>
