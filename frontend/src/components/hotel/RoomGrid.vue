<script setup lang="ts">
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import RoomCard from './RoomCard.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import type { RoomGridItem } from '@/types/hotel'

// `property` is static for the lifetime of this component this phase --
// there's no property switcher UI yet (single-property assumption, same as
// the KPI row on Dashboard.vue), so a one-shot params object at creation
// time is enough; no need for a reactive params wiring.
const props = defineProps<{ property?: string }>()
const emit = defineEmits<{ 'select-room': [room: RoomGridItem] }>()

const roomsResource = createResource({
	url: 'pp2_hotel.api.dashboard.get_room_grid',
	params: props.property ? { property: props.property } : {},
	auto: true,
})

defineExpose({ reload: () => roomsResource.reload() })

const rooms = computed<RoomGridItem[]>(() => roomsResource.data ?? [])

interface FloorGroup {
	floor: string
	rooms: RoomGridItem[]
}

// Groups preserve first-seen floor order from the API response (e.g.
// "Floor 1", "Floor 2", ...) rather than re-sorting alphabetically, since
// the backend is the source of truth for floor ordering.
const floorGroups = computed<FloorGroup[]>(() => {
	const order: string[] = []
	const byFloor = new Map<string, RoomGridItem[]>()
	for (const room of rooms.value) {
		const floor = room.floor || 'Unassigned'
		if (!byFloor.has(floor)) {
			byFloor.set(floor, [])
			order.push(floor)
		}
		byFloor.get(floor)!.push(room)
	}
	return order.map((floor) => ({ floor, rooms: byFloor.get(floor)! }))
})
</script>

<template>
	<div>
		<LoadingState v-if="roomsResource.loading && !roomsResource.data" :rows="6" />
		<ErrorState
			v-else-if="roomsResource.error"
			title="Couldn't load rooms"
			description="Something went wrong while loading the room grid."
			@retry="roomsResource.reload()"
		/>
		<EmptyState
			v-else-if="!rooms.length"
			title="No rooms found"
			description="There are no rooms configured for this property yet."
		/>
		<div v-else class="space-y-6">
			<div v-for="group in floorGroups" :key="group.floor">
				<h3 class="mb-2 text-[12px] font-semibold uppercase leading-[16px] tracking-wide text-app-muted">
					{{ group.floor }}
				</h3>
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
					<RoomCard
						v-for="room in group.rooms"
						:key="room.name"
						:room="room"
						@click="emit('select-room', room)"
					/>
				</div>
			</div>
		</div>
	</div>
</template>
