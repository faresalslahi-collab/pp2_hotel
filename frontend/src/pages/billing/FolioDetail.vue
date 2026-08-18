<script setup lang="ts">
// Not nav-tree-generated -- wired directly into router/index.ts's appRoutes,
// same pattern as ReservationDetail.vue. Reached only via RoomDrawer's View
// Folio action (or a direct URL); there's no Folios list page this phase
// (see the product spec's "What NOT to build" section).
import { computed, ref, watch } from 'vue'
import { createResource, toast, Button } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import DataTable, { type DataTableColumn } from '@/components/ui/DataTable.vue'
import AddChargeDialog from '@/components/hotel/AddChargeDialog.vue'
import AddPaymentDialog from '@/components/hotel/AddPaymentDialog.vue'
import CheckoutDialog from '@/components/hotel/CheckoutDialog.vue'
import { formatCurrency, formatDate } from '@/utils/format'
import { getErrorMessage } from '@/utils/errors'
import type { FolioDetail, CheckoutResult } from '@/types/hotel'

const props = defineProps<{ folio: string }>()

const folioResource = createResource({
	url: 'pp2_hotel.api.folio.get_folio_detail',
	params: { folio: props.folio },
	auto: true,
})

// vue-router reuses this component instance across folio-to-folio
// navigation (same route record, different :folio) -- re-point and reload
// rather than recreate, mirroring ReservationDetail.vue's doc-resource watch.
watch(
	() => props.folio,
	(newFolio, oldFolio) => {
		if (!newFolio || newFolio === oldFolio) return
		folioResource.update({ params: { folio: newFolio } })
		folioResource.reload()
	},
)

const folio = computed<FolioDetail | null>(() => folioResource.data ?? null)

// Same equivalence RoomDrawer.vue relies on: this folio's own status is the
// authoritative signal here (get_folio_detail doesn't separately return the
// underlying stay's status), and it's only ever Closed by checkout.
const canFolioActions = computed(() => folio.value?.status === 'Open')

// Covers the checkout-time-failure retry path -- invoice generation is
// best-effort at checkout (see CheckoutResult's own comment in types/hotel.ts),
// so a Closed folio with no sales_invoice yet means it needs a manual retry.
const canGenerateInvoice = computed(() => folio.value?.status === 'Closed' && !folio.value?.sales_invoice)

const invoiceAction = createResource({
	url: 'pp2_hotel.api.invoicing.generate_invoice',
	method: 'POST',
	auto: false,
})

async function generateInvoice() {
	if (!folio.value) return
	try {
		await invoiceAction.submit({ folio: folio.value.name })
		toast.success('Invoice generated.')
		folioResource.reload()
	} catch (error) {
		toast.error(getErrorMessage(error, 'Something went wrong while generating the invoice.'))
	}
}

const chargeColumns: DataTableColumn[] = [
	{ key: 'posting_date', label: 'Date' },
	{ key: 'description', label: 'Description' },
	{ key: 'qty', label: 'Qty' },
	{ key: 'rate', label: 'Rate' },
	{ key: 'amount', label: 'Amount' },
]
const paymentColumns: DataTableColumn[] = [
	{ key: 'posting_date', label: 'Date' },
	{ key: 'payment_method', label: 'Method' },
	{ key: 'amount', label: 'Amount' },
	{ key: 'reference', label: 'Reference' },
]

const addChargeOpen = ref(false)
const addPaymentOpen = ref(false)
const checkoutOpen = ref(false)

function onCharged() {
	toast.success('Charge added.')
	folioResource.reload()
}
function onPaid() {
	toast.success('Payment recorded.')
	folioResource.reload()
}
function onCheckedOut(result: CheckoutResult) {
	// Invoice generation is best-effort at checkout -- surface a distinct,
	// non-blocking warning when it failed rather than a plain success toast,
	// so staff know to use the Generate Invoice retry button below.
	if (result.invoice_error) {
		toast.warning('Checked out. Invoice generation failed -- generate it manually below.')
	} else {
		toast.success('Guest checked out.')
	}
	folioResource.reload()
}
</script>

