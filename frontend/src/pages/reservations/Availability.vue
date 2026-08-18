<script setup lang="ts">
// Property is fixed (no switcher yet) -- same single-property assumption as
// Dashboard.vue/RoomGrid.vue, except get_availability's `property` param is
// required (unlike the dashboard endpoints, which treat a missing property
// as "no filter"), so this page has to actually resolve one: it fetches the
// first Property record and uses it, same as NewReservation.vue does.
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createListResource, call, Button, FormControl } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import LoadingState from '@/components/ui/LoadingState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatCurrency } from '@/utils/format'
import { addDaysIso, todayIso } from '@/utils/dates'

const router = useRouter()

const properties = createListResource({
	doctype: 'Property',
	fields: ['name', 'property_name', 'default_currency'],
	pageLength: 1,
	auto: true,
})
const property = computed<string | null>(() => properties.data?.[0]?.name ?? null)
const currency = computed<string>(() => properties.data?.[0]?.default_currency ?? '')

const roomTypes = createListResource({
	doctype: 'Room Type',
	fields: ['name', 'room_type_name', 'base_rate'],
	filters: {},
	auto: false,
})

const arrival = ref(todayIso())
const departure = ref(addDaysIso(todayIso(), 1))

const availability = ref<Record<string, number>>({})
const loadingAvailability = ref(false)
const availabilityError = ref<unknown>(null)

async function loadAvailability() {
	const types = roomTypes.data ?? []
	if (!property.value || !types.length) return
	loadingAvailability.value = true
	availabilityError.value = null
	try {
		const entries = await Promise.all(
			types.map(async (rt: { name: string }) => {
				const count = await call('pp2_hotel.api.availability.get_availability', {
					property: property.value,
					room_type: rt.name,
					arrival: arrival.value,
					departure: departure.value,
				})
				return [rt.name, count as number] as const
			}),
		)
		availability.value = Object.fromEntries(entries)
	} catch (error) {
		availabilityError.value = error
	} finally {
		loadingAvailability.value = false
	}
}

// Room Types are scoped to the resolved property, and everything reloads
// together once that property is known -- there's no user-facing property
// switcher this phase, so this only ever fires once per page load.
watch(
	property,
	(value) => {
		if (!value) return
		roomTypes.update({ filters: { property: value } })
		roomTypes.reload().then(loadAvailability)
	},
	{ immediate: true },
)

function bookRoomType(roomTypeName: string) {
	router.push({
		path: '/reservations/new',
		query: { room_type: roomTypeName, arrival: arrival.value, departure: departure.value },
	})
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Availability</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Check room-type availability for a date range.</p>
		</div>

		<div class="mb-6 flex flex-wrap items-end gap-3 rounded-app-md border border-app-border bg-app-surface p-4">
			<FormControl v-model="arrival" type="date" label="Arrival" variant="outline" />
			<FormControl v-model="departure" type="date" label="Departure" variant="outline" />
			<Button variant="solid" :loading="loadingAvailability" @click="loadAvailability">Check Availability</Button>
		</div>

		<LoadingState v-if="roomTypes.list.loading && !roomTypes.data" :rows="4" />
		<ErrorState
			v-else-if="roomTypes.list.error"
			title="Couldn't load room types"
			description="Something went wrong while loading room types."
			@retry="roomTypes.reload()"
		/>
		<ErrorState
			v-else-if="availabilityError"
			title="Couldn't check availability"
			description="Something went wrong while checking availability."
			@retry="loadAvailability"
		/>
		<EmptyState
			v-else-if="!roomTypes.data?.length"
			title="No room types configured"
			description="There are no room types configured for this property yet."
		/>
		<div v-else class="overflow-x-auto rounded-app-md border border-app-border bg-app-surface">
			<table class="w-full text-left text-[13px] leading-[16px]">
				<thead>
					<tr class="border-b border-app-border">
						<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Room Type</th>
						<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Base Rate</th>
						<th class="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-app-muted">Available</th>
						<th class="px-4 py-2.5"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-app-border">
					<tr v-for="rt in roomTypes.data" :key="rt.name">
						<td class="px-4 py-2.5 text-app-text">{{ rt.room_type_name }}</td>
						<td class="px-4 py-2.5 text-app-text">{{ formatCurrency(rt.base_rate, currency) }}</td>
						<td class="px-4 py-2.5">
							<span v-if="loadingAvailability" class="text-app-muted">…</span>
							<span
								v-else
								class="font-medium"
								:class="(availability[rt.name] ?? 0) > 0 ? 'text-app-success' : 'text-app-danger'"
							>
								{{ availability[rt.name] ?? 0 }}
							</span>
						</td>
						<td class="px-4 py-2.5 text-right">
							<Button
								variant="outline"
								:disabled="loadingAvailability || (availability[rt.name] ?? 0) <= 0"
								@click="bookRoomType(rt.name)"
							>
								Book
							</Button>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</PageContainer>
</template>
