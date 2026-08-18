<script setup lang="ts">
import MasterListPage from '@/components/config/MasterListPage.vue'
import type { MasterField } from '@/components/config/MasterFormDialog.vue'
import type { DataTableColumn } from '@/components/ui/DataTable.vue'

const SERVICE_TYPES = ['Room Service', 'Laundry', 'Minibar', 'Spa', 'Other']

const columns: DataTableColumn[] = [
	{ key: 'service_name', label: 'Service Name' },
	{ key: 'service_type', label: 'Type' },
	{ key: 'rate', label: 'Rate' },
	{ key: 'is_active', label: 'Active' },
]

const fields: MasterField[] = [
	{ fieldname: 'service_name', label: 'Service Name', type: 'text', required: true },
	{ fieldname: 'service_type', label: 'Service Type', type: 'select', options: SERVICE_TYPES },
	{ fieldname: 'rate', label: 'Rate', type: 'number' },
	{ fieldname: 'is_active', label: 'Active', type: 'checkbox' },
]
</script>

<template>
	<MasterListPage
		doctype="Hotel Service"
		title="Hotel Services"
		description="The rate card used by Add Charge and Order Service."
		:columns="columns"
		:fields="fields"
		order-by="service_name asc"
	/>
</template>
