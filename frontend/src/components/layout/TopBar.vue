<script setup lang="ts">
import { ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { Menu, Search, Bell } from 'lucide-vue-next'
import { useSessionStore } from '@/stores/session'
import { useUiStore } from '@/stores/ui'
import EmptyState from '@/components/ui/EmptyState.vue'

const session = useSessionStore()
const ui = useUiStore()

// Visual only this phase -- wiring a real cross-entity search (rooms,
// guests, reservations, folios) is a later-phase concern once those
// endpoints exist.
const searchQuery = ref('')

const notificationsOpen = ref(false)
const notificationsPanel = ref(null)
onClickOutside(notificationsPanel, () => (notificationsOpen.value = false))

const userMenuOpen = ref(false)
const userMenu = ref(null)
onClickOutside(userMenu, () => (userMenuOpen.value = false))
</script>

<template>
	<header class="flex h-14 shrink-0 items-center gap-3 border-b border-app-border bg-app-surface px-4 sm:px-6">
		<button
			type="button"
			class="text-app-muted hover:text-app-text md:hidden"
			aria-label="Open navigation"
			@click="ui.openMobileNav()"
		>
			<Menu :size="22" />
		</button>

		<div class="max-w-md flex-1">
			<div class="relative">
				<Search :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-app-muted" />
				<input
					v-model="searchQuery"
					type="text"
					placeholder="Search rooms, guests, reservations..."
					class="h-9 w-full rounded-app-sm border border-app-border bg-app-bg py-1.5 pl-9 pr-3 text-[13px] text-app-text placeholder:text-app-muted focus:border-app-primary focus:outline-none focus:ring-1 focus:ring-app-primary"
				/>
			</div>
		</div>

		<div class="ml-auto flex shrink-0 items-center gap-2">
			<div ref="notificationsPanel" class="relative">
				<button
					type="button"
					class="flex h-9 w-9 items-center justify-center rounded-app-sm text-app-muted hover:bg-app-bg hover:text-app-text"
					aria-label="Notifications"
					@click="notificationsOpen = !notificationsOpen"
				>
					<Bell :size="18" />
				</button>
				<div
					v-if="notificationsOpen"
					class="absolute right-0 top-11 z-10 w-72 rounded-app-md border border-app-border bg-app-surface py-1 shadow-lg"
				>
					<p class="px-3 pt-2 text-[13px] font-semibold leading-[16px] text-app-text">Notifications</p>
					<EmptyState title="No notifications yet" description="Alerts will show up here in a later phase." />
				</div>
			</div>

			<div ref="userMenu" class="relative">
				<button
					type="button"
					class="flex items-center gap-2 rounded-app-sm px-1.5 py-1 hover:bg-app-bg"
					@click="userMenuOpen = !userMenuOpen"
				>
					<span
						class="flex h-8 w-8 items-center justify-center rounded-full bg-app-primary text-[12px] font-medium text-white"
					>
						{{ session.initials }}
					</span>
					<span class="hidden text-[13px] font-medium leading-[16px] text-app-text sm:inline">
						{{ session.fullName }}
					</span>
				</button>
				<div
					v-if="userMenuOpen"
					class="absolute right-0 top-11 z-10 w-48 rounded-app-md border border-app-border bg-app-surface py-1 shadow-lg"
				>
					<div class="border-b border-app-border px-3 py-2">
						<p class="truncate text-[13px] font-medium leading-[16px] text-app-text">{{ session.fullName }}</p>
						<p class="truncate text-[12px] leading-[16px] text-app-muted">{{ session.user }}</p>
					</div>
					<a
						href="/api/method/logout"
						class="block w-full px-3 py-2 text-left text-[13px] leading-[16px] text-app-text hover:bg-app-bg"
					>
						Log out
					</a>
				</div>
			</div>
		</div>
	</header>
</template>
