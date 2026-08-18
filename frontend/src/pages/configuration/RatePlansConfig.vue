<script setup lang="ts">
// Rate Plan shipped its schema and services.rate_plan.get_effective_rate()
// back in Phase 6 -- this is the config screen that was deliberately
// deferred to "whichever phase actually ships Configuration UI" at the
// time (see ARCHITECTURE.md's Phase 6/7/8/9 build-phases notes).
import MasterListPage from '@/components/config/MasterListPage.vue'
import type { MasterField } from '@/components/config/MasterFormDialog.vue'
import type { DataTableColumn } from '@/components/ui/DataTable.vue'

const columns: DataTableColumn[] = [
	{ key: 'plan_name', label: 'Plan Name' },
	{ key: 'room_type', label: 'Room Type' },
	{ key: 'start_date', label: 'Start Date' },
	{ key: 'end_date', label: 'End Date' },
	{ key: 'rate', label: 'Rate' },
	{ key: 'is_active', label: 'Active' },
]

const fields: MasterField[] = [
	{ fieldname: 'plan_name', label: 'Plan Name', type: 'text', required: true },
	{ fieldname: 'property', label: 'Property', type: 'link', linkDoctype: 'Property', linkTitleField: 'property_name', required: true },
	{ fieldname: 'room_type', label: 'Room Type', type: 'link', linkDoctype: 'Room Type', linkTitleField: 'room_type_name', required: true },
	{ fieldname: 'start_date', label: 'Start Date', type: 'date', required: true },
	{ fieldname: 'end_date', label: 'End Date', type: 'date', required: true },
	{ fieldname: 'rate', label: 'Rate', type: 'number', required: true },
	{ fieldname: 'is_active', label: 'Active', type: 'checkbox' },
]
</script>

<template>
	<MasterListPage
		doctype="Rate Plan"
		title="Rate Plans"
		description="Date-range-aware pricing per Room Type -- overlapping active ranges for the same Room Type are rejected."
		:columns="columns"
		:fields="fields"
		order-by="start_date desc"
	/>
</template>
