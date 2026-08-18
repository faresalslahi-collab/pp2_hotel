<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import { addDaysIso, todayIso } from '@/utils/dates'
import type { PaymentReport } from '@/types/hotel'

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase. Also supplies the currency for the by-method
// summary tiles, since (unlike each payment row) the report's top-level
// `total`/`by_method` totals don't carry their own currency field.
const properties = createListResource({
	doctype: 'Property',
	fields: ['name', 'default_currency'],
	pageLength: 1,
	auto: true,
})
const property = computed<string | null>(() => properties.data?.[0]?.name ?? null)
const currency = computed<string>(() => properties.data?.[0]?.default_currency ?? '')

const startDate = ref(addDaysIso(todayIso(), -6))
const endDate = ref(todayIso())

const reportResource = createResource({
	url: 'pp2_hotel.api.reports.get_payment_report',
	params: {},
	auto: false,
})

const report = computed<PaymentReport | null>(() => reportResource.data ?? null)

function runReport() {
	reportResource.reload({
		property: property.value ?? undefined,
		start_date: startDate.value,
		end_date: endDate.value,
	})
}

// Same gating Availability.vue uses: wait for the property to resolve
// before the first fetch.
watch(
	property,
	(value) => {
		if (!value) return
		runReport()
	},
	{ immediate: true },
)

interface SummaryTile {
	label: string
	value: string
}

// One tile per payment method, plus a Total tile last.
const summaryTiles = computed<SummaryTile[]>(() => {
	const data = report.value
	if (!data) return []
	const tiles: SummaryTile[] = data.by_method.map((m) => ({
		label: m.payment_method,
		value: formatCurrency(m.total, currency.value),
	}))
	tiles.push({ label: 'Total', value: formatCurrency(data.total, currency.value) })
	return tiles
})

const columns: DataTableColumn[] = [
	{ key: 'posting_date', label: 'Date' },
	{ key: 'guest_name', label: 'Guest' },
	{ key: 'room_number', label: 'Room' },
	{ key: 'payment_method', label: 'Method' },
	{ key: 'amount', label: 'Amount' },
	{ key: 'reference', label: 'Reference' },
]

const paymentRows = computed(() => report.value?.payments ?? [])
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Payment Report</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Payments recorded for a date range.</p>
		</div>

		<div class="mb-6 flex flex-wrap items-end gap-3 rounded-app-md border border-app-border bg-app-surface p-4">
			<FormControl v-model="startDate" type="date" label="Start Date" variant="outline" />
			<FormControl v-model="endDate" type="date" label="End Date" variant="outline" />
			<Button variant="solid" :loading="reportResource.loading" @click="runReport">Run Report</Button>
		</div>

		<LoadingState v-if="reportResource.loading && !report" :rows="4" />
		<ErrorState
			v-else-if="reportResource.error"
			title="Couldn't load report"
			description="Something went wrong while loading the payment report."
			@retry="runReport"
		/>
		<template v-else-if="report">
			<div class="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
				<div v-for="tile in summaryTiles" :key="tile.label" class="rounded-app-md border border-app-border bg-app-surface p-3">
					<p class="truncate text-[12px] leading-[16px] text-app-muted">{{ tile.label }}</p>
					<p class="mt-1 truncate text-[20px] font-semibold leading-[28px] text-app-text">{{ tile.value }}</p>
				</div>
			</div>

			<DataTable
				:columns="columns"
				:rows="paymentRows"
				empty-title="No payments for this range"
				empty-description="There are no payments recorded for the selected date range."
			>
				<template #cell-posting_date="{ row }">{{ formatDate(row.posting_date) }}</template>
				<template #cell-amount="{ row }">{{ formatCurrency(row.amount, row.currency) }}</template>
			</DataTable>
		</template>
	</PageContainer>
</template>
