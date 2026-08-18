<script setup lang="ts">
// Same Teleport + Transition custom-panel mechanism as RoomDrawer.vue (not
// frappe-ui's <Dialog>) -- reusing its exact backdrop treatment keeps this
// to one modal language for "big custom panel" needs instead of introducing
// a third. Centered + fade/scale rather than a right-edge slide, though:
// this is a small, focused confirm-one-thing action, not a detail view, so
// docking it to the screen edge like RoomDrawer would read oddly for a
// two-field confirmation.
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import LoadingState from '@/components/ui/LoadingState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import type { CheckInResult } from '@/types/hotel'

const props = defineProps<{
	open: boolean
	reservation: string | null
	reservationRoom: string | null
	roomType: string | null
	preAssignedRoom?: string | null
}>()
const emit = defineEmits<{ close: []; 'checked-in': [result: CheckInResult] }>()

const selectedRoom = ref<string>('')

const availableRooms = createListResource({
	doctype: 'Room',
	fields: ['name', 'room_number'],
	filters: {},
	auto: false,
})

const checkInResource = createResource({
	url: 'pp2_hotel.api.checkin.check_in',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens for a (possibly different)
// reservation line -- mirrors RoomDrawer.vue's watch-on-open pattern. Only
// fetches the Available-rooms list when there isn't already a pre-assigned
// room, since that path never needs a picker.
watch(
	() => [props.open, props.reservationRoom, props.roomType, props.preAssignedRoom] as const,
	([open, , roomType, preAssignedRoom]) => {
		if (!open) return
		selectedRoom.value = preAssignedRoom || ''
		checkInResource.reset()
		if (!preAssignedRoom && roomType) {
			availableRooms.update({ filters: { room_type: roomType, status: 'Available' } })
			availableRooms.reload()
		}
	},
	{ immediate: true },
)

const roomOptions = computed(() =>
	(availableRooms.data ?? []).map((room: { name: string; room_number: string }) => ({
		label: room.room_number,
		value: room.name,
	})),
)

const canConfirm = computed(() => Boolean(props.reservation && props.reservationRoom && selectedRoom.value))

async function confirm() {
	if (!props.reservation || !props.reservationRoom || !selectedRoom.value) return
	try {
		const result = await checkInResource.submit({
			reservation: props.reservation,
			reservation_room: props.reservationRoom,
			room: selectedRoom.value,
		})
		emit('checked-in', result as CheckInResult)
		emit('close')
	} catch {
		// checkInResource.error is now set -- rendered inline below, dialog
		// stays open so the user can pick a different room and retry (e.g.
		// someone else just took the room they picked).
	}
}
</script>

<template>
	<Teleport to="body">
		<Transition name="pp2-modal-backdrop">
			<div v-if="open" class="fixed inset-0 z-40 bg-black/40" @click="emit('close')" />
		</Transition>
		<Transition name="pp2-modal-panel">
			<div v-if="open" class="fixed inset-0 z-40 flex items-center justify-center p-4" role="dialog" aria-modal="true">
				<div class="flex w-full max-w-md flex-col rounded-app-md border border-app-border bg-app-surface shadow-xl">
					<div class="flex h-14 shrink-0 items-center justify-between border-b border-app-border px-4">
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Check In</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close check-in dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="checkInResource.error"
							title="Check-in failed"
							:description="getErrorMessage(checkInResource.error, 'Something went wrong while checking in.')"
							@retry="confirm"
						/>

						<div v-if="preAssignedRoom" class="space-y-1">
							<p class="text-[11px] font-semibold uppercase leading-[16px] tracking-wide text-app-muted">Room</p>
							<p class="text-[15px] font-medium leading-[20px] text-app-text">{{ preAssignedRoom }}</p>
						</div>
						<template v-else>
							<LoadingState v-if="availableRooms.list.loading && !availableRooms.data" :rows="3" />
							<ErrorState
								v-else-if="availableRooms.list.error"
								title="Couldn't load available rooms"
								description="Something went wrong while loading rooms for this room type."
								@retry="availableRooms.reload()"
							/>
							<EmptyState
								v-else-if="!roomOptions.length"
								title="No available rooms"
								description="There are no available rooms of this room type right now."
							/>
							<FormControl
								v-else
								v-model="selectedRoom"
								type="select"
								label="Assign Room"
								variant="outline"
								:options="[{ label: 'Select a room…', value: '' }, ...roomOptions]"
							/>
						</template>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="checkInResource.loading" :disabled="!canConfirm" @click="confirm">
							Check In
						</Button>
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<style scoped>
.pp2-modal-backdrop-enter-active,
.pp2-modal-backdrop-leave-active {
	transition: opacity 150ms ease;
}
.pp2-modal-backdrop-enter-from,
.pp2-modal-backdrop-leave-to {
	opacity: 0;
}

.pp2-modal-panel-enter-active,
.pp2-modal-panel-leave-active {
	transition:
		opacity 150ms ease,
		transform 150ms ease;
}
.pp2-modal-panel-enter-from,
.pp2-modal-panel-leave-to {
	opacity: 0;
	transform: scale(0.97);
}
</style>
