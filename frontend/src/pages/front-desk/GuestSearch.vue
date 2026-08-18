<script setup lang="ts">
// A richer, front-desk-facing sibling to NewReservation.vue's own inline
// guest picker: same debounce-since-createListResource-has-none workaround
// (see that file's own comment), but the backend (search_guests) also
// enriches each hit with front-desk-relevant context -- an in-house room,
// or a not-yet-checked-in Confirmed reservation -- so a result is
// something staff can act on directly. There is no Guest Profile page to
// click into yet (see DATABASE.md's Guest Document/Guest Preference
// entries), so a result with a room opens the existing Room Drawer and a
// result with a reservation opens the existing Reservation Detail page;
// a result with neither just shows its contact details inline.
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, FormControl } from 'frappe-ui'
import PageContainer from '@/components/layout/PageContainer.vue'
import RoomDrawer from '@/components/hotel/RoomDrawer.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatDate } from '@/utils/format'
import type { GuestSearchResult } from '@/types/hotel'

const router = useRouter()
const query = ref('')

const search = createResource({
	url: 'pp2_hotel.api.front_desk.search_guests',
	params: { query: '' },
	auto: false,
})

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(query, (value) => {
	if (searchTimer) clearTimeout(searchTimer)
	const trimmed = value.trim()
	if (trimmed.length < 2) {
		search.reset()
		return
	}
	searchTimer = setTimeout(() => {
		search.submit({ query: trimmed })
	}, 350)
})

const results = () => (search.data ?? []) as GuestSearchResult[]

const selectedRoom = ref<string | null>(null)
const drawerOpen = ref(false)

function openResult(result: GuestSearchResult) {
	if (result.room) {
		selectedRoom.value = result.room
		drawerOpen.value = true
	} else if (result.reservation) {
		router.push(`/reservations/${result.reservation}`)
	}
}

function closeDrawer() {
	drawerOpen.value = false
}
</script>

<template>
	<PageContainer>
		<div class="mb-6">
			<h1 class="text-[20px] font-semibold leading-[28px] text-app-text">Guest Search</h1>
			<p class="text-[13px] leading-[16px] text-app-muted">Find a guest by name, phone, or email.</p>
		</div>

		<FormControl
			v-model="query"
			type="text"
			placeholder="Search by name, phone, or email…"
			autocomplete="off"
			class="mb-6 max-w-md"
		/>

		<EmptyState
			v-if="query.trim().length >= 2 && !search.loading && results().length === 0"
			title="No guests found"
			description="Try a different name, phone number, or email."
		/>
		<EmptyState
			v-else-if="query.trim().length < 2"
			title="Start typing to search"
			description="Enter at least 2 characters of a guest's name, phone, or email."
		/>

		<div v-else class="space-y-2">
			<button
				v-for="result in results()"
				:key="result.name"
				type="button"
				class="flex w-full items-center justify-between rounded-app-md border border-app-border bg-app-surface p-3 text-left hover:border-app-primary"
				:class="{ 'cursor-default hover:border-app-border': !result.room && !result.reservation }"
				@click="openResult(result)"
			>
				<div>
					<p class="text-[14px] font-medium leading-[20px] text-app-text">{{ result.guest_name }}</p>
					<p class="text-[12px] leading-[16px] text-app-muted">
						{{ [result.phone, result.email].filter(Boolean).join(' · ') || 'No contact details on file' }}
					</p>
				</div>
				<div class="text-right">
					<p v-if="result.room_number" class="text-[12px] font-medium leading-[16px] text-app-primary">
						In-House · Room {{ result.room_number }}
					</p>
					<p v-else-if="result.reservation" class="text-[12px] font-medium leading-[16px] text-app-muted">
						Arriving {{ formatDate(result.reservation_arrival) }}
					</p>
				</div>
			</button>
		</div>

		<RoomDrawer :open="drawerOpen" :room-name="selectedRoom" @close="closeDrawer" />
	</PageContainer>
</template>
