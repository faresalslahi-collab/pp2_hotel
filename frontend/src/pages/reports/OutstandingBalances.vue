<script setup lang="ts">
import { computed, watch } from 'vue'
import { createResource, createListResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import { formatCurrency } from '@/utils/format'
import type { OutstandingBalanceRow } from '@/types/hotel'

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase.
const properties = createListResource({
	doctype: 'Property',
	fields: ['name'],
	pageLength: 1,
	auto: true,
})
const property = computed<string | null>(() => properties.data?.[0]?.name ?? null)

const balancesResource = createResource({
	url: 'pp2_hotel.api.reports.get_outstanding_balances',
	params: {},
	auto: false,
})

const rows = computed<OutstandingBalanceRow[]>(() => balancesResource.data ?? [])

function loadBalances() {
	balancesResource.reload({ property: property.value ?? undefined })
}

// Same gating Availability.vue uses: wait for the property to resolve
// before the first fetch.
watch(
	property,
	(value) => {
		if (!value) return
		loadBalances()
	},
	{ immediate: true },
)

const columns: DataTableColumn[] = [
	{ key: 'guest_name', label: 'Guest' },
	{ key: 'room_number', label: 'Room' },
	{ key: 'status', label: 'Status' },
	{ key: 'total', label: 'Total' },
	{ key: 'paid_amount', label: 'Paid' },
	{ key: 'balance', label: 'Balance' },
	{ key: 'checkout_override_reason', label: 'Override Reason' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Outstanding Balances</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Every folio with money owed -- including closed folios left over from a checkout override.
			</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="balancesResource.loading"
			:error="balancesResource.error"
			empty-title="No outstanding balances"
			empty-description="Every folio has been paid in full."
			error-title="Couldn't load outstanding balances"
			error-description="Something went wrong while loading outstanding balances."
			@retry="loadBalances"
		>
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
			<!-- Every row here is money owed by definition -- always render in
			     the danger token, not just when some threshold is crossed. -->
			<template #cell-balance="{ row }">
				<span class="font-medium text-app-danger">{{ formatCurrency(row.balance, row.currency) }}</span>
			</template>
			<template #cell-checkout_override_reason="{ row }">{{ row.checkout_override_reason ?? '—' }}</template>
		</DataTable>
	</PageContainer>
</template>
