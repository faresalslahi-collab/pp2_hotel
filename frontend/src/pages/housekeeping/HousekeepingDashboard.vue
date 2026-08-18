<script setup lang="ts">
// The Phase 4 operational worklist: one row per room that currently needs
// housekeeping attention (get_housekeeping_board only ever returns tasks not
// yet Inspected -- those have already dropped off). Direct one-click
// transitions (Start Cleaning, Mark Clean) call their endpoint straight from
// the row, same "no dialog needed for a no-extra-input action" reasoning as
// Arrivals.vue's Check In button; Report Maintenance and Inspect open a
// dialog because they need extra input (a description, a pass/fail result).
import { computed, ref } from 'vue'
import { createResource, toast, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import ReportMaintenanceDialog from '@/components/hotel/ReportMaintenanceDialog.vue'
import InspectDialog from '@/components/hotel/InspectDialog.vue'
import { getErrorMessage } from '@/utils/errors'
import type { HousekeepingBoardRow, InspectionResult, RoomStatus } from '@/types/hotel'

const boardResource = createResource({
	url: 'pp2_hotel.api.housekeeping.get_housekeeping_board',
	params: {},
	auto: true,
})

const rows = computed<HousekeepingBoardRow[]>(() => boardResource.data ?? [])

const columns: DataTableColumn[] = [
	{ key: 'room', label: 'Room' },
	{ key: 'status', label: 'Status' },
	{ key: 'priority', label: 'Priority' },
	{ key: 'assigned_to', label: 'Assigned To' },
	{ key: 'action', label: '' },
]

// Derives the room's actual status from the task's status for a normal row
// (Pending -> Dirty, In Progress -> Cleaning, Completed -> Clean) so
// StatusBadge can render the same room-status language used everywhere else
// in the app, rather than a second, one-off "task status" color scheme.
// Orphan rows (no task record) already carry the room's real status --
// `orphan_room_status` -- straight from the backend.
function roomStatusFor(row: Record<string, any>): RoomStatus | null {
	if (row.orphan_room_status) return row.orphan_room_status
	switch (row.status) {
		case 'Pending':
			return 'Dirty'
		case 'In Progress':
			return 'Cleaning'
		case 'Completed':
			return 'Clean'
		default:
			return null
	}
}

// Tracks which single row currently has a direct (no-dialog) action
// in-flight, so only that row's button shows a loading state and the others
// stay clickable/disabled-consistently rather than every button on the board
// reacting to one shared resource's .loading flag.
const actioningTask = ref<string | null>(null)

const startCleaningAction = createResource({
	url: 'pp2_hotel.api.housekeeping.start_cleaning',
	method: 'POST',
	auto: false,
})
const markCleanAction = createResource({
	url: 'pp2_hotel.api.housekeeping.mark_clean',
	method: 'POST',
	auto: false,
})

async function startCleaning(row: Record<string, any>) {
	if (!row.name) return
	actioningTask.value = row.name
	try {
		await startCleaningAction.submit({ task: row.name })
		toast.success('Cleaning started.')
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not start cleaning.'))
	} finally {
		actioningTask.value = null
	}
}

async function markClean(row: Record<string, any>) {
	if (!row.name) return
	actioningTask.value = row.name
	try {
		await markCleanAction.submit({ task: row.name })
		toast.success('Room marked clean.')
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not mark this room clean.'))
	} finally {
		actioningTask.value = null
	}
}

const reportMaintenanceOpen = ref(false)
const reportMaintenanceTask = ref<string | null>(null)

function openReportMaintenance(row: Record<string, any>) {
	if (!row.name) return
	reportMaintenanceTask.value = row.name
	reportMaintenanceOpen.value = true
}

function onReported() {
	toast.success('Maintenance reported. Room taken out of rotation.')
	boardResource.reload()
}

const inspectOpen = ref(false)
const inspectTask = ref<string | null>(null)

function openInspect(row: Record<string, any>) {
	if (!row.name) return
	inspectTask.value = row.name
	inspectOpen.value = true
}

// A Passed inspection is a normal success; a Failed one bounces the room
// back to Dirty and re-queues the task, which reads very differently from
// "done" -- surfaced as a warning toast, not a generic success one, per the
// product spec.
function onInspected(result: InspectionResult) {
	if (result === 'Passed') {
		toast.success('Inspection passed. Room is now Available.')
	} else {
		toast.warning('Inspection failed -- room sent back to Dirty and re-queued.')
	}
	boardResource.reload()
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Housekeeping Dashboard</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Rooms that currently need housekeeping attention.
			</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="boardResource.loading"
			:error="boardResource.error"
			empty-title="Nothing to clean"
			empty-description="Every room is Inspected/Available -- no active housekeeping tasks right now."
			@retry="boardResource.reload()"
		>
			<template #cell-room="{ row }">
				<div>
					<p class="font-medium text-app-text">{{ row.room_number }}</p>
					<p class="text-[11px] leading-[16px] text-app-muted">{{ row.room }}</p>
				</div>
			</template>
			<template #cell-status="{ row }">
				<StatusBadge v-if="roomStatusFor(row)" :status="roomStatusFor(row)!" />
				<span v-else class="text-app-muted">—</span>
			</template>
			<template #cell-priority="{ row }">{{ row.priority ?? '—' }}</template>
			<template #cell-assigned_to="{ row }">{{ row.assigned_to ?? 'Unassigned' }}</template>
			<template #cell-action="{ row }">
				<div v-if="!row.name" class="text-[13px] text-app-muted">No task record on file</div>
				<div v-else class="flex flex-wrap gap-2">
					<Button
						v-if="row.status === 'Pending'"
						variant="outline"
						:loading="actioningTask === row.name && startCleaningAction.loading"
						:disabled="actioningTask !== null && actioningTask !== row.name"
						@click="startCleaning(row)"
					>
						Start Cleaning
					</Button>
					<template v-else-if="row.status === 'In Progress'">
						<Button
							variant="outline"
							:loading="actioningTask === row.name && markCleanAction.loading"
							:disabled="actioningTask !== null && actioningTask !== row.name"
							@click="markClean(row)"
						>
							Mark Clean
						</Button>
						<Button variant="outline" @click="openReportMaintenance(row)">Report Maintenance</Button>
					</template>
					<Button v-else-if="row.status === 'Completed'" variant="outline" @click="openInspect(row)">
						Inspect
					</Button>
				</div>
			</template>
		</DataTable>

		<ReportMaintenanceDialog
			:open="reportMaintenanceOpen"
			:task="reportMaintenanceTask"
			@close="reportMaintenanceOpen = false"
			@reported="onReported"
		/>
		<InspectDialog :open="inspectOpen" :task="inspectTask" @close="inspectOpen = false" @inspected="onInspected" />
	</PageContainer>
</template>
