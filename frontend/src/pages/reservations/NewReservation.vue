<script setup lang="ts">
// Guest section is a toggle (search existing vs. create new) rather than two
// permanently-visible forms, matching the contract's two guest paths.
// "New guest" is only actually created (frappe.client.insert) at submit
// time, not as the user types -- so switching modes back and forth, or
// abandoning the form, never leaves an orphaned Guest record behind.
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource, createListResource, Button, FormControl, toast } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { getErrorMessage } from '@/utils/errors'
import { addDaysIso, todayIso } from '@/utils/dates'

const route = useRoute()
const router = useRouter()

// ---- Property (single-property assumption, same as Dashboard/RoomGrid) ----
const properties = createListResource({
	doctype: 'Property',
	fields: ['name', 'property_name'],
	pageLength: 1,
	auto: true,
})
const property = computed<string | null>(() => properties.data?.[0]?.name ?? null)

// ---- Room Types (for the room-line picker + rate defaulting) ----
const roomTypes = createListResource({
	doctype: 'Room Type',
	fields: ['name', 'room_type_name', 'base_rate'],
	filters: {},
	auto: false,
})
watch(
	property,
	(value) => {
		if (!value) return
		roomTypes.update({ filters: { property: value } })
		roomTypes.reload()
	},
	{ immediate: true },
)
const roomTypeOptions = computed(() =>
	(roomTypes.data ?? []).map((rt: { name: string; room_type_name: string }) => ({
		label: rt.room_type_name,
		value: rt.name,
	})),
)

// ---- Guest: existing (search) vs. new (inline-create at submit time) ----
const guestMode = ref<'existing' | 'new'>('existing')
const guestQuery = ref('')
const selectedGuest = ref<{ name: string; guest_name: string; phone?: string; email?: string } | null>(null)
const newGuest = reactive({ guest_name: '', phone: '', email: '' })

const guestSearch = createListResource({
	doctype: 'Guest',
	fields: ['name', 'guest_name', 'phone', 'email'],
	filters: {},
	auto: false,
})

// frappe-ui's createListResource has no built-in `debounce` option (only
// plain createResource does -- see resources.js), so this is a small local
// debounce around the search trigger instead.
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(guestQuery, (value) => {
	if (searchTimer) clearTimeout(searchTimer)
	const query = value.trim()
	if (query.length < 2) {
		guestSearch.setData([])
		return
	}
	searchTimer = setTimeout(() => {
		guestSearch.update({ filters: { guest_name: ['like', `%${query}%`] } })
		guestSearch.reload()
	}, 350)
})

function selectGuest(guest: { name: string; guest_name: string; phone?: string; email?: string }) {
	selectedGuest.value = guest
	guestQuery.value = ''
	guestSearch.setData([])
}

const guestInsert = createResource({ url: 'frappe.client.insert', method: 'POST', auto: false })

async function resolveGuest(): Promise<string> {
	if (guestMode.value === 'existing') {
		if (!selectedGuest.value) throw new Error('Please search for and select a guest.')
		return selectedGuest.value.name
	}
	if (!newGuest.guest_name.trim()) throw new Error('Please enter the new guest’s name.')
	const doc = await guestInsert.submit({
		doc: { doctype: 'Guest', guest_name: newGuest.guest_name, phone: newGuest.phone, email: newGuest.email },
	})
	return doc.name
}

// ---- Room lines ----
interface RoomLine {
	room_type: string
	room: string
	arrival: string
	departure: string
	adults: number
	children: number
	rate: number | null
}

function makeLine(overrides: Partial<RoomLine> = {}): RoomLine {
	return {
		room_type: '',
		room: '',
		arrival: todayIso(),
		departure: addDaysIso(todayIso(), 1),
		adults: 1,
		children: 0,
		rate: null,
		...overrides,
	}
}

// Prefill the first line from Availability.vue's "Book" action
// (?room_type=...&arrival=...&departure=...), if present.
function queryStr(value: unknown): string {
	return Array.isArray(value) ? (value[0] ?? '') : ((value as string) ?? '')
}
const prefillRoomType = queryStr(route.query.room_type)
const prefillArrival = queryStr(route.query.arrival)
const prefillDeparture = queryStr(route.query.departure)

const lines = reactive<RoomLine[]>([
	makeLine({
		room_type: prefillRoomType,
		arrival: prefillArrival || todayIso(),
		departure: prefillDeparture || addDaysIso(todayIso(), 1),
	}),
])

