<script setup lang="ts">
// Read-only list of every Room currently Out of Order. "Out of Order" has no
// writer anywhere in this app yet -- it's still the separate, longer-term,
// Desk-only status ROOM_STATUS_ENGINE.md has documented since Phase 1
// (distinct from "Maintenance", which Maintenance Request now manages the
// full lifecycle of). This page just gives that status a real screen instead
// of ComingSoon; setting/clearing it remains a Desk-only action this phase.
import { createListResource } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'

const rooms = createListResource({
	doctype: 'Room',
	// Not `floor` -- Floor is hash-autonamed, so the raw Link value is a
	// meaningless ID with no display value to fall back on here (unlike
	// Room Movement's raw Room links, which are at least human-readable).
	fields: ['name', 'room_number', 'room_type'],
	filters: { status: 'Out of Order' },
	orderBy: 'room_number asc',
	pageLength: 100,
	auto: true,
})

const columns: DataTableColumn[] = [
	{ key: 'room_number', label: 'Room' },
	{ key: 'room_type', label: 'Room Type' },
]
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Out of Order Rooms</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Rooms taken out of rotation for a structural or long-term issue. Managed in Frappe Desk.
			</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rooms.data ?? []"
			:loading="rooms.list.loading"
			:error="rooms.list.error"
			empty-title="No rooms Out of Order"
			empty-description="Every room is on the sellable track right now."
			@retry="rooms.reload()"
		/>
	</PageContainer>
</template>
