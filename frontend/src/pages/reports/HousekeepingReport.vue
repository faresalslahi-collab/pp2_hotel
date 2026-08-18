<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { addDaysIso, todayIso } from '@/utils/dates'
import type { HousekeepingReport } from '@/types/hotel'

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase.
const properties = createListResource({
	doctype: 'Property',
	fields: ['name'],
	pageLength: 1,
	auto: true,
})
const property = computed<string | null>(() => properties.data?.[0]?.name ?? null)

// Default range is last 30 days, matching this report's own server-side
// default (see pp2_hotel.services.reports.get_housekeeping_report) --
// unlike the occupancy/revenue and payment reports, which default to 7.
const startDate = ref(addDaysIso(todayIso(), -29))
const endDate = ref(todayIso())

const reportResource = createResource({
	url: 'pp2_hotel.api.reports.get_housekeeping_report',
	params: {},
	auto: false,
})

const report = computed<HousekeepingReport | null>(() => reportResource.data ?? null)

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

interface KpiTile {
	label: string
	value: string
}

function formatTurnaround(minutes: number | null): string {
	if (minutes === null) return '—'
	return `${Math.round(minutes)} min`
}

const kpiTiles = computed<KpiTile[]>(() => {
	const data = report.value
	if (!data) return []
	return [
		{ label: 'Total Tasks', value: String(data.total_tasks) },
		{ label: 'Completed', value: String(data.completed_tasks) },
		{ label: 'Pass Rate', value: `${data.pass_rate}%` },
		{ label: 'Avg Turnaround', value: formatTurnaround(data.avg_turnaround_minutes) },
	]
})
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Housekeeping Report</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Task volume, inspection pass rate, and turnaround for a date range.
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
			description="Something went wrong while loading the housekeeping report."
			@retry="runReport"
		/>
		<div v-else-if="report" class="grid grid-cols-2 gap-3 sm:grid-cols-4">
			<div v-for="tile in kpiTiles" :key="tile.label" class="rounded-app-md border border-app-border bg-app-surface p-3">
				<p class="truncate text-[12px] leading-[16px] text-app-muted">{{ tile.label }}</p>
				<p class="mt-1 truncate text-[20px] font-semibold leading-[28px] text-app-text">{{ tile.value }}</p>
			</div>
		</div>
	</PageContainer>
</template>
