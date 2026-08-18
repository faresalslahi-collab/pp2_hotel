<script setup lang="ts">
// Same shape/wiring as Departures.vue -- get_in_house returns every
// currently checked-in stay (not just today's departures) but the row shape
// and the "click a row to open RoomDrawer" behavior are identical.
import { computed, ref } from 'vue'
import { createResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import RoomDrawer from '@/components/hotel/RoomDrawer.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import type { StayListRow } from '@/types/hotel'

const inHouseResource = createResource({
	url: 'pp2_hotel.api.front_desk.get_in_house',
	params: {},
	auto: true,
})

const rows = computed<StayListRow[]>(() => inHouseResource.data ?? [])

const columns: DataTableColumn[] = [
	{ key: 'guest_name', label: 'Guest' },
	{ key: 'room_number', label: 'Room' },
	{ key: 'arrival', label: 'Arrival' },
	{ key: 'departure', label: 'Departure' },
	{ key: 'balance', label: 'Balance' },
]

const drawerOpen = ref(false)
const drawerRoomName = ref<string | null>(null)

function openRoom(row: Record<string, any>) {
	drawerRoomName.value = row.room
	drawerOpen.value = true
}

function closeDrawer() {
	drawerOpen.value = false
}

// A checkout from within this drawer removes the guest from the in-house
// list -- reload so the row doesn't linger stale (same reasoning as
// Dashboard.vue's RoomGrid reload on this same event).
function onCheckedOut() {
	inHouseResource.reload()
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">In-House Guests</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Every guest currently checked in.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="inHouseResource.loading"
			:error="inHouseResource.error"
			row-clickable
			empty-title="No guests in-house"
			empty-description="There are no guests currently checked in."
			@retry="inHouseResource.reload()"
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
