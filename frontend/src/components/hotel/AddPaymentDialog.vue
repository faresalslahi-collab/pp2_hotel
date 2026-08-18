<script setup lang="ts">
// Same centered Teleport + Transition modal as CheckInDialog.vue /
// AddChargeDialog.vue.
import { computed, ref, watch } from 'vue'
import { createResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import { todayIso } from '@/utils/dates'
import { PAYMENT_METHODS } from '@/types/hotel'

const props = defineProps<{ open: boolean; folio: string | null }>()
const emit = defineEmits<{ close: []; paid: [] }>()

const amount = ref<number | null>(null)
const paymentMethod = ref<string>(PAYMENT_METHODS[0])
const reference = ref('')
const notes = ref('')
const postingDate = ref(todayIso())

const paymentAction = createResource({
	url: 'pp2_hotel.api.folio.add_payment',
	method: 'POST',
	auto: false,
})

watch(
	() => props.open,
	(open) => {
		if (!open) return
		amount.value = null
		paymentMethod.value = PAYMENT_METHODS[0]
		reference.value = ''
		notes.value = ''
		postingDate.value = todayIso()
		paymentAction.reset()
	},
	{ immediate: true },
)

const canSubmit = computed(
	() => Boolean(props.folio) && Number(amount.value) > 0 && Boolean(paymentMethod.value),
)

async function submit() {
	if (!props.folio || !canSubmit.value) return
	try {
		await paymentAction.submit({
			folio: props.folio,
			amount: Number(amount.value),
			payment_method: paymentMethod.value,
			reference: reference.value.trim() || undefined,
			notes: notes.value.trim() || undefined,
			posting_date: postingDate.value,
		})
		emit('paid')
		emit('close')
	} catch {
		// paymentAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Record Payment</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close payment dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="paymentAction.error"
							title="Could not record payment"
							:description="getErrorMessage(paymentAction.error, 'Something went wrong while recording this payment.')"
							@retry="submit"
						/>

						<div class="grid grid-cols-2 gap-3">
							<FormControl v-model="amount" type="number" label="Amount" variant="outline" required />
							<FormControl
								v-model="paymentMethod"
								type="select"
								label="Payment Method"
								variant="outline"
								:options="PAYMENT_METHODS"
							/>
						</div>
						<FormControl v-model="reference" type="text" label="Reference (optional)" variant="outline" />
						<FormControl v-model="notes" type="textarea" label="Notes (optional)" variant="outline" />
						<FormControl v-model="postingDate" type="date" label="Date" variant="outline" />
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="paymentAction.loading" :disabled="!canSubmit" @click="submit">
							Record Payment
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
