<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, FormControl } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import type { GuestLedgerRow } from '@/types/hotel'

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase.
const properties = createListResource({
	doctype: 'Property',
	fields: ['name'],
	pageLength: 1,
	auto: true,
})
const property = computed<string | null>(() => properties.data?.[0]?.name ?? null)

const STATUS_OPTIONS = ['All', 'Open', 'Closed']
const statusFilter = ref('All')

const ledgerResource = createResource({
	url: 'pp2_hotel.api.reports.get_guest_ledger',
	params: {},
	auto: false,
})

const rows = computed<GuestLedgerRow[]>(() => ledgerResource.data ?? [])

function loadLedger() {
	ledgerResource.reload({
		property: property.value ?? undefined,
		status: statusFilter.value === 'All' ? undefined : statusFilter.value,
	})
}

// Same gating Availability.vue uses: wait for the property to resolve
// before the first fetch so it's included from the start.
watch(
	property,
	(value) => {
		if (!value) return
		loadLedger()
	},
	{ immediate: true },
)

watch(statusFilter, () => {
	if (!property.value) return
	loadLedger()
})

const columns: DataTableColumn[] = [
	{ key: 'guest_name', label: 'Guest' },
	{ key: 'room_number', label: 'Room' },
	{ key: 'arrival', label: 'Arrival' },
	{ key: 'departure', label: 'Departure' },
	{ key: 'status', label: 'Status' },
	{ key: 'total', label: 'Total' },
	{ key: 'paid_amount', label: 'Paid' },
	{ key: 'balance', label: 'Balance' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Guest Ledger</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Every folio's balance, open or closed.</p>
		</div>

		<div class="mb-6 flex flex-wrap items-end gap-3 rounded-app-md border border-app-border bg-app-surface p-4">
			<FormControl
				v-model="statusFilter"
				type="select"
				label="Status"
				variant="outline"
				:options="STATUS_OPTIONS"
			/>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="ledgerResource.loading"
			:error="ledgerResource.error"
			empty-title="No folios found"
			empty-description="There are no folios matching this filter."
			error-title="Couldn't load guest ledger"
			error-description="Something went wrong while loading the guest ledger."
			@retry="loadLedger"
		>
			<template #cell-arrival="{ row }">{{ formatDate(row.arrival) }}</template>
			<template #cell-departure="{ row }">{{ formatDate(row.departure) }}</template>
			<template #cell-status="{ row }">
				<span
					class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-app-sm px-2 py-0.5 text-xs font-medium leading-4"
					:class="row.status === 'Open' ? 'bg-app-success-surface text-app-success' : 'bg-app-border/50 text-app-muted'"
				>
					<span
						class="h-1.5 w-1.5 shrink-0 rounded-full"
						:class="row.status === 'Open' ? 'bg-app-success' : 'bg-app-muted'"
					/>
					{{ row.status }}
				</span>
			</template>
			<template #cell-total="{ row }">{{ formatCurrency(row.total, row.currency) }}</template>
			<template #cell-paid_amount="{ row }">{{ formatCurrency(row.paid_amount, row.currency) }}</template>
			<template #cell-balance="{ row }">{{ formatCurrency(row.balance, row.currency) }}</template>
		</DataTable>
	</PageContainer>
</template>
