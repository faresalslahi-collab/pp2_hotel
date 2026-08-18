<script setup lang="ts">
// Single source of truth for Room.status -> color across the whole app
// (dashboard KPI cards reference the tokens directly, RoomCard/RoomDrawer
// go through this component) -- see tailwind.config.js's `room-*` token
// doc comment. Never hardcode a status color anywhere else.
export type RoomStatus =
	| 'Available'
	| 'Occupied'
	| 'Dirty'
	| 'Cleaning'
	| 'Clean'
	| 'Inspected'
	| 'Reserved'
	| 'Out of Order'
	| 'Maintenance'

const props = defineProps<{ status: RoomStatus }>()

// Full, static class names -- Tailwind's JIT scanner greps source files for
// literal utility strings, so a runtime-interpolated class like
// `bg-app-room-${status}-surface` would never get generated into the CSS
// output. Every combination has to appear verbatim somewhere in this file.
const CLASSES: Record<RoomStatus, { surface: string; text: string; dot: string }> = {
	Available: { surface: 'bg-app-room-available-surface', text: 'text-app-room-available', dot: 'bg-app-room-available' },
	Occupied: { surface: 'bg-app-room-occupied-surface', text: 'text-app-room-occupied', dot: 'bg-app-room-occupied' },
	Dirty: { surface: 'bg-app-room-dirty-surface', text: 'text-app-room-dirty', dot: 'bg-app-room-dirty' },
	Cleaning: { surface: 'bg-app-room-cleaning-surface', text: 'text-app-room-cleaning', dot: 'bg-app-room-cleaning' },
	Clean: { surface: 'bg-app-room-clean-surface', text: 'text-app-room-clean', dot: 'bg-app-room-clean' },
	Inspected: { surface: 'bg-app-room-inspected-surface', text: 'text-app-room-inspected', dot: 'bg-app-room-inspected' },
	Reserved: { surface: 'bg-app-room-reserved-surface', text: 'text-app-room-reserved', dot: 'bg-app-room-reserved' },
	'Out of Order': { surface: 'bg-app-room-ooo-surface', text: 'text-app-room-ooo', dot: 'bg-app-room-ooo' },
	Maintenance: { surface: 'bg-app-room-maintenance-surface', text: 'text-app-room-maintenance', dot: 'bg-app-room-maintenance' },
}

const classes = CLASSES[props.status]
</script>

<template>
	<span
		class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-app-sm px-2 py-0.5 text-xs font-medium leading-4"
		:class="[classes.surface, classes.text]"
	>
		<span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="classes.dot" />
		{{ status }}
	</span>
</template>
