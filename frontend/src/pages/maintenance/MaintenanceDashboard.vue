<script setup lang="ts">
// The Phase 8 operational worklist -- one row per active (Open/In Progress)
// Maintenance Request, same active-only-board shape as
// HousekeepingDashboard.vue. Start Work is a direct one-click transition (no
// extra input needed); Resolve/Cancel each open a reason/notes prompt via the
// shared ReasonPromptDialog.vue (same component ReservationDetail.vue uses
// for Cancel/Mark No Show), since the backend requires text for both.
import { computed, ref } from 'vue'
import { createResource, toast, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import ReasonPromptDialog from '@/components/ui/ReasonPromptDialog.vue'
import { getErrorMessage } from '@/utils/errors'
import { formatDate } from '@/utils/format'
import type { MaintenanceBoardRow } from '@/types/hotel'

const boardResource = createResource({
	url: 'pp2_hotel.api.maintenance.get_maintenance_board',
	params: {},
	auto: true,
})

const rows = computed<MaintenanceBoardRow[]>(() => boardResource.data ?? [])

const columns: DataTableColumn[] = [
	{ key: 'room', label: 'Room' },
	{ key: 'status', label: 'Status' },
	{ key: 'priority', label: 'Priority' },
	{ key: 'reported_date', label: 'Reported' },
	{ key: 'assigned_to', label: 'Assigned To' },
	{ key: 'action', label: '' },
]

// Tracks which single row has a direct (no-dialog) action in-flight, same
// per-row-loading pattern as HousekeepingDashboard.vue's actioningTask.
const actioningRequest = ref<string | null>(null)

const startWorkAction = createResource({
	url: 'pp2_hotel.api.maintenance.start_work',
	method: 'POST',
	auto: false,
})

async function startWork(row: Record<string, any>) {
	actioningRequest.value = row.name
	try {
		await startWorkAction.submit({ request: row.name })
		toast.success('Work started.')
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not start work on this request.'))
	} finally {
		actioningRequest.value = null
	}
}

const resolveOpen = ref(false)
const resolveRequest = ref<string | null>(null)
const resolveAction = createResource({
	url: 'pp2_hotel.api.maintenance.resolve_request',
	method: 'POST',
	auto: false,
})

function openResolve(row: Record<string, any>) {
	resolveRequest.value = row.name
	resolveOpen.value = true
}

async function submitResolve(resolutionNotes: string) {
	if (!resolveRequest.value) return
	try {
		await resolveAction.submit({ request: resolveRequest.value, resolution_notes: resolutionNotes })
		toast.success('Resolved. Room sent to Dirty for a once-over clean.')
		resolveOpen.value = false
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not resolve this request.'))
	}
}

const cancelOpen = ref(false)
const cancelRequestName = ref<string | null>(null)
const cancelAction = createResource({
	url: 'pp2_hotel.api.maintenance.cancel_request',
	method: 'POST',
	auto: false,
})

function openCancel(row: Record<string, any>) {
	cancelRequestName.value = row.name
	cancelOpen.value = true
}

async function submitCancel(reason: string) {
	if (!cancelRequestName.value) return
	try {
		await cancelAction.submit({ request: cancelRequestName.value, reason })
		toast.success('Request cancelled.')
		cancelOpen.value = false
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not cancel this request.'))
	}
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Maintenance Dashboard</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Rooms with an open or in-progress maintenance issue.</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="boardResource.loading"
			:error="boardResource.error"
			empty-title="Nothing to fix"
			empty-description="No open or in-progress maintenance requests right now."
			@retry="boardResource.reload()"
		>
			<template #cell-room="{ row }">
				<div>
					<p class="font-medium text-app-text">{{ row.room_number }}</p>
					<p class="text-[11px] leading-[16px] text-app-muted">{{ row.room }}</p>
				</div>
			</template>
			<template #cell-reported_date="{ row }">{{ formatDate(row.reported_date) }}</template>
			<template #cell-assigned_to="{ row }">{{ row.assigned_to ?? 'Unassigned' }}</template>
			<template #cell-action="{ row }">
				<div class="flex flex-wrap gap-2">
					<Button
						v-if="row.status === 'Open'"
						variant="outline"
						:loading="actioningRequest === row.name && startWorkAction.loading"
						:disabled="actioningRequest !== null && actioningRequest !== row.name"
						@click="startWork(row)"
					>
						Start Work
					</Button>
					<Button variant="outline" @click="openResolve(row)">Resolve</Button>
					<Button variant="outline" @click="openCancel(row)">Cancel</Button>
				</div>
			</template>
		</DataTable>

		<ReasonPromptDialog
			:open="resolveOpen"
			title="Resolve Maintenance Request"
			description="The room will be sent to Dirty and a cleaning task created, so it gets a once-over before it's sellable again."
			label="Resolution Notes"
			confirm-label="Resolve"
			:loading="resolveAction.loading"
			@close="resolveOpen = false"
			@confirm="submitResolve"
		/>
		<ReasonPromptDialog
			:open="cancelOpen"
			title="Cancel Maintenance Request"
			description="Use this for a mistaken or duplicate report -- the room reverts straight to Available, no cleaning needed."
			confirm-label="Cancel Request"
			:loading="cancelAction.loading"
			@close="cancelOpen = false"
			@confirm="submitCancel"
		/>
	</PageContainer>
</template>
