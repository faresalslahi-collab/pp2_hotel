<script setup lang="ts">
// Backs FOUR nav destinations, not one: the Reports section's Occupancy,
// Revenue, ADR, and RevPAR links (see nav.ts) all point at this same
// component via PHASE5_ROUTES in router/index.ts. The backend already
// computes occupancy/ADR/RevPAR/revenue together in a single call
// (get_occupancy_revenue_report) -- there's no cheaper per-metric endpoint to
// split these into four screens, and the product spec doesn't ask for
// visually distinct pages, so one report with all four numbers up front
// serves every destination instead of four near-duplicate files.
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import { addDaysIso, todayIso } from '@/utils/dates'
import type { OccupancyRevenueReport } from '@/types/hotel'

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase, and the report endpoints treat a missing
// `property` as "no filter" anyway, but resolving it lets KPI cards and the
// daily table format money in this property's actual currency.
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
	url: 'pp2_hotel.api.reports.get_occupancy_revenue_report',
	params: {},
	auto: false,
})

const report = computed<OccupancyRevenueReport | null>(() => reportResource.data ?? null)

function runReport() {
	reportResource.reload({
		property: property.value ?? undefined,
		start_date: startDate.value,
		end_date: endDate.value,
	})
}

// Same gating Availability.vue uses: wait for the property to resolve
// before the first fetch so it's included from the start rather than
// firing twice (once without it, once with it).
watch(
	property,
	(value) => {
		if (!value) return
		runReport()
	},
	{ immediate: true },
)

interface KpiTile {
	label: string
	value: string
}

const kpiTiles = computed<KpiTile[]>(() => {
	const data = report.value
	if (!data) return []
	return [
		{ label: 'Occupancy %', value: `${data.occupancy_pct}%` },
		{ label: 'ADR', value: formatCurrency(data.adr, currency.value) },
		{ label: 'RevPAR', value: formatCurrency(data.revpar, currency.value) },
		{ label: 'Total Revenue', value: formatCurrency(data.total_revenue, currency.value) },
	]
})

const columns: DataTableColumn[] = [
	{ key: 'date', label: 'Date' },
	{ key: 'occupancy_pct', label: 'Occupancy %' },
	{ key: 'room_revenue', label: 'Room Revenue' },
	{ key: 'other_revenue', label: 'Other Revenue' },
	{ key: 'total_revenue', label: 'Total Revenue' },
]

const dailyRows = computed(() => report.value?.daily ?? [])
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Occupancy & Revenue</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Occupancy, ADR, RevPAR, and revenue for a date range.
			</p>
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
			description="Something went wrong while loading the occupancy and revenue report."
			@retry="runReport"
		/>
		<template v-else-if="report">
			<div class="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
				<div v-for="tile in kpiTiles" :key="tile.label" class="rounded-app-md border border-app-border bg-app-surface p-3">
					<p class="truncate text-[12px] leading-[16px] text-app-muted">{{ tile.label }}</p>
					<p class="mt-1 truncate text-[20px] font-semibold leading-[28px] text-app-text">{{ tile.value }}</p>
				</div>
			</div>

			<DataTable
				:columns="columns"
				:rows="dailyRows"
				empty-title="No data for this range"
				empty-description="There is no occupancy or revenue data for the selected date range."
			>
				<template #cell-date="{ row }">{{ formatDate(row.date) }}</template>
				<template #cell-occupancy_pct="{ row }">{{ row.occupancy_pct }}%</template>
				<template #cell-room_revenue="{ row }">{{ formatCurrency(row.room_revenue, currency) }}</template>
				<template #cell-other_revenue="{ row }">{{ formatCurrency(row.other_revenue, currency) }}</template>
				<template #cell-total_revenue="{ row }">{{ formatCurrency(row.total_revenue, currency) }}</template>
			</DataTable>
		</template>
	</PageContainer>
</template>
