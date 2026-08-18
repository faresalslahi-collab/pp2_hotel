<script setup lang="ts">
// Same centered Teleport + Transition modal as CheckoutDialog.vue/
// AddChargeDialog.vue. No live rate preview before submit -- like those two,
// the financial-impact numbers (old/new rate, difference) only ever come
// back from pp2_hotel.api.room_movement.move_room's own response, shown in
// the success toast rather than duplicating the backend's Rate Plan lookup
// on the client.
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl, toast } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import { formatCurrency } from '@/utils/format'
import type { RoomMovementResult } from '@/types/hotel'

const props = defineProps<{ open: boolean; stay: string | null; property: string | null; currency: string }>()
const emit = defineEmits<{ close: []; moved: [result: RoomMovementResult] }>()

const availableRooms = createListResource({
	doctype: 'Room',
	fields: ['name', 'room_number', 'room_type'],
	filters: {},
	auto: false,
})

const toRoom = ref('')
const reason = ref('')

const moveAction = createResource({
	url: 'pp2_hotel.api.room_movement.move_room',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens for a (possibly different)
// stay -- mirrors CheckoutDialog.vue's watch-on-open pattern.
watch(
	() => [props.open, props.property] as const,
	([open, property]) => {
		if (!open) return
		toRoom.value = ''
		reason.value = ''
		moveAction.reset()
		if (property) {
			availableRooms.update({ filters: { property, status: 'Available' } })
			availableRooms.reload()
		}
	},
	{ immediate: true },
)

const roomOptions = computed(() => [
	{ label: 'Select a room…', value: '' },
	...(availableRooms.data ?? []).map((room: { name: string; room_number: string; room_type: string }) => ({
		label: `${room.room_number} (${room.room_type})`,
		value: room.name,
	})),
])

const canSubmit = computed(() => Boolean(props.stay) && Boolean(toRoom.value))

async function submit() {
	if (!props.stay || !canSubmit.value) return
	try {
		const result = await moveAction.submit({
			hotel_stay: props.stay,
			to_room: toRoom.value,
			reason: reason.value.trim() || undefined,
		})
		const typedResult = result as RoomMovementResult
		toast.success(
			`Moved to ${toRoom.value}. Rate ${formatCurrency(typedResult.old_rate, props.currency)} -> ${formatCurrency(typedResult.new_rate, props.currency)}.`,
		)
		emit('moved', typedResult)
		emit('close')
	} catch {
		// moveAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Move Room</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close move room dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="moveAction.error"
							title="Could not move room"
							:description="getErrorMessage(moveAction.error, 'Something went wrong while moving this room.')"
							@retry="submit"
						/>

						<FormControl
							v-model="toRoom"
							type="select"
							label="Move To"
							variant="outline"
							:options="roomOptions"
						/>
						<p v-if="!availableRooms.list.loading && !(availableRooms.data ?? []).length" class="text-[13px] leading-[16px] text-app-muted">
							No other Available rooms in this property right now.
						</p>
						<FormControl
							v-model="reason"
							type="textarea"
							label="Reason (optional)"
							variant="outline"
							placeholder="Why is this guest moving rooms?"
						/>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="moveAction.loading" :disabled="!canSubmit" @click="submit">
							Confirm Move
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
