<script setup lang="ts">
import { ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { BedDouble, ChevronDown, ChevronsLeft, ChevronsRight, X } from 'lucide-vue-next'
import AppSidebarNav from './AppSidebarNav.vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()

// App-switcher dropdown off the sidebar header's logo/wordmark -- same
// trigger/panel/onClickOutside shape as TopBar.vue's own user menu.
// "Workspaces"/"Website"/"Edit Sidebar"/"Display"/"Session Defaults" from
// Frappe Desk's own equivalent menu are deliberately left out: this is a
// standalone Vue SPA with no Workspace or Website-builder concept of its
// own, so those items would open onto nothing. "Desktop" (-> /app) and
// "Log out" are real, existing destinations; "Reload" is a real action.
const appMenuOpen = ref(false)
const appMenuRef = ref(null)
onClickOutside(appMenuRef, () => (appMenuOpen.value = false))

function reload() {
	window.location.reload()
}
</script>

<template>
	<!-- Desktop: fixed-in-flow sidebar, collapses to an icon-only ~w-16 rail. -->
	<aside
		class="hidden shrink-0 flex-col border-r border-app-border bg-app-surface transition-[width] duration-150 md:flex"
		:class="ui.sidebarCollapsed ? 'w-16' : 'w-64'"
	>
		<div ref="appMenuRef" class="relative shrink-0 border-b border-app-border">
			<button
				type="button"
				class="flex h-14 w-full items-center gap-2 px-4 hover:bg-app-bg"
				@click="appMenuOpen = !appMenuOpen"
			>
				<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-app-sm bg-app-primary text-white">
					<BedDouble :size="18" />
				</div>
				<span v-if="!ui.sidebarCollapsed" class="truncate text-[14px] font-semibold leading-[20px] text-app-text">
					PP2 Hotel
				</span>
				<ChevronDown v-if="!ui.sidebarCollapsed" :size="15" class="ml-auto shrink-0 text-app-muted" />
			</button>
			<div
				v-if="appMenuOpen"
				class="absolute left-2 top-full z-20 mt-1 w-48 rounded-app-md border border-app-border bg-app-surface py-1 shadow-lg"
			>
				<a
					href="/app"
					class="block w-full px-3 py-2 text-left text-[13px] leading-[16px] text-app-text hover:bg-app-bg"
				>
					Desktop
				</a>
				<button
					type="button"
					class="block w-full px-3 py-2 text-left text-[13px] leading-[16px] text-app-text hover:bg-app-bg"
					@click="reload"
				>
					Reload
				</button>
				<div class="my-1 border-t border-app-border"></div>
				<a
					href="/api/method/logout"
					class="block w-full px-3 py-2 text-left text-[13px] leading-[16px] text-app-text hover:bg-app-bg"
				>
					Log out
				</a>
			</div>
		</div>

		<AppSidebarNav :collapsed="ui.sidebarCollapsed" />

		<button
			type="button"
			class="flex shrink-0 items-center gap-2 border-t border-app-border px-4 py-3 text-[13px] text-app-muted hover:text-app-text"
			@click="ui.toggleSidebar()"
		>
			<component :is="ui.sidebarCollapsed ? ChevronsRight : ChevronsLeft" :size="18" class="shrink-0" />
			<span v-if="!ui.sidebarCollapsed">Collapse</span>
		</button>
	</aside>

	<!-- Mobile: off-canvas drawer with backdrop, toggled from TopBar's hamburger. -->
	<Teleport to="body">
		<Transition name="pp2-drawer-backdrop">
			<div v-if="ui.mobileNavOpen" class="fixed inset-0 z-50 bg-black/40 md:hidden" @click="ui.closeMobileNav()" />
		</Transition>
		<Transition name="pp2-drawer-panel">
			<aside
				v-if="ui.mobileNavOpen"
				class="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-app-surface shadow-xl md:hidden"
			>
				<div class="flex h-14 shrink-0 items-center justify-between border-b border-app-border px-4">
					<div class="flex items-center gap-2">
						<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-app-sm bg-app-primary text-white">
							<BedDouble :size="18" />
						</div>
						<span class="text-[14px] font-semibold leading-[20px] text-app-text">PP2 Hotel</span>
					</div>
					<button
						type="button"
						class="text-app-muted hover:text-app-text"
						aria-label="Close navigation"
						@click="ui.closeMobileNav()"
					>
						<X :size="20" />
					</button>
				</div>
				<AppSidebarNav :collapsed="false" @navigate="ui.closeMobileNav()" />
			</aside>
		</Transition>
	</Teleport>
</template>

<style scoped>
.pp2-drawer-backdrop-enter-active,
.pp2-drawer-backdrop-leave-active {
	transition: opacity 150ms ease;
}
.pp2-drawer-backdrop-enter-from,
.pp2-drawer-backdrop-leave-to {
	opacity: 0;
}

.pp2-drawer-panel-enter-active,
.pp2-drawer-panel-leave-active {
	transition: transform 150ms ease;
}
.pp2-drawer-panel-enter-from,
.pp2-drawer-panel-leave-to {
	transform: translateX(-100%);
}
</style>
