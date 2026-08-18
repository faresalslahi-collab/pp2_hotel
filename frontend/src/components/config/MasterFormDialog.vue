<script setup lang="ts">
// Generic create/edit form for the five simple master doctypes Phase 11
// gives their first Vue screen (Property, Floor, Room Type, Rate Plan,
// Hotel Service) -- all CRUD through Frappe's own generic whitelisted
// frappe.client.insert/save/delete, since each doctype's DocType
// permission table (set in its own earlier phase) already gates who can
// write it; no new backend code needed for this phase at all. A `link`
// field type fetches its options from the target doctype via
// createListResource, the same "select populated from a list fetch"
// pattern AddChargeDialog.vue/OrderServiceDialog.vue already use for
// picking a Hotel Service -- generalized here instead of duplicated.
import { computed, reactive, watch } from 'vue'
import { createResource, createListResource, Button, FormControl } from 'frappe-ui'
import { X } from 'lucide-vue-next'
import ErrorState from '@/components/ui/ErrorState.vue'
import { getErrorMessage } from '@/utils/errors'

export interface MasterField {
	fieldname: string
	label: string
	type: 'text' | 'number' | 'date' | 'checkbox' | 'textarea' | 'select' | 'link'
	required?: boolean
	options?: string[] // for type: 'select'
	linkDoctype?: string // for type: 'link'
	linkTitleField?: string // for type: 'link' -- defaults to 'name'
}

const props = defineProps<{
	open: boolean
	doctype: string
	title: string
	fields: MasterField[]
	record: Record<string, any> | null // null means "create new"
}>()
const emit = defineEmits<{ close: []; saved: [] }>()

const formData = reactive<Record<string, any>>({})
const linkOptionsCache = reactive<Record<string, { value: string; label: string }[]>>({})
// The *complete* existing document when editing, fetched fresh each time the
// dialog opens -- frappe.client.save() treats any standard field missing
// from the submitted dict (creation, owner, ...) as being cleared, not left
// alone, and rejects clearing an immutable one ("Value cannot be changed for
// Created On"). Sending the full doc with only this form's fields
// overwritten avoids that entirely, on top of already needing `modified`
// for the optimistic-lock check.
const fullRecord = reactive<Record<string, any>>({})

const getAction = createResource({
	url: 'frappe.client.get',
	auto: false,
})
const saveAction = createResource({
	url: 'frappe.client.save',
	method: 'POST',
	auto: false,
})
const insertAction = createResource({
	url: 'frappe.client.insert',
	method: 'POST',
	auto: false,
})
const activeAction = computed(() => (props.record ? saveAction : insertAction))

watch(
	() => [props.open, props.record] as const,
	([open, record]) => {
		if (!open) return
		saveAction.reset()
		insertAction.reset()
		for (const key of Object.keys(fullRecord)) delete fullRecord[key]
		for (const field of props.fields) {
			formData[field.fieldname] = record ? record[field.fieldname] : (field.type === 'checkbox' ? 0 : '')
		}
		if (record) {
			getAction.submit({ doctype: props.doctype, name: record.name }).then((doc: Record<string, any>) => {
				Object.assign(fullRecord, doc)
			})
		}
		for (const field of props.fields) {
			if (field.type !== 'link' || !field.linkDoctype) continue
			if (linkOptionsCache[field.fieldname]) continue
			const titleField = field.linkTitleField ?? 'name'
			const list = createListResource({
				doctype: field.linkDoctype,
				fields: titleField === 'name' ? ['name'] : ['name', titleField],
				pageLength: 200,
				auto: false,
			})
			list.reload().then(() => {
				linkOptionsCache[field.fieldname] = (list.data ?? []).map((row: Record<string, any>) => ({
					value: row.name,
					label: titleField === 'name' ? row.name : (row[titleField] ?? row.name),
				}))
			})
		}
	},
	{ immediate: true },
)

function selectOptionsFor(field: MasterField) {
	if (field.type === 'select') return field.options ?? []
	if (field.type === 'link') return [{ label: 'Select…', value: '' }, ...(linkOptionsCache[field.fieldname] ?? [])]
	return []
}

const canSubmit = computed(
	() =>
		(!props.record || Boolean(fullRecord.name)) &&
		props.fields.every((field) => !field.required || Boolean(formData[field.fieldname])),
)

async function submit() {
	if (!canSubmit.value) return
	try {
		if (props.record) {
			// fullRecord carries every field (creation, owner, modified, ...)
			// so only this form's fields actually change -- see fullRecord's
			// own comment above for why a partial dict isn't safe here.
			await saveAction.submit({ doc: { ...fullRecord, ...formData } })
		} else {
			await insertAction.submit({ doc: { doctype: props.doctype, ...formData } })
		}
		emit('saved')
		emit('close')
	} catch {
		// activeAction.error renders inline below; dialog stays open to retry.
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
				<div class="flex max-h-[90vh] w-full max-w-md flex-col rounded-app-md border border-app-border bg-app-surface shadow-xl">
					<div class="flex h-14 shrink-0 items-center justify-between border-b border-app-border px-4">
						<p class="text-[14px] font-semibold leading-[20px] text-app-text">
							{{ record ? `Edit ${title}` : `New ${title}` }}
						</p>
						<button
							type="button"
							class="text-app-muted hover:text-app-text"
							aria-label="Close dialog"
							@click="emit('close')"
						>
							<X :size="20" />
						</button>
					</div>

					<div class="space-y-4 overflow-y-auto p-4">
						<ErrorState
							v-if="activeAction.error"
							title="Could not save"
							:description="getErrorMessage(activeAction.error, 'Something went wrong while saving.')"
							@retry="submit"
						/>

						<FormControl
							v-for="field in fields"
							:key="field.fieldname"
							v-model="formData[field.fieldname]"
							:type="field.type === 'link' ? 'select' : field.type"
							:label="field.label"
							variant="outline"
							:required="field.required"
							:options="selectOptionsFor(field)"
						/>
					</div>

					<div class="flex justify-end gap-2 border-t border-app-border p-4">
						<Button variant="outline" @click="emit('close')">Cancel</Button>
						<Button variant="solid" :loading="activeAction.loading" :disabled="!canSubmit" @click="submit">
							Save
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