// Pick up the prefilled room type's base rate once Room Types have loaded
// (they're fetched async, so this can't happen inline at line-creation time).
watch(
	() => roomTypes.data,
	(data) => {
		if (!prefillRoomType || !data) return
		const match = data.find((rt: { name: string }) => rt.name === prefillRoomType)
		if (match && lines[0]?.room_type === prefillRoomType) lines[0].rate = match.base_rate
	},
)

function onRoomTypeSelect(line: RoomLine, value: string) {
	line.room_type = value
	const match = (roomTypes.data ?? []).find((rt: { name: string }) => rt.name === value)
	if (match) line.rate = match.base_rate
}

function addLine() {
	lines.push(makeLine())
}

function removeLine(index: number) {
	lines.splice(index, 1)
}

// ---- Source / notes ----
const SOURCES = ['Walk-in', 'Phone', 'Email', 'Direct', 'Other']
const source = ref('Direct')
const notes = ref('')

// ---- Submit ----
const createResourceAction = createResource({
	url: 'pp2_hotel.api.reservations.create_reservation',
	method: 'POST',
	auto: false,
})
const confirmResourceAction = createResource({
	url: 'pp2_hotel.api.reservations.confirm_reservation',
	method: 'POST',
	auto: false,
})

const formError = ref<string | null>(null)
const submitting = ref<'draft' | 'confirm' | null>(null)

function validate() {
	if (!property.value) throw new Error('No property is configured yet.')
	if (!lines.length) throw new Error('Add at least one room.')
	for (const line of lines) {
		if (!line.room_type) throw new Error('Every room line needs a room type.')
		if (!line.arrival || !line.departure) throw new Error('Every room line needs arrival and departure dates.')
		if (line.departure <= line.arrival) throw new Error('Departure must be after arrival.')
	}
}

async function buildPayload(guest: string) {
	return {
		guest,
		property: property.value,
		source: source.value,
		notes: notes.value || undefined,
		rooms: lines.map((line) => ({
			room_type: line.room_type,
			room: line.room || undefined,
			arrival: line.arrival,
			departure: line.departure,
			adults: Number(line.adults) || 0,
			children: Number(line.children) || 0,
			rate: line.rate != null ? Number(line.rate) : undefined,
		})),
	}
}

async function saveDraft() {
	formError.value = null
	submitting.value = 'draft'
	try {
		validate()
		const guest = await resolveGuest()
		const payload = await buildPayload(guest)
		const name = await createResourceAction.submit(payload)
		toast.success('Reservation saved as draft.')
		router.push(`/reservations/${name}`)
	} catch (error) {
		formError.value = getErrorMessage(error, 'Could not save this reservation.')
	} finally {
		submitting.value = null
	}
}

