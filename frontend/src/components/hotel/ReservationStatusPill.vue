<script setup lang="ts">
// Reservation.status color map -- deliberately separate from StatusBadge.vue
// (Room.status): the two fields have different value sets and different
// semantics (a "Reserved" room and a "Confirmed" reservation aren't the same
// axis), so reusing StatusBadge's map would mean silently overloading it
// with unrelated meanings. Same dot+pill visual language, own map, built
// entirely from the existing `app.*` token set (no new hex colors).
import type { ReservationStatus } from '@/types/hotel'

defineProps<{ status: ReservationStatus }>()

const CLASSES: Record<ReservationStatus, { surface: string; text: string; dot: string }> = {
	Draft: { surface: 'bg-app-border/50', text: 'text-app-muted', dot: 'bg-app-muted' },
	Confirmed: { surface: 'bg-app-success-surface', text: 'text-app-success', dot: 'bg-app-success' },
	Cancelled: { surface: 'bg-app-danger-surface', text: 'text-app-danger', dot: 'bg-app-danger' },
	'No Show': { surface: 'bg-app-warning-surface', text: 'text-app-warning', dot: 'bg-app-warning' },
	Completed: { surface: 'bg-app-info-surface', text: 'text-app-info', dot: 'bg-app-info' },
}
</script>

<template>
	<span
		class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-app-sm px-2 py-0.5 text-xs font-medium leading-4"
		:class="[CLASSES[status].surface, CLASSES[status].text]"
	>
		<span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="CLASSES[status].dot" />
		{{ status }}
	</span>
</template>