<template>
	<PageContainer>
		<LoadingState v-if="folioResource.loading && !folioResource.data" :rows="8" />
		<ErrorState
			v-else-if="folioResource.error"
			title="Couldn't load folio"
			description="Something went wrong while loading this folio."
			@retry="folioResource.reload()"
		/>
		<div v-else-if="folio" class="space-y-6">
			<div class="flex flex-wrap items-start justify-between gap-3">
				<div>
					<div class="flex items-center gap-2">
						<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">{{ folio.name }}</h1>
						<span
							class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-app-sm px-2 py-0.5 text-xs font-medium leading-4"
							:class="folio.status === 'Open' ? 'bg-app-success-surface text-app-success' : 'bg-app-border/50 text-app-muted'"
						>
							<span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="folio.status === 'Open' ? 'bg-app-success' : 'bg-app-muted'" />
							{{ folio.status }}
						</span>
					</div>
					<p class="text-[13px] leading-[16px] text-app-muted">
						{{ folio.guest_name }} &middot; Room {{ folio.room_number ?? '—' }}
					</p>
				</div>
				<div class="flex gap-2">
					<Button variant="outline" :disabled="!canFolioActions" @click="addPaymentOpen = true">Add Payment</Button>
					<Button variant="outline" :disabled="!canFolioActions" @click="addChargeOpen = true">Add Charge</Button>
					<Button variant="solid" :disabled="!canFolioActions" @click="checkoutOpen = true">Check-out</Button>
					<Button
						v-if="canGenerateInvoice"
						variant="outline"
						:loading="invoiceAction.loading"
						@click="generateInvoice"
					>
						Generate Invoice
					</Button>
				</div>
			</div>

			<div class="grid grid-cols-2 gap-4 rounded-app-md border border-app-border bg-app-surface p-4 sm:grid-cols-4">
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Arrival</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ formatDate(folio.arrival) }}</p>
				</div>
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Departure</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ formatDate(folio.departure) }}</p>
				</div>
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Stay</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ folio.stay }}</p>
				</div>
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Currency</p>
					<p class="text-[13px] leading-[16px] text-app-text">{{ folio.currency }}</p>
				</div>
				<div>
					<p class="text-[11px] uppercase leading-[16px] text-app-muted">Invoice</p>
					<p class="text-[13px] leading-[16px] text-app-text">
						{{ folio.sales_invoice ?? (folio.status === 'Closed' ? 'Not yet invoiced' : '—') }}
					</p>
				</div>
			</div>

			<p
				v-if="folio.checkout_override_reason"
				class="rounded-app-md border border-app-warning bg-app-warning-surface p-3 text-[13px] leading-[16px] text-app-warning"
			>
				Checked out with an outstanding balance override: "{{ folio.checkout_override_reason }}"
			</p>

			<div>
				<h2 class="mb-3 text-[15px] font-semibold leading-[20px] text-app-text">Charges</h2>
				<DataTable
					:columns="chargeColumns"
					:rows="folio.items"
					empty-title="No charges yet"
					empty-description="Charges added to this folio will appear here."
				>
					<template #cell-posting_date="{ row }">{{ formatDate(row.posting_date) }}</template>
					<template #cell-rate="{ row }">{{ formatCurrency(row.rate, folio.currency) }}</template>
					<template #cell-amount="{ row }">{{ formatCurrency(row.amount, folio.currency) }}</template>
				</DataTable>
			</div>

			<div>
				<h2 class="mb-3 text-[15px] font-semibold leading-[20px] text-app-text">Payments</h2>
				<DataTable
					:columns="paymentColumns"
					:rows="folio.payments"
					empty-title="No payments yet"
					empty-description="Payments recorded on this folio will appear here."
				>
					<template #cell-posting_date="{ row }">{{ formatDate(row.posting_date) }}</template>
					<template #cell-amount="{ row }">{{ formatCurrency(row.amount, folio.currency) }}</template>
					<template #cell-reference="{ row }">{{ row.reference ?? '—' }}</template>
				</DataTable>
			</div>

			<div class="max-w-sm space-y-1.5 rounded-app-md border border-app-border bg-app-surface p-4">
				<div class="flex justify-between text-[13px] leading-[16px]">
					<p class="text-app-muted">Subtotal</p>
					<p class="text-app-text">{{ formatCurrency(folio.subtotal, folio.currency) }}</p>
				</div>
				<div class="flex justify-between text-[13px] leading-[16px]">
					<p class="text-app-muted">Tax ({{ folio.tax_rate }}%)</p>
					<p class="text-app-text">{{ formatCurrency(folio.tax_amount, folio.currency) }}</p>
				</div>
				<div class="flex justify-between border-t border-app-border pt-1.5 text-[13px] font-medium leading-[16px]">
					<p class="text-app-text">Total</p>
					<p class="text-app-text">{{ formatCurrency(folio.total, folio.currency) }}</p>
				</div>
				<div class="flex justify-between text-[13px] leading-[16px]">
					<p class="text-app-muted">Paid</p>
					<p class="text-app-text">{{ formatCurrency(folio.paid_amount, folio.currency) }}</p>
				</div>
				<div class="flex justify-between border-t border-app-border pt-1.5 text-[15px] font-semibold leading-[20px]">
					<p class="text-app-text">Balance</p>
					<p :class="folio.balance > 0 ? 'text-app-danger' : 'text-app-success'">
						{{ formatCurrency(folio.balance, folio.currency) }}
					</p>
				</div>
			</div>
		</div>

		<AddChargeDialog
			:open="addChargeOpen"
			:folio="folio?.name ?? null"
			@close="addChargeOpen = false"
			@charged="onCharged"
		/>
		<AddPaymentDialog
			:open="addPaymentOpen"
			:folio="folio?.name ?? null"
			@close="addPaymentOpen = false"
			@paid="onPaid"
		/>
		<CheckoutDialog
			:open="checkoutOpen"
			:stay="folio?.stay ?? null"
			:folio="folio?.name ?? null"
			@close="checkoutOpen = false"
			@checked-out="onCheckedOut"
		/>
	</PageContainer>
</template>
