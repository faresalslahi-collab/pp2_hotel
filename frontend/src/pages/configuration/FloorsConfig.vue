<script setup lang="ts">
import MasterListPage from '@/components/config/MasterListPage.vue'
import type { MasterField } from '@/components/config/MasterFormDialog.vue'
import type { DataTableColumn } from '@/components/ui/DataTable.vue'

const columns: DataTableColumn[] = [
	{ key: 'floor_name', label: 'Floor Name' },
	{ key: 'property', label: 'Property' },
	{ key: 'floor_number', label: 'Floor Number' },
]

const fields: MasterField[] = [
	{ fieldname: 'floor_name', label: 'Floor Name', type: 'text', required: true },
	{ fieldname: 'property', label: 'Property', type: 'link', linkDoctype: 'Property', linkTitleField: 'property_name', required: true },
	{ fieldname: 'floor_number', label: 'Floor Number', type: 'number' },
]
</script>

<template>
	<MasterListPage
		doctype="Floor"
		title="Floors"
		description="Groups Rooms for the Room Grid and Reservation Calendar."
		:columns="columns"
		:fields="fields"
		order-by="floor_number asc"
	/>
</template>
