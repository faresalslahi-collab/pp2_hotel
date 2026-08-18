<script setup lang="ts">
// Small reusable "type a reason, then confirm" modal -- used by
// ReservationDetail.vue for both Cancel and Mark No Show, which the backend
// both reject outright on an empty reason (see
// pp2_hotel.api.reservations.cancel_reservation/mark_no_show). Built on
// frappe-ui's own <Dialog>, not the RoomDrawer/CheckInDialog slide-over
// pattern -- a two-field confirm prompt is exactly what Dialog is for, and
// this bench's other frappe-ui frontends (gcc_hr) use it the same way, so
// this isn't introducing a new modal language, just the one frappe-ui
// already ships for exactly this shape of interaction.
import { ref, watch } from 'vue'
import { Button, Dialog, FormControl } from 'frappe-ui'

const props = withDefaults(
	defineProps<{
		open: boolean
		title: string
		description?: string
		confirmLabel?: string
		// Phase 8 reuses this dialog for Resolve Maintenance Request, where
		// "Resolution Notes" reads far better than the generic "Reason" this
		// was originally written for (Cancel/Mark No Show).
		label?: string
		loading?: boolean
	}>(),
	{ description: '', confirmLabel: 'Confirm', label: 'Reason', loading: false },
)
const emit = defineEmits<{ close: []; confirm: [reason: string] }>()

const reason = ref('')

watch(
	() => props.open,
	(open) => {
		if (open) reason.value = ''
	},
)

function onModelUpdate(value: boolean) {
	if (!value) emit('close')
}

function confirm() {
	if (!reason.value.trim()) return
	emit('confirm', reason.value.trim())
}
</script>

<template>
	<Dialog :model-value="open" :options="{ title, size: 'sm' }" @update:model-value="onModelUpdate">
		<template #body-content>
			<div class="space-y-3">
				<p v-if="description" class="text-[13px] leading-[16px] text-app-muted">{{ description }}</p>
				<FormControl
					v-model="reason"
					type="textarea"
					:label="label"
					variant="outline"
					required
					placeholder="Explain why..."
				/>
			</div>
		</template>
		<template #actions>
			<div class="flex flex-row-reverse gap-2">
				<Button variant="solid" theme="red" :loading="loading" :disabled="!reason.trim()" @click="confirm">
					{{ confirmLabel }}
				</Button>
				<Button variant="outline" @click="emit('close')">Cancel</Button>
			</div>
		</template>
	</Dialog>
</template>
