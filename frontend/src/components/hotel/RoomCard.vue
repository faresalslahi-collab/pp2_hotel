<script setup lang="ts">
import StatusBadge from '@/components/ui/StatusBadge.vue'
import type { RoomGridItem } from '@/types/hotel'

defineProps<{ room: RoomGridItem }>()
const emit = defineEmits<{ click: [] }>()
</script>

<template>
	<button
		type="button"
		class="flex w-full flex-col gap-2 rounded-app-md border border-app-border bg-app-surface p-3 text-left transition-colors hover:border-app-primary hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-app-primary"
		@click="emit('click')"
	>
		<div class="flex items-start justify-between gap-2">
			<div class="min-w-0">
				<p class="truncate text-[15px] font-semibold leading-[20px] text-app-text">{{ room.room_number }}</p>
				<p class="truncate text-[12px] leading-[16px] text-app-muted">{{ room.room_type }}</p>
			</div>
			<StatusBadge :status="room.status" />
		</div>
		<p v-if="room.guest_name" class="truncate text-[13px] leading-[16px] text-app-text">
			{{ room.guest_name }}
		</p>
	</button>
</template>
