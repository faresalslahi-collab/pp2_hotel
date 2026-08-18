import { defineStore } from 'pinia'

const SIDEBAR_COLLAPSED_KEY = 'pp2_hotel:sidebarCollapsed'
const OPEN_SECTIONS_KEY = 'pp2_hotel:openSections'

function readBoolean(key: string, fallback: boolean): boolean {
	const raw = localStorage.getItem(key)
	return raw === null ? fallback : raw === 'true'
}

function readStringArray(key: string): string[] {
	try {
		const raw = localStorage.getItem(key)
		const parsed = raw ? JSON.parse(raw) : []
		return Array.isArray(parsed) ? parsed.filter((v) => typeof v === 'string') : []
	} catch {
		return []
	}
}

export const useUiStore = defineStore('ui', {
	state: () => ({
		// Desktop collapse-to-rail toggle (~w-16 icon-only rail when true).
		sidebarCollapsed: readBoolean(SIDEBAR_COLLAPSED_KEY, false),
		// Mobile off-canvas drawer open/closed -- not persisted, always starts closed.
		mobileNavOpen: false,
		// Which top-level nav sections the user has manually expanded. Note:
		// AppSidebar.vue additionally force-opens whichever section contains
		// the active route on top of this -- route-driven expansion always
		// wins visually, this store only remembers manual toggles.
		openSections: readStringArray(OPEN_SECTIONS_KEY) as string[],
	}),
	actions: {
		toggleSidebar() {
			this.sidebarCollapsed = !this.sidebarCollapsed
			localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(this.sidebarCollapsed))
		},
		openMobileNav() {
			this.mobileNavOpen = true
		},
		closeMobileNav() {
			this.mobileNavOpen = false
		},
		toggleSection(label: string) {
			if (this.openSections.includes(label)) {
				this.openSections = this.openSections.filter((l) => l !== label)
			} else {
				this.openSections = [...this.openSections, label]
			}
			localStorage.setItem(OPEN_SECTIONS_KEY, JSON.stringify(this.openSections))
		},
		// Idempotent open, distinct from toggleSection -- used when expanding
		// out of the collapsed rail (AppSidebarNav's onParentClick), where a
		// plain toggle would incorrectly close a section that happened to
		// already be in openSections from a previous session.
		openSection(label: string) {
			if (!this.openSections.includes(label)) {
				this.openSections = [...this.openSections, label]
				localStorage.setItem(OPEN_SECTIONS_KEY, JSON.stringify(this.openSections))
			}
		},
		isSectionOpen(label: string): boolean {
			return this.openSections.includes(label)
		},
	},
})
