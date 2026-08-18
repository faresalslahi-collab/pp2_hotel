<script setup lang="ts">
// Manages Property User -- who can see which Property once a second
// Property exists (see pp2_hotel/permissions.py and PERMISSIONS.md section
// 3). Not part of the brief's original Configuration nav -- added in Phase
// 12 alongside the property-scoped permission mechanism itself, since
// System Manager/Hotel Administrator need *some* way to grant/revoke access
// without dropping into Frappe Desk for a routine admin task.
import MasterListPage from '@/components/config/MasterListPage.vue'
import type { MasterField } from '@/components/config/MasterFormDialog.vue'
import type { DataTableColumn } from '@/components/ui/DataTable.vue'

const columns: DataTableColumn[] = [
	{ key: 'property', label: 'Property' },
	{ key: 'user', label: 'User' },
]

const fields: MasterField[] = [
	{ fieldname: 'property', label: 'Property', type: 'link', linkDoctype: 'Property', linkTitleField: 'property_name', required: true },
	{ fieldname: 'user', label: 'User', type: 'link', linkDoctype: 'User', linkTitleField: 'full_name', required: true },
]
</script>

<template>
	<MasterListPage
		doctype="Property User"
		title="Property Access"
		description="Which users can see which Property. System Manager and Hotel Administrator always see every Property regardless of this list."
		:columns="columns"
		:fields="fields"
	/>
</template>
