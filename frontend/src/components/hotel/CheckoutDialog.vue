<script setup lang="ts">
// Same centered Teleport + Transition modal as the other Phase 3 dialogs.
// The one wrinkle here vs. AddCharge/AddPayment is the two very different
// footers depending on the folio balance + the current user's roles -- see
// canOverride/needsOverride below, which mirror
// pp2_hotel.services.checkout.check_out's own branching exactly so the UI
// never offers a path the backend would reject.
import { computed, ref, watch } from 'vue'
import { createResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import { formatCurrency } from '@/utils/format'
import { useSessionStore } from '@/stores/session'
import type { FolioDetail, CheckoutResult } from '@/types/hotel'

const props = defineProps<{ open: boolean; stay: string | null; folio: string | null }>()
const emit = defineEmits<{ close: []; 'checked-out': [result: CheckoutResult] }>()

const sessionStore = useSessionStore()

// Mirrors pp2_hotel.services.checkout.OVERRIDE_ROLES verbatim -- keep these
// two lists in sync if the backend's ever changes.
const OVERRIDE_ROLES = ['System Manager', 'Hotel Administrator', 'Hotel Manager', 'Front Desk Manager']

const folioResource = createResource({
	url: 'pp2_hotel.api.folio.get_folio_detail',
	params: { folio: '' },
	auto: false,
})

const reason = ref('')

const checkoutAction = createResource({
	url: 'pp2_hotel.api.checkout.check_out',
	method: 'POST',
	auto: false,
})

// Re-fetch the folio balance whenever the dialog opens for a (possibly
// different) stay/folio -- mirrors RoomDrawer.vue's watch-on-open pattern.
// A stay with no folio at all (shouldn't normally happen post-check-in, but
// defended against anyway) just skips the fetch -- balance defaults to 0,
// same as the backend's own `folio.balance if folio else 0.0`.
watch(
	() => [props.open, props.folio] as const,
	([open, folio]) => {
		if (!open) return
		reason.value = ''
		checkoutAction.reset()
		if (folio) {
			folioResource.update({ params: { folio } })
			folioResource.reload()
		} else {
			folioResource.reset()
		}
	},
	{ immediate: true },
)

const folio = computed<FolioDetail | null>(() => folioResource.data ?? null)
const balance = computed(() => folio.value?.balance ?? 0)
const needsOverride = computed(() => balance.value > 0)
const canOverride = computed(() => sessionStore.hasAnyRole(OVERRIDE_ROLES))

// Blocks the submit path entirely while the folio balance can't be trusted
// yet (still loading, or failed to load) -- never let a stale/unknown
// balance decide whether checkout is safe to submit.
const balanceUnknown = computed(
	() => Boolean(props.folio) && (folioResource.loading || Boolean(folioResource.error)) && !folio.value,
)

const canSubmit = computed(() => {
	if (!props.stay || balanceUnknown.value) return false
	if (!needsOverride.value) return true
	return canOverride.value && reason.value.trim().length > 0
})

async function submit() {
	if (!props.stay || !canSubmit.value) return
	try {
		const result = await checkoutAction.submit({
			stay: props.stay,
			override_reason: needsOverride.value ? reason.value.trim() : undefined,
		})
		emit('checked-out', result as CheckoutResult)
		emit('close')
	} catch {
		// checkoutAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Check-out</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close check-out dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="checkoutAction.error"
							title="Check-out failed"
							:description="getErrorMessage(checkoutAction.error, 'Something went wrong while checking out.')"
							@retry="submit"
						/>

						<template v-if="props.folio">
							<LoadingState v-if="folioResource.loading && !folioResource.data" :rows="3" />
							<ErrorState
								v-else-if="folioResource.error"
								title="Couldn't load folio"
								description="Something went wrong while loading the folio balance."
								@retry="folioResource.reload()"
							/>
							<template v-else-if="folio">
								<div class="grid grid-cols-3 gap-3 rounded-app-md border border-app-border p-3">
									<div>
										<p class="text-[11px] uppercase leading-[16px] text-app-muted">Total</p>
										<p class="text-[14px] font-medium leading-[20px] text-app-text">
											{{ formatCurrency(folio.total, folio.currency) }}
										</p>
									</div>
									<div>
										<p class="text-[11px] uppercase leading-[16px] text-app-muted">Paid</p>
										<p class="text-[14px] font-medium leading-[20px] text-app-text">
											{{ formatCurrency(folio.paid_amount, folio.currency) }}
										</p>
									</div>
									<div>
										<p class="text-[11px] uppercase leading-[16px] text-app-muted">Balance</p>
										<p
											class="text-[14px] font-semibold leading-[20px]"
											:class="balance > 0 ? 'text-app-danger' : 'text-app-success'"
										>
											{{ formatCurrency(balance, folio.currency) }}
										</p>
									</div>
								</div>

								<div
									v-if="needsOverride && canOverride"
									class="space-y-3 rounded-app-md border border-app-warning bg-app-warning-surface p-3"
								>
									<p class="text-[13px] font-medium leading-[16px] text-app-warning">
										Outstanding balance. Checking out now is an exception, not the normal flow -- a reason is
										required and will be recorded on the folio.
									</p>
									<FormControl
										v-model="reason"
										type="textarea"
										label="Override Reason"
										variant="outline"
										required
										placeholder="Explain why this guest is checking out with an outstanding balance…"
									/>
								</div>
								<div v-else-if="needsOverride" class="space-y-1 rounded-app-md border border-app-danger bg-app-danger-surface p-3">
									<p class="text-[13px] font-medium leading-[16px] text-app-danger">
										Check-out is blocked until this balance is settled.
									</p>
									<p class="text-[13px] leading-[16px] text-app-danger">
										Use Add Payment to collect the outstanding {{ formatCurrency(balance, folio.currency) }} first.
									</p>
								</div>
							</template>
						</template>
						<p v-else class="text-[13px] leading-[16px] text-app-muted">
							This stay has no folio on record -- check-out will proceed with no balance to settle.
						</p>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button
							v-if="!needsOverride"
							variant="solid"
							:loading="checkoutAction.loading"
							:disabled="!canSubmit"
							@click="submit"
						>
							Confirm Check-out
						</Button>
						<button
							v-else-if="canOverride"
							type="button"
							class="inline-flex h-9 items-center rounded-app-sm bg-app-warning px-3 text-[13px] font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
							:disabled="!canSubmit || checkoutAction.loading"
							@click="submit"
						>
							{{ checkoutAction.loading ? 'Overriding…' : 'Override & Check Out' }}
						</button>
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
