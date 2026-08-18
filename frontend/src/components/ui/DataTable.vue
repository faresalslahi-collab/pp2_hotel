<script setup lang="ts">
// Generic list-table shell shared by this phase's four list pages (All
// Reservations, Arrivals, Departures, In-House Guests) -- same
// Loading/Empty/ErrorState wiring RoomGrid.vue uses, just column-driven
// instead of card-grid-driven. Rows are typed loosely (Record<string, any>)
// rather than one shared generic: the four pages' row shapes (Reservation,
// ArrivalRow, StayListRow) don't overlap enough for a single generic to pull
// its weight, and every column renders through the `cell-<key>` slot escape
// hatch anyway, so callers get real typing at the point they actually use
// `row`.
import LoadingState from './LoadingState.vue'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'

export interface DataTableColumn {
	key: string
	label: string
}

withDefaults(
	defineProps<{
		columns: DataTableColumn[]
		rows: Record<string, any>[]
		loading?: boolean
		// `any`, not `unknown` -- Vue's withDefaults()/defineProps() macro
		// can't synthesize a runtime prop declaration for `unknown` cleanly
		// (it mis-resolves the default-value type as a slot function type).
		// Callers only ever pass a resource's `.error`/`.list.error`, which
		// our frappe-ui.d.ts stub already types as `any` anyway.
		error?: any
		emptyTitle?: string
		emptyDescription?: string
		errorTitle?: string
		errorDescription?: string
		// Set by pages where clicking a row navigates/opens something
		// (ReservationList, Departures, In-House Guests). Arrivals renders a
		// per-row "Check In" button instead, so it leaves this off.
		rowClickable?: boolean
	}>(),
	{
		loading: false,
		error: null,
		emptyTitle: 'Nothing to show',
		emptyDescription: '',
		errorTitle: "Couldn't load data",
		errorDescription: 'Something went wrong while loading this list.',
		rowClickable: false,
	},
)

const emit = defineEmits<{ retry: []; 'row-click': [row: Record<string, any>] }>()
</script>

<template>
	<div>
		<LoadingState v-if="loading && !rows.length" :rows="6" />
		<ErrorState
			v-else-if="error"
			:title="errorTitle"
			:description="errorDescription"
			@retry="emit('retry')"
		/>
		<EmptyState v-else-if="!rows.length" :title="emptyTitle" :description="emptyDescription" />
		<div v-else class="overflow-x-auto rounded-app-md border border-app-border bg-app-surface">
			<table class="w-full text-left text-[13px] leading-[16px]">
				<thead>
					<tr class="border-b border-app-border">
						<th
							v-for="col in columns"
							:key="col.key"
							class="whitespace-nowrap px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted"
						>
							{{ col.label }}
						</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-app-border">
					<tr
						v-for="(row, index) in rows"
						:key="row.name ?? index"
						:class="rowClickable ? 'cursor-pointer transition-colors hover:bg-app-bg' : ''"
						@click="rowClickable && emit('row-click', row)"
					>
						<td v-for="col in columns" :key="col.key" class="whitespace-nowrap px-4 py-2.5 align-middle text-app-text">
							<slot :name="`cell-${col.key}`" :row="row">
								{{ row[col.key] ?? '—' }}
							</slot>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>
