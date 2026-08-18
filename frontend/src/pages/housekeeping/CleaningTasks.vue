<script setup lang="ts">
// Plain full-history list of every Housekeeping Task record, including
// Inspected ones -- unlike the Dashboard's active-only board, this is the
// audit trail. Same createListResource + DataTable shape as
// ReservationList.vue.
import { createListResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import { formatDate } from '@/utils/format'

const tasks = createListResource({
	doctype: 'Housekeeping Task',
	fields: ['name', 'room', 'status', 'priority', 'assigned_to', 'started_at', 'completed_at', 'creation'],
	orderBy: 'creation desc',
	pageLength: 100,
	auto: true,
})

const columns: DataTableColumn[] = [
	{ key: 'name', label: 'Task' },
	{ key: 'room', label: 'Room' },
	{ key: 'status', label: 'Status' },
	{ key: 'priority', label: 'Priority' },
	{ key: 'assigned_to', label: 'Assigned To' },
	{ key: 'started_at', label: 'Started' },
	{ key: 'completed_at', label: 'Completed' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Cleaning Tasks</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Full history of every housekeeping task.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="tasks.data ?? []"
			:loading="tasks.list.loading"
			:error="tasks.list.error"
			empty-title="No cleaning tasks yet"
			empty-description="Housekeeping tasks will show up here once rooms start needing attention."
			@retry="tasks.reload()"
		>
			<template #cell-name="{ row }">
				<span class="font-medium text-app-text">{{ row.name }}</span>
			</template>
			<template #cell-assigned_to="{ row }">{{ row.assigned_to ?? 'Unassigned' }}</template>
			<template #cell-started_at="{ row }">{{ row.started_at ? formatDate(row.started_at) : '—' }}</template>
			<template #cell-completed_at="{ row }">{{ row.completed_at ? formatDate(row.completed_at) : '—' }}</template>
		</DataTable>
	</PageContainer>
</template>
