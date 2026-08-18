<script setup lang="ts">
// Generic list+create+edit+delete shell for the five simple master
// doctypes Phase 11 gives their first Vue screen. Pairs with
// MasterFormDialog.vue for the actual create/edit form. Delete goes
// through frappe.client.delete, same "no new backend code" reasoning as
// the form dialog -- DocType permissions already gate all of this.
import { computed, ref } from 'vue'
import { createResource, createListResource, toast, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import MasterFormDialog, { type MasterField } from '@/components/config/MasterFormDialog.vue'
import { getErrorMessage } from '@/utils/errors'

const props = defineProps<{
	doctype: string
	title: string
	description: string
	columns: DataTableColumn[]
	fields: MasterField[]
	orderBy?: string
}>()

// `modified` is required even though no column shows it -- frappe.client.save
// does an optimistic-lock check against it (TimestampMismatchError if it's
// missing/stale), so MasterFormDialog.vue needs it round-tripped from the
// list row it opened the edit dialog from.
const listFields = computed(() => Array.from(new Set(['name', 'modified', ...props.fields.map((f) => f.fieldname)])))

const list = createListResource({
	doctype: props.doctype,
	fields: listFields.value,
	orderBy: props.orderBy ?? 'modified desc',
	pageLength: 100,
	auto: true,
})

const formOpen = ref(false)
const editingRecord = ref<Record<string, any> | null>(null)

function openCreate() {
	editingRecord.value = null
	formOpen.value = true
}
function openEdit(row: Record<string, any>) {
	editingRecord.value = row
	formOpen.value = true
}
function onSaved() {
	toast.success('Saved.')
	list.reload()
}

const deleteAction = createResource({
	url: 'frappe.client.delete',
	method: 'POST',
	auto: false,
})

async function remove(row: Record<string, any>) {
	if (!confirm(`Delete ${row.name}? This can't be undone.`)) return
	try {
		await deleteAction.submit({ doctype: props.doctype, name: row.name })
		toast.success('Deleted.')
		list.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not delete this record.'))
	}
}
</script>

<template>
	<PageContainer>
		<div class="mb-6 flex flex-wrap items-start justify-between gap-3">
			<div>
				<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">{{ title }}</h1>
				<p class="text-[13px] leading-[16px] text-app-muted">{{ description }}</p>
			</div>
			<Button variant="solid" @click="openCreate">New</Button>
		</div>

		<DataTable
			:columns="[...columns, { key: 'action', label: '' }]"
			:rows="list.data ?? []"
			:loading="list.list.loading"
			:error="list.list.error"
			:empty-title="`No ${title.toLowerCase()} yet`"
			empty-description="Use New to create the first one."
			row-clickable
			@retry="list.reload()"
			@row-click="openEdit"
		>
			<template v-for="field in fields.filter((f) => f.type === 'checkbox')" :key="field.fieldname" #[`cell-${field.fieldname}`]="{ row }">
				{{ row[field.fieldname] ? 'Yes' : 'No' }}
			</template>
			<template #cell-action="{ row }">
				<Button variant="outline" theme="red" @click.stop="remove(row)">Delete</Button>
			</template>
		</DataTable>

		<MasterFormDialog
			:open="formOpen"
			:doctype="doctype"
			:title="title.replace(/s$/, '')"
			:fields="fields"
			:record="editingRecord"
			@close="formOpen = false"
			@saved="onSaved"
		/>
	</PageContainer>
</template>
