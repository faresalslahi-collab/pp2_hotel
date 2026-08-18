<script setup lang="ts">
// Plain full-history list of every Room Movement record -- same
// createListResource + DataTable shape as CleaningTasks.vue/
// RoomInspections.vue, raw Link values shown as-is (guest/from_room/
// to_room), no enrichment join.
import { computed } from 'vue'
import { createListResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import { formatCurrency, formatDate } from '@/utils/format'

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase, and Room Movement's own rows don't carry a
// currency field (Rate Plan/Room Type don't either), so this is purely for
// formatting the Old/New Rate columns.
const properties = createListResource({
	doctype: 'Property',
	fields: ['name', 'default_currency'],
	pageLength: 1,
	auto: true,
})
const currency = computed<string>(() => properties.data?.[0]?.default_currency ?? '')

const movements = createListResource({
	doctype: 'Room Movement',
	fields: [
		'name',
		'movement_date',
		'guest',
		'from_room',
		'to_room',
		'old_rate',
		'new_rate',
		'rate_difference',
		'reason',
	],
	orderBy: 'creation desc',
	pageLength: 100,
	auto: true,
})

const columns: DataTableColumn[] = [
	{ key: 'name', label: 'Movement' },
	{ key: 'movement_date', label: 'Date' },
	{ key: 'guest', label: 'Guest' },
	{ key: 'from_room', label: 'From Room' },
	{ key: 'to_room', label: 'To Room' },
	{ key: 'old_rate', label: 'Old Rate' },
	{ key: 'new_rate', label: 'New Rate' },
	{ key: 'rate_difference', label: 'Difference' },
	{ key: 'reason', label: 'Reason' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Room Movement</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Full history of every room-to-room transfer.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="movements.data ?? []"
			:loading="movements.list.loading"
			:error="movements.list.error"
			empty-title="No room movements yet"
			empty-description="Room-to-room transfers will show up here once a guest is moved mid-stay."
			@retry="movements.reload()"
		>
			<template #cell-name="{ row }">
				<span class="font-medium text-app-text">{{ row.name }}</span>
			</template>
			<template #cell-movement_date="{ row }">{{ formatDate(row.movement_date) }}</template>
			<template #cell-old_rate="{ row }">{{ formatCurrency(row.old_rate, currency) }}</template>
			<template #cell-new_rate="{ row }">{{ formatCurrency(row.new_rate, currency) }}</template>
			<template #cell-rate_difference="{ row }">
				<span
					class="font-medium"
					:class="row.rate_difference > 0 ? 'text-app-success' : row.rate_difference < 0 ? 'text-app-danger' : 'text-app-text'"
				>
					{{ row.rate_difference > 0 ? '+' : '' }}{{ formatCurrency(row.rate_difference, currency) }}
				</span>
			</template>
			<template #cell-reason="{ row }">{{ row.reason ?? '—' }}</template>
		</DataTable>
	</PageContainer>
</template>
