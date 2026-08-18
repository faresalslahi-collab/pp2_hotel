<script setup lang="ts">
// Same centered Teleport + Transition modal as CheckInDialog.vue (not
// frappe-ui's <Dialog>) -- kept to the one "mutating action" modal language
// this app already has, rather than introducing frappe-ui's Dialog for just
// this one case.
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import { todayIso } from '@/utils/dates'
import type { HotelServiceOption } from '@/types/hotel'

const props = defineProps<{ open: boolean; folio: string | null }>()
const emit = defineEmits<{ close: []; charged: [] }>()

const services = createListResource({
	doctype: 'Hotel Service',
	fields: ['name', 'service_name', 'rate'],
	filters: { is_active: 1 },
	auto: false,
})

const selectedService = ref('')
// Kept internal (not its own input) -- the spec's manual-entry path only
// exposes Description/Amount/Qty/Date; a service's rate is only ever used
// to (re)compute Amount when that service is selected, mirroring the
// backend's own "rate defaults to amount" contract for the free-text path.
const serviceRate = ref<number | null>(null)
const description = ref('')
const amount = ref<number | null>(null)
const qty = ref(1)
const postingDate = ref(todayIso())

const chargeAction = createResource({
	url: 'pp2_hotel.api.folio.add_charge',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens -- mirrors CheckInDialog's
// watch-on-open pattern.
watch(
	() => props.open,
	(open) => {
		if (!open) return
		selectedService.value = ''
		serviceRate.value = null
		description.value = ''
		amount.value = null
		qty.value = 1
		postingDate.value = todayIso()
		chargeAction.reset()
		services.update({ filters: { is_active: 1 } })
		services.reload()
	},
	{ immediate: true },
)

const serviceOptions = computed(() =>
	(services.data ?? []).map((service: HotelServiceOption) => ({
		label: service.service_name,
		value: service.name,
	})),
)

function roundMoney(value: number): number {
	return Math.round(value * 100) / 100
}

function onServiceSelect(value: string) {
	selectedService.value = value
	if (!value) {
		serviceRate.value = null
		return
	}
	const match = (services.data ?? []).find((service: HotelServiceOption) => service.name === value)
	if (!match) return
	description.value = match.service_name
	serviceRate.value = match.rate
	amount.value = roundMoney(match.rate * (Number(qty.value) || 1))
}

// While a service is selected, changing Qty keeps Amount in sync with
// rate x qty. Once the user clears the service (back to a free-text charge),
// Amount is a plain, independently-editable number.
watch(qty, (newQty) => {
	if (serviceRate.value != null) {
		amount.value = roundMoney(serviceRate.value * (Number(newQty) || 1))
	}
})

const canSubmit = computed(
	() =>
		Boolean(props.folio) &&
		description.value.trim().length > 0 &&
		Number(amount.value) > 0 &&
		Number(qty.value) > 0,
)

async function submit() {
	if (!props.folio || !canSubmit.value) return
	try {
		await chargeAction.submit({
			folio: props.folio,
			description: description.value.trim(),
			amount: Number(amount.value),
			hotel_service: selectedService.value || undefined,
			qty: Number(qty.value),
			rate: selectedService.value ? (serviceRate.value ?? undefined) : undefined,
			posting_date: postingDate.value,
		})
		emit('charged')
		emit('close')
	} catch {
		// chargeAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Add Charge</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close add charge dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="chargeAction.error"
							title="Could not add charge"
							:description="getErrorMessage(chargeAction.error, 'Something went wrong while adding this charge.')"
							@retry="submit"
						/>

						<FormControl
							:model-value="selectedService"
							type="select"
							label="Hotel Service (optional)"
							variant="outline"
							:options="[{ label: 'Custom charge…', value: '' }, ...serviceOptions]"
							@update:model-value="onServiceSelect"
						/>
						<FormControl v-model="description" type="text" label="Description" variant="outline" required />
						<div class="grid grid-cols-2 gap-3">
							<FormControl v-model="amount" type="number" label="Amount" variant="outline" required />
							<FormControl v-model="qty" type="number" label="Qty" variant="outline" />
						</div>
						<FormControl v-model="postingDate" type="date" label="Date" variant="outline" />
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="chargeAction.loading" :disabled="!canSubmit" @click="submit">
							Add Charge
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
