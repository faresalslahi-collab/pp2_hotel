<script setup lang="ts">
// Plain full-history list of every Room Inspection record. Same
// createListResource + DataTable shape as CleaningTasks.vue; the one bit of
// custom rendering is the Passed/Failed pill, matching the app's existing
// success/danger token usage (ReservationStatusPill.vue, CheckoutDialog.vue's
// balance coloring) rather than introducing a new color pairing.
import { createListResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import { formatDate } from '@/utils/format'

const inspections = createListResource({
	doctype: 'Room Inspection',
	fields: ['name', 'housekeeping_task', 'room', 'result', 'inspector', 'inspection_date', 'notes'],
	orderBy: 'inspection_date desc',
	pageLength: 100,
	auto: true,
})

const columns: DataTableColumn[] = [
	{ key: 'name', label: 'Inspection' },
	{ key: 'room', label: 'Room' },
	{ key: 'housekeeping_task', label: 'Task' },
	{ key: 'result', label: 'Result' },
	{ key: 'inspector', label: 'Inspector' },
	{ key: 'inspection_date', label: 'Date' },
	{ key: 'notes', label: 'Notes' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Room Inspection</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Full history of every room inspection.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="inspections.data ?? []"
			:loading="inspections.list.loading"
			:error="inspections.list.error"
			empty-title="No inspections yet"
			empty-description="Inspections will show up here once cleaning tasks start getting inspected."
			@retry="inspections.reload()"
		>
			<template #cell-name="{ row }">
				<span class="font-medium text-app-text">{{ row.name }}</span>
			</template>
			<template #cell-result="{ row }">
				<span
					class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-app-sm px-2 py-0.5 text-xs font-medium leading-4"
					:class="
						row.result === 'Passed'
							? 'bg-app-success-surface text-app-success'
							: 'bg-app-danger-surface text-app-danger'
					"
				>
					<span
						class="h-1.5 w-1.5 shrink-0 rounded-full"
						:class="row.result === 'Passed' ? 'bg-app-success' : 'bg-app-danger'"
					/>
					{{ row.result }}
				</span>
			</template>
			<template #cell-inspector="{ row }">{{ row.inspector ?? '—' }}</template>
			<template #cell-inspection_date="{ row }">{{ formatDate(row.inspection_date) }}</template>
			<template #cell-notes="{ row }">
				<span class="block max-w-xs truncate" :title="row.notes ?? ''">{{ row.notes ?? '—' }}</span>
			</template>
		</DataTable>
	</PageContainer>
</template>
