<script setup lang="ts">
// One component serves all four of /services, /services/room-service,
// /services/laundry, /services/minibar -- same "one component, several nav
// entries" consolidation Phase 5 used for the four Reports routes, except
// here each route actually filters different data (by service_type),
// determined from the route path itself rather than a route-level prop, to
// avoid restructuring router/index.ts's shared PHASE#_ROUTES component-only
// map. /services/other-charges stays ComingSoon -- redundant with
// AddChargeDialog.vue's existing free-text charge path, no distinct
// order/delivery workflow to build there.
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { createResource, createListResource, toast, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import ReasonPromptDialog from '@/components/ui/ReasonPromptDialog.vue'
import { getErrorMessage } from '@/utils/errors'
import { formatCurrency, formatDate } from '@/utils/format'
import type { ServiceOrderBoardRow } from '@/types/hotel'

const route = useRoute()

const SERVICE_TYPE_BY_PATH: Record<string, string> = {
	'/services/room-service': 'Room Service',
	'/services/laundry': 'Laundry',
	'/services/minibar': 'Minibar',
}
const serviceTypeFilter = computed<string | undefined>(() => SERVICE_TYPE_BY_PATH[route.path])
const pageTitle = computed(() => (serviceTypeFilter.value ? `${serviceTypeFilter.value} Orders` : 'Service Orders'))

// Same single-property resolution as Availability.vue -- no property
// switcher exists this phase, only used to format money below.
const properties = createListResource({
	doctype: 'Property',
	fields: ['name', 'default_currency'],
	pageLength: 1,
	auto: true,
})
const currency = computed<string>(() => properties.data?.[0]?.default_currency ?? '')

const boardResource = createResource({
	url: 'pp2_hotel.api.service_orders.get_service_board',
	params: { service_type: serviceTypeFilter.value },
	auto: true,
})

// The same component instance serves all four /services* routes -- Vue
// Router doesn't remount it on a static-to-static path change, so the
// active-category filter needs its own reload, same as FolioDetail.vue's
// watch on a changing :folio param.
watch(serviceTypeFilter, (value) => {
	boardResource.reload({ service_type: value })
})

const rows = computed<ServiceOrderBoardRow[]>(() => boardResource.data ?? [])

const columns: DataTableColumn[] = [
	{ key: 'room', label: 'Room' },
	{ key: 'service_type', label: 'Type' },
	{ key: 'description', label: 'Description' },
	{ key: 'qty', label: 'Qty' },
	{ key: 'amount', label: 'Amount' },
	{ key: 'ordered_at', label: 'Ordered' },
	{ key: 'action', label: '' },
]

const actioningOrder = ref<string | null>(null)

const deliverAction = createResource({
	url: 'pp2_hotel.api.service_orders.deliver_order',
	method: 'POST',
	auto: false,
})

async function deliver(row: Record<string, any>) {
	actioningOrder.value = row.name
	try {
		await deliverAction.submit({ order: row.name })
		toast.success('Delivered and billed to the folio.')
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not deliver this order.'))
	} finally {
		actioningOrder.value = null
	}
}

const cancelOpen = ref(false)
const cancelOrderName = ref<string | null>(null)
const cancelAction = createResource({
	url: 'pp2_hotel.api.service_orders.cancel_order',
	method: 'POST',
	auto: false,
})

function openCancel(row: Record<string, any>) {
	cancelOrderName.value = row.name
	cancelOpen.value = true
}

async function submitCancel(reason: string) {
	if (!cancelOrderName.value) return
	try {
		await cancelAction.submit({ order: cancelOrderName.value, reason })
		toast.success('Order cancelled.')
		cancelOpen.value = false
		boardResource.reload()
	} catch (err) {
		toast.error(getErrorMessage(err, 'Could not cancel this order.'))
	}
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">{{ pageTitle }}</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">
				Pending guest service orders{{ serviceTypeFilter ? '' : ' across every category' }} -- billed to the
				folio once delivered.
			</p>
		</div>

		<DataTable
			:columns="columns"
			:rows="rows"
			:loading="boardResource.loading"
			:error="boardResource.error"
			empty-title="No pending orders"
			empty-description="Orders placed from a Room Drawer will show up here until delivered or cancelled."
			@retry="boardResource.reload()"
		>
			<template #cell-room="{ row }">
				<div>
					<p class="font-medium text-app-text">{{ row.room_number }}</p>
					<p class="text-[11px] leading-[16px] text-app-muted">{{ row.room }}</p>
				</div>
			</template>
			<template #cell-amount="{ row }">{{ formatCurrency(row.amount, currency) }}</template>
			<template #cell-ordered_at="{ row }">{{ formatDate(row.ordered_at) }}</template>
			<template #cell-action="{ row }">
				<div class="flex flex-wrap gap-2">
					<Button
						variant="outline"
						:loading="actioningOrder === row.name && deliverAction.loading"
						:disabled="actioningOrder !== null && actioningOrder !== row.name"
						@click="deliver(row)"
					>
						Deliver
					</Button>
					<Button variant="outline" @click="openCancel(row)">Cancel</Button>
				</div>
			</template>
		</DataTable>

		<ReasonPromptDialog
			:open="cancelOpen"
			title="Cancel Service Order"
			description="Nothing is billed for a cancelled order -- use this when the guest changes their mind before delivery."
			confirm-label="Cancel Order"
			:loading="cancelAction.loading"
			@close="cancelOpen = false"
			@confirm="submitCancel"
		/>
	</PageContainer>
</template>