async function createAndConfirm() {
	formError.value = null
	submitting.value = 'confirm'
	try {
		validate()
		const guest = await resolveGuest()
		const payload = await buildPayload(guest)
		const name = await createResourceAction.submit(payload)
		await confirmResourceAction.submit({ reservation: name })
		toast.success('Reservation created and confirmed.')
		router.push(`/reservations/${name}`)
	} catch (error) {
		formError.value = getErrorMessage(error, 'Could not create and confirm this reservation.')
	} finally {
		submitting.value = null
	}
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">New Reservation</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Book one or more rooms for a guest.</p>
		</div>

		<div class="max-w-3xl space-y-6">
			<!-- Guest -->
			<section class="space-y-3 rounded-app-md border border-app-border bg-app-surface p-4">
				<div class="flex items-center justify-between">
					<h2 class="text-[14px] font-semibold leading-[20px] text-app-text">Guest</h2>
					<div class="flex gap-1 rounded-app-sm border border-app-border p-0.5">
						<button
							type="button"
							class="rounded-app-sm px-3 py-1 text-[13px] font-medium"
							:class="guestMode === 'existing' ? 'bg-app-primary text-white' : 'text-app-muted'"
							@click="guestMode = 'existing'"
						>
							Existing Guest
						</button>
						<button
							type="button"
							class="rounded-app-sm px-3 py-1 text-[13px] font-medium"
							:class="guestMode === 'new' ? 'bg-app-primary text-white' : 'text-app-muted'"
							@click="guestMode = 'new'"
						>
							New Guest
						</button>
					</div>
				</div>

				<template v-if="guestMode === 'existing'">
					<div v-if="selectedGuest" class="flex items-center justify-between rounded-app-sm border border-app-border p-3">
						<div>
							<p class="text-[14px] font-medium leading-[20px] text-app-text">{{ selectedGuest.guest_name }}</p>
							<p class="text-[13px] leading-[16px] text-app-muted">
								{{ [selectedGuest.phone, selectedGuest.email].filter(Boolean).join(' · ') || 'No contact details' }}
							</p>
						</div>
						<Button variant="outline" @click="selectedGuest = null">Change</Button>
					</div>
					<template v-else>
						<FormControl
							v-model="guestQuery"
							type="text"
							label="Search Guest"
							variant="outline"
							placeholder="Type at least 2 letters of the guest's name…"
						/>
						<ul v-if="guestSearch.data?.length" class="divide-y divide-app-border rounded-app-sm border border-app-border">
							<li
								v-for="guest in guestSearch.data"
								:key="guest.name"
								class="cursor-pointer px-3 py-2 text-[13px] hover:bg-app-bg"
								@click="selectGuest(guest)"
							>
								<span class="font-medium text-app-text">{{ guest.guest_name }}</span>
								<span class="text-app-muted"> — {{ [guest.phone, guest.email].filter(Boolean).join(' · ') }}</span>
							</li>
						</ul>
						<EmptyState
							v-else-if="guestQuery.trim().length >= 2 && !guestSearch.list.loading"
							title="No matching guests"
							description="Try a different search, or switch to New Guest."
						/>
					</template>
				</template>
				<template v-else>
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
						<FormControl v-model="newGuest.guest_name" type="text" label="Guest Name" variant="outline" required />
						<FormControl v-model="newGuest.phone" type="tel" label="Phone" variant="outline" />
						<FormControl v-model="newGuest.email" type="email" label="Email" variant="outline" />
					</div>
				</template>
			</section>

			<!-- Rooms -->
			<section class="space-y-4 rounded-app-md border border-app-border bg-app-surface p-4">
				<div class="flex items-center justify-between">
					<h2 class="text-[14px] font-semibold leading-[20px] text-app-text">Rooms</h2>
					<Button variant="outline" @click="addLine">Add Room</Button>
				</div>

				<div
					v-for="(line, index) in lines"
					:key="index"
					class="space-y-3 rounded-app-sm border border-app-border p-3"
				>
					<div class="flex items-center justify-between">
						<p class="text-[12px] font-semibold uppercase tracking-wide text-app-muted">Room {{ index + 1 }}</p>
						<button
							v-if="lines.length > 1"
							type="button"
							class="text-[13px] text-app-danger hover:underline"
							@click="removeLine(index)"
						>
							Remove
						</button>
					</div>
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
						<FormControl
							:model-value="line.room_type"
							type="select"
							label="Room Type"
							variant="outline"
							:options="[{ label: 'Select a room type…', value: '' }, ...roomTypeOptions]"
							@update:model-value="(value: string) => onRoomTypeSelect(line, value)"
						/>
						<FormControl v-model="line.arrival" type="date" label="Arrival" variant="outline" />
						<FormControl v-model="line.departure" type="date" label="Departure" variant="outline" />
						<FormControl v-model="line.adults" type="number" label="Adults" variant="outline" />
						<FormControl v-model="line.children" type="number" label="Children" variant="outline" />
						<FormControl v-model="line.rate" type="number" label="Rate" variant="outline" />
						<FormControl
							v-model="line.room"
							type="text"
							label="Room (optional)"
							variant="outline"
							description="Leave blank to assign a room at check-in"
						/>
					</div>
				</div>
			</section>

			<!-- Source / Notes -->
			<section class="space-y-3 rounded-app-md border border-app-border bg-app-surface p-4">
				<FormControl v-model="source" type="select" label="Source" variant="outline" :options="SOURCES" />
				<FormControl v-model="notes" type="textarea" label="Notes" variant="outline" />
			</section>

			<p v-if="formError" class="text-[13px] leading-[16px] text-app-danger">{{ formError }}</p>

			<div class="flex justify-end gap-2">
				<Button variant="outline" :loading="submitting === 'draft'" @click="saveDraft">Save as Draft</Button>
				<Button variant="solid" :loading="submitting === 'confirm'" @click="createAndConfirm">Create &amp; Confirm</Button>
			</div>
		</div>
	</PageContainer>
</template>
