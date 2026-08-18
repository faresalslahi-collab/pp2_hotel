<script setup lang="ts">
// Shows the Guest ID rather than the guest's name in the Guest column -- the
// contract's own note for this list flags both options as acceptable for a
// first pass ("either add a second lookup... or accept showing the Guest ID
// ... your call, whichever is less code"). A second batched Guest lookup +
// dedupe/join logic is real complexity for a column that's cosmetic; showing
// the ID is correct today and is a one-line follow-up to upgrade later.
import { useRouter } from 'vue-router'
import { createListResource, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import ReservationStatusPill from '@/components/hotel/ReservationStatusPill.vue'
import { formatDate } from '@/utils/format'

const router = useRouter()

const reservations = createListResource({
	doctype: 'Reservation',
	fields: ['name', 'guest', 'property', 'arrival', 'departure', 'status', 'source', 'creation'],
	orderBy: 'creation desc',
	pageLength: 100,
	auto: true,
})

const columns: DataTableColumn[] = [
	{ key: 'name', label: 'Reservation #' },
	{ key: 'guest', label: 'Guest' },
	{ key: 'arrival', label: 'Arrival' },
	{ key: 'departure', label: 'Departure' },
	{ key: 'status', label: 'Status' },
	{ key: 'source', label: 'Source' },
]

function openReservation(row: Record<string, any>) {
	router.push(`/reservations/${row.name}`)
}
</script>

<template>
	<PageContainer>
		<div class="mb-6 flex items-center justify-between gap-3">
			<div>
				<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">All Reservations</h1>
				<p class="text-[13px] leading-[16px] text-app-muted">Every reservation on the books.</p>
			</div>
			<Button variant="solid" route="/reservations/new">New Reservation</Button>
		</div>

		<DataTable
			:columns="columns"
			:rows="reservations.data ?? []"
			:loading="reservations.list.loading"
			:error="reservations.list.error"
			row-clickable
			empty-title="No reservations yet"
			empty-description="Reservations you create will show up here."
			@retry="reservations.reload()"
			@row-click="openReservation"
		>
			<template #cell-name="{ row }">
				<span class="font-medium text-app-text">{{ row.name }}</span>
			</template>
			<template #cell-arrival="{ row }">{{ formatDate(row.arrival) }}</template>
			<template #cell-departure="{ row }">{{ formatDate(row.departure) }}</template>
			<template #cell-status="{ row }">
				<ReservationStatusPill :status="row.status" />
			</template>
		</DataTable>
	</PageContainer>
</template>
