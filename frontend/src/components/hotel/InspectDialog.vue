<script setup lang="ts">
// Same centered Teleport + Transition modal as CheckInDialog.vue /
// AddChargeDialog.vue. The one piece of custom UI here is the Passed/Failed
// toggle -- deliberately two big buttons rather than a FormControl select,
// so Failed (the "something's wrong, re-queue this room" path) can be styled
// danger-toned and impossible to pick by accident.
import { computed, ref, watch } from 'vue'
import { createResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import { useSessionStore } from '@/stores/session'
import type { InspectionResult } from '@/types/hotel'

const props = defineProps<{ open: boolean; task: string | null }>()
const emit = defineEmits<{ close: []; inspected: [result: InspectionResult] }>()

const sessionStore = useSessionStore()

const result = ref<InspectionResult>('Passed')
const notes = ref('')

const inspectAction = createResource({
	url: 'pp2_hotel.api.housekeeping.inspect',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens for a (possibly different)
// task -- mirrors CheckInDialog's watch-on-open pattern.
watch(
	() => props.open,
	(open) => {
		if (!open) return
		result.value = 'Passed'
		notes.value = ''
		inspectAction.reset()
	},
	{ immediate: true },
)

// Failed is the "something's wrong" path -- at minimum encourage a reason
// since the room gets bounced back to Dirty and re-queued for the team to
// re-clean; require it rather than just nudging so the re-queue always
// carries a reason someone else can act on.
const canSubmit = computed(() => {
	if (!props.task) return false
	if (result.value === 'Failed') return notes.value.trim().length > 0
	return true
})

async function submit() {
	if (!props.task || !canSubmit.value) return
	try {
		await inspectAction.submit({
			task: props.task,
			result: result.value,
			inspector: sessionStore.user || undefined,
			notes: notes.value.trim() || undefined,
		})
		emit('inspected', result.value)
		emit('close')
	} catch {
		// inspectAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Inspect Room</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close inspection dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="inspectAction.error"
							title="Inspection failed to save"
							:description="getErrorMessage(inspectAction.error, 'Something went wrong while recording this inspection.')"
							@retry="submit"
						/>

						<div>
							<p class="mb-2 text-[11px] font-semibold uppercase leading-[16px] tracking-wide text-app-muted">
								Result
							</p>
							<div class="grid grid-cols-2 gap-2">
								<button
									type="button"
									class="rounded-app-sm border px-3 py-2 text-[13px] font-medium transition-colors"
									:class="
										result === 'Passed'
											? 'border-app-success bg-app-success-surface text-app-success'
											: 'border-app-border bg-app-surface text-app-muted hover:bg-app-bg'
									"
									@click="result = 'Passed'"
								>
									Passed
								</button>
								<button
									type="button"
									class="rounded-app-sm border px-3 py-2 text-[13px] font-medium transition-colors"
									:class="
										result === 'Failed'
											? 'border-app-danger bg-app-danger-surface text-app-danger'
											: 'border-app-border bg-app-surface text-app-muted hover:bg-app-bg'
									"
									@click="result = 'Failed'"
								>
									Failed
								</button>
							</div>
						</div>

						<FormControl
							v-model="notes"
							type="textarea"
							variant="outline"
							:label="result === 'Failed' ? 'Notes (required)' : 'Notes (optional)'"
							:required="result === 'Failed'"
							placeholder="What needs to be redone?"
						/>
						<p v-if="result === 'Failed'" class="text-[13px] leading-[16px] text-app-danger">
							Failing this inspection sends the room back to Dirty and re-queues the task.
						</p>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button v-if="result === 'Passed'" variant="solid" :loading="inspectAction.loading" :disabled="!canSubmit" @click="submit">
							Pass Inspection
						</Button>
						<button
							v-else
							type="button"
							class="inline-flex h-9 items-center rounded-app-sm bg-app-danger px-3 text-[13px] font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
							:disabled="!canSubmit || inspectAction.loading"
							@click="submit"
						>
							{{ inspectAction.loading ? 'Saving…' : 'Fail & Re-queue' }}
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
