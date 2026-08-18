<script setup lang="ts">
// Company/default_currency/country/timezone/address stay Desk-only advanced
// fields this phase -- the common day-to-day fields (name, code, active,
// city, tax rate) are what staff actually need to touch regularly. See
// MasterListPage.vue/MasterFormDialog.vue for the shared CRUD shell.
import MasterListPage from '@/components/config/MasterListPage.vue'
import type { MasterField } from '@/components/config/MasterFormDialog.vue'
import type { DataTableColumn } from '@/components/ui/DataTable.vue'

const columns: DataTableColumn[] = [
	{ key: 'property_name', label: 'Property Name' },
	{ key: 'property_code', label: 'Code' },
	{ key: 'city', label: 'City' },
	{ key: 'default_tax_rate', label: 'Tax Rate' },
	{ key: 'is_active', label: 'Active' },
]

const fields: MasterField[] = [
	{ fieldname: 'property_name', label: 'Property Name', type: 'text', required: true },
	{ fieldname: 'property_code', label: 'Property Code', type: 'text', required: true },
	{ fieldname: 'city', label: 'City', type: 'text' },
	{ fieldname: 'default_tax_rate', label: 'Default Tax Rate (%)', type: 'number' },
	{ fieldname: 'is_active', label: 'Active', type: 'checkbox' },
]
</script>

<template>
	<MasterListPage
		doctype="Property"
		title="Properties"
		description="Company/currency/country/timezone are still managed in Frappe Desk."
		:columns="columns"
		:fields="fields"
		order-by="property_name asc"
	/>
</template>
