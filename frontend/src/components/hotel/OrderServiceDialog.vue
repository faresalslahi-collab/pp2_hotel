<script setup lang="ts">
// Same centered Teleport + Transition modal as AddChargeDialog.vue, and the
// same "pick a Hotel Service or enter one manually" pattern -- the
// difference is what happens on submit: this creates a Pending Service
// Order (services.service_orders.create_order), not an instant Folio
// charge. The bill only posts later, when staff mark the order Delivered
// from the Services board (see ServiceOrders.vue) -- see
// services/service_orders.py's module note for why that split exists.
import { computed, ref, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import { formatCurrency } from '@/utils/format'
import type { HotelServiceOption } from '@/types/hotel'

const props = defineProps<{ open: boolean; folio: string | null; currency: string }>()
const emit = defineEmits<{ close: []; ordered: [] }>()

const services = createListResource({
	doctype: 'Hotel Service',
	fields: ['name', 'service_name', 'rate', 'service_type'],
	filters: { is_active: 1 },
	auto: false,
})

const selectedService = ref('')
const selectedServiceType = ref('')
const description = ref('')
const rate = ref<number | null>(null)
const qty = ref(1)

const orderAction = createResource({
	url: 'pp2_hotel.api.service_orders.create_order',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens -- mirrors
// AddChargeDialog.vue's watch-on-open pattern.
watch(
	() => props.open,
	(open) => {
		if (!open) return
		selectedService.value = ''
		selectedServiceType.value = ''
		description.value = ''
		rate.value = null
		qty.value = 1
		orderAction.reset()
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

function onServiceSelect(value: string) {
	selectedService.value = value
	if (!value) {
		selectedServiceType.value = ''
		return
	}
	const match = (services.data ?? []).find((service: HotelServiceOption) => service.name === value)
	if (!match) return
	description.value = match.service_name
	rate.value = match.rate
	selectedServiceType.value = match.service_type ?? ''
}

const total = computed(() => (Number(rate.value) || 0) * (Number(qty.value) || 0))

const canSubmit = computed(
	() => Boolean(props.folio) && description.value.trim().length > 0 && Number(rate.value) > 0 && Number(qty.value) > 0,
)

async function submit() {
	if (!props.folio || !canSubmit.value) return
	try {
		await orderAction.submit({
			folio: props.folio,
			description: description.value.trim(),
			hotel_service: selectedService.value || undefined,
			rate: Number(rate.value),
			qty: Number(qty.value),
			service_type: selectedServiceType.value || undefined,
		})
		emit('ordered')
		emit('close')
	} catch {
		// orderAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Order Service</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close order service dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="orderAction.error"
							title="Could not place this order"
							:description="getErrorMessage(orderAction.error, 'Something went wrong while placing this order.')"
							@retry="submit"
						/>

						<p class="text-[13px] leading-[16px] text-app-muted">
							Creates a Pending order -- it only bills to the folio once marked Delivered from the Services
							board.
						</p>
						<FormControl
							:model-value="selectedService"
							type="select"
							label="Hotel Service (optional)"
							variant="outline"
							:options="[{ label: 'Custom order…', value: '' }, ...serviceOptions]"
							@update:model-value="onServiceSelect"
						/>
						<FormControl v-model="description" type="text" label="Description" variant="outline" required />
						<div class="grid grid-cols-2 gap-3">
							<FormControl v-model="rate" type="number" label="Rate" variant="outline" required />
							<FormControl v-model="qty" type="number" label="Qty" variant="outline" />
						</div>
						<p class="text-[13px] leading-[16px] text-app-muted">Total: {{ formatCurrency(total, currency) }}</p>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="orderAction.loading" :disabled="!canSubmit" @click="submit">
							Order Service
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
