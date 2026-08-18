<script setup lang="ts">
// Same centered Teleport + Transition modal as the other Phase 4 dialogs.
// Kept deliberately minimal even after Phase 8 added Maintenance Request --
// this is reached from an already-in-progress cleaning task, so it stays a
// single required description field; the note still lands on the task too,
// and services.housekeeping.report_maintenance() now also creates a real
// Maintenance Request behind the scenes (see ReportIssueDialog.vue for the
// general-purpose "report an issue on any room" entry point on RoomDrawer).
import { computed, ref, watch } from 'vue'
import { createResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'

const props = defineProps<{ open: boolean; task: string | null }>()
const emit = defineEmits<{ close: []; reported: [] }>()

const description = ref('')

const reportAction = createResource({
	url: 'pp2_hotel.api.housekeeping.report_maintenance',
	method: 'POST',
	auto: false,
})

// Re-derive everything whenever the dialog opens for a (possibly different)
// task -- mirrors CheckInDialog's watch-on-open pattern.
watch(
	() => props.open,
	(open) => {
		if (!open) return
		description.value = ''
		reportAction.reset()
	},
	{ immediate: true },
)

const canSubmit = computed(() => Boolean(props.task) && description.value.trim().length > 0)

async function submit() {
	if (!props.task || !canSubmit.value) return
	try {
		await reportAction.submit({
			task: props.task,
			description: description.value.trim(),
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
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">Report Maintenance</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close report maintenance dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 p-4">
						<ErrorState
							v-if="reportAction.error"
							title="Could not report maintenance"
							:description="getErrorMessage(reportAction.error, 'Something went wrong while reporting this issue.')"
							@retry="submit"
						/>

						<p class="text-[13px] leading-[16px] text-app-muted">
							This takes the room out of rotation (status becomes Maintenance), appends your note to the
							cleaning task, and creates a Maintenance Request for tracking.
						</p>
						<FormControl
							v-model="description"
							type="textarea"
							label="What's wrong?"
							variant="outline"
							required
							placeholder="Describe the issue…"
						/>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="reportAction.loading" :disabled="!canSubmit" @click="submit">
							Report Maintenance
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
