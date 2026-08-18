<script setup lang="ts">
// Plain full-history list of every Maintenance Request record, including
// Resolved/Cancelled ones -- unlike the Dashboard's active-only board. Same
// createListResource + DataTable shape as CleaningTasks.vue. This is also
// the "Maintenance History" nav destination in disguise -- a second,
// near-duplicate list showing the same data with a status filter would be
// exactly the kind of redundant screen Phase 4 already decided not to build
// twice for Housekeeping, so /maintenance/history stays ComingSoon.
import { createListResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import { formatDate } from '@/utils/format'

const requests = createListResource({
	doctype: 'Maintenance Request',
	fields: [
		'name',
		'room',
		'status',
		'priority',
		'description',
		'assigned_to',
		'reported_date',
		'resolved_date',
	],
	orderBy: 'creation desc',
	pageLength: 100,
	auto: true,
})

const columns: DataTableColumn[] = [
	{ key: 'name', label: 'Request' },
	{ key: 'room', label: 'Room' },
	{ key: 'status', label: 'Status' },
	{ key: 'priority', label: 'Priority' },
	{ key: 'description', label: 'Description' },
	{ key: 'assigned_to', label: 'Assigned To' },
	{ key: 'reported_date', label: 'Reported' },
	{ key: 'resolved_date', label: 'Resolved' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Maintenance Requests</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Full history of every maintenance request.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="requests.data ?? []"
			:loading="requests.list.loading"
			:error="requests.list.error"
			empty-title="No maintenance requests yet"
			empty-description="Requests will show up here once an issue is reported on a room."
			@retry="requests.reload()"
		>
			<template #cell-name="{ row }">
				<span class="font-medium text-app-text">{{ row.name }}</span>
			</template>
			<template #cell-assigned_to="{ row }">{{ row.assigned_to ?? 'Unassigned' }}</template>
			<template #cell-reported_date="{ row }">{{ formatDate(row.reported_date) }}</template>
			<template #cell-resolved_date="{ row }">{{ row.resolved_date ? formatDate(row.resolved_date) : '—' }}</template>
		</DataTable>
	</PageContainer>
</template>
