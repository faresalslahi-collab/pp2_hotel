<script setup lang="ts">
// The same RoomGrid/RoomDrawer pair Dashboard.vue uses, without the KPI
// row -- a dedicated Room Status board for when a user wants the grid
// without the day's arrival/departure counts alongside it. Reachable from
// Front Desk > Room Status (was a nav-only stub since Phase 1; wired up
// during the Phase 13 nav audit -- the pieces already existed, this route
// had simply never been connected to them).
import { ref } from 'vue'
import PageContainer from '@/components/layout/PageContainer.vue'
import RoomGrid from '@/components/hotel/RoomGrid.vue'
import RoomDrawer from '@/components/hotel/RoomDrawer.vue'
import type { RoomGridItem } from '@/types/hotel'

const selectedRoom = ref<RoomGridItem | null>(null)
const drawerOpen = ref(false)
const roomGrid = ref<InstanceType<typeof RoomGrid> | null>(null)

function openRoom(room: RoomGridItem) {
	selectedRoom.value = room
	drawerOpen.value = true
}

function closeDrawer() {
	drawerOpen.value = false
}

function onCheckedOut() {
	roomGrid.value?.reload()
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Room Status</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Every room, grouped by floor, colored by current status.</p>
		</div>

		<RoomGrid ref="roomGrid" @select-room="openRoom" />

		<RoomDrawer
			:open="drawerOpen"
			:room-name="selectedRoom?.name ?? null"
			@close="closeDrawer"
			@checked-out="onCheckedOut"
			@moved="onCheckedOut"
			@reported="onCheckedOut"
		/>
	</PageContainer>
</template>
