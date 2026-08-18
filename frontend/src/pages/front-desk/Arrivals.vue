<script setup lang="ts">
import { computed, ref } from 'vue'
import { createResource, toast, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import CheckInDialog from '@/components/hotel/CheckInDialog.vue'
import { formatDate } from '@/utils/format'
import type { ArrivalRow, CheckInResult } from '@/types/hotel'

const arrivalsResource = createResource({
	url: 'pp2_hotel.api.front_desk.get_arrivals_today',
	params: {},
	auto: true,
})

const rows = computed<ArrivalRow[]>(() => arrivalsResource.data ?? [])

const columns: DataTableColumn[] = [
	{ key: 'guest_name', label: 'Guest' },
	{ key: 'room_type_name', label: 'Room Type' },
	{ key: 'room', label: 'Room' },
	{ key: 'arrival', label: 'Arrival' },
	{ key: 'departure', label: 'Departure' },
	{ key: 'occupancy', label: 'Adults / Children' },
	{ key: 'action', label: '' },
]

const checkInOpen = ref(false)
// Loosely typed to match what DataTable's slot actually hands back (see
// DataTable.vue's doc comment) -- it's still every field of ArrivalRow at
// runtime, just not typed as such here.
const checkInRow = ref<Record<string, any> | null>(null)

function openCheckIn(row: Record<string, any>) {
	checkInRow.value = row
	checkInOpen.value = true
}

function closeCheckIn() {
	checkInOpen.value = false
}

function onCheckedIn(_result: CheckInResult) {
	toast.success('Guest checked in.')
	arrivalsResource.reload()
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Arrivals</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Guests expected to arrive today.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="arrivalsResource.loading"
			:error="arrivalsResource.error"
			empty-title="No arrivals today"
			empty-description="There are no reservations arriving today."
			@retry="arrivalsResource.reload()"
		>
			<template #cell-room="{ row }">
				<span v-if="row.room" class="text-app-text">{{ row.room }}</span>
				<span v-else class="text-app-muted">Unassigned</span>
			</template>
			<template #cell-arrival="{ row }">{{ formatDate(row.arrival) }}</template>
			<template #cell-departure="{ row }">{{ formatDate(row.departure) }}</template>
			<template #cell-occupancy="{ row }">{{ row.adults }} Adult{{ row.adults === 1 ? '' : 's' }}<template v-if="row.children">, {{ row.children }} Child{{ row.children === 1 ? '' : 'ren' }}</template></template>
			<template #cell-action="{ row }">
				<Button variant="outline" @click="openCheckIn(row)">Check In</Button>
			</template>
		</DataTable>

		<CheckInDialog
			:open="checkInOpen"
			:reservation="checkInRow?.reservation ?? null"
			:reservation-room="checkInRow?.reservation_room ?? null"
			:room-type="checkInRow?.room_type ?? null"
			:pre-assigned-room="checkInRow?.room ?? null"
			@close="closeCheckIn"
			@checked-in="onCheckedIn"
		/>
	</PageContainer>
</template>
