<script setup lang="ts">
// Same centered Teleport + Transition modal as ReportMaintenanceDialog.vue,
// generalized to any room (not just one with an active Housekeeping Task) --
// reachable from RoomDrawer.vue regardless of occupancy, since an issue can
// be reported on an Occupied room too (the backend just leaves the room's
// own status alone in that case; see services/maintenance.py).
import { computed, ref, watch } from 'vue'
import { createResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'
import type { MaintenancePriority } from '@/types/hotel'

const PRIORITIES: MaintenancePriority[] = ['Low', 'Normal', 'High', 'Urgent']

const props = defineProps<{ open: boolean; room: string | null }>()
const emit = defineEmits<{ close: []; reported: [] }>()

const description = ref('')
const priority = ref<MaintenancePriority>('Normal')

const reportAction = createResource({
	url: 'pp2_hotel.api.maintenance.create_request',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens for a (possibly different)
// room -- mirrors ReportMaintenanceDialog.vue's watch-on-open pattern.
watch(
	() => props.open,
	(open) => {
		if (!open) return
		description.value = ''
		priority.value = 'Normal'
		reportAction.reset()
	},
	{ immediate: true },
)

const canSubmit = computed(() => Boolean(props.room) && description.value.trim().length > 0)

async function submit() {
	if (!props.room || !canSubmit.value) return
	try {
		await reportAction.submit({
			room: props.room,
			description: description.value.trim(),
			priority: priority.value,
		})
		emit('reported')
		emit('close')
	} catch {
		// reportAction.error renders inline below; dialog stays open to retry.
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Report Issue</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close report issue dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="reportAction.error"
							title="Could not report this issue"
							:description="getErrorMessage(reportAction.error, 'Something went wrong while reporting this issue.')"
							@retry="submit"
						/>

						<p class="text-[13px] leading-[16px] text-app-muted">
							Creates a Maintenance Request. If the room isn't currently occupied, it's also taken out of
							rotation until the request is resolved.
						</p>
						<FormControl
							v-model="description"
							type="textarea"
							label="What's wrong?"
							variant="outline"
							required
							placeholder="Describe the issue…"
						/>
						<FormControl
							v-model="priority"
							type="select"
							label="Priority"
							variant="outline"
							:options="PRIORITIES"
						/>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="reportAction.loading" :disabled="!canSubmit" @click="submit">
							Report Issue
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
