<script setup lang="ts">
import MasterListPage from '@/components/config/MasterListPage.vue'
import type { MasterField } from '@/components/config/MasterFormDialog.vue'
import type { DataTableColumn } from '@/components/ui/DataTable.vue'

const columns: DataTableColumn[] = [
	{ key: 'room_type_name', label: 'Room Type' },
	{ key: 'property', label: 'Property' },
	{ key: 'base_rate', label: 'Base Rate' },
	{ key: 'max_occupancy', label: 'Max Occupancy' },
]

const fields: MasterField[] = [
	{ fieldname: 'room_type_name', label: 'Room Type Name', type: 'text', required: true },
	{ fieldname: 'property', label: 'Property', type: 'link', linkDoctype: 'Property', linkTitleField: 'property_name', required: true },
	{ fieldname: 'base_rate', label: 'Base Rate', type: 'number' },
	{ fieldname: 'max_occupancy', label: 'Max Occupancy', type: 'number' },
	{ fieldname: 'description', label: 'Description', type: 'textarea' },
]
</script>

<template>
	<MasterListPage
		doctype="Room Type"
		title="Room Types"
		description="The default rate used for Reservation Room lines and Rate Plan fallback."
		:columns="columns"
		:fields="fields"
		order-by="room_type_name asc"
	/>
</template>
