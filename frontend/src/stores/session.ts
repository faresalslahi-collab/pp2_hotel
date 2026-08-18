import { defineStore } from 'pinia'
import { call } from 'frappe-ui'

// Boot data is injected as individual `window.*` globals by the backend's
// www/pp2_hotel.py entrypoint (a Jinja loop: `window["{{ key }}"] =
// {{ boot[key] | tojson }}`), mirroring the exact pattern gcc_hr and qcore
// use in this same bench -- NOT a single `window.boot` object. csrf_token,
// user, full_name, user_image, roles, site_name are all present for a
// logged-in user; for a Guest (if the backend ever serves the shell to one)
// they degrade to empty/default values rather than being undefined.
declare global {
	interface Window {
		csrf_token?: string
		user?: string
		full_name?: string
		user_image?: string | null
		roles?: string[]
		site_name?: string
	}
}

function cleanWindowValue(value?: string | null): string {
	if (!value || value.startsWith('{{')) return ''
	return value
}

export const useSessionStore = defineStore('session', {
	state: () => ({
		user: '' as string,
		fullName: '' as string,
		userImage: null as string | null,
		roles: [] as string[],
		siteName: '' as string,
		ready: false,
	}),
	actions: {
		// Defensive by design: the backend may still be migrating in parallel,
		// so this must never throw if `window.*` boot globals are missing --
		// it just leaves the store at its empty defaults instead of crashing
		// the whole SPA shell.
		bootstrap() {
			this.user = cleanWindowValue(window.user)
			this.fullName = cleanWindowValue(window.full_name) || this.user
			this.userImage = window.user_image ?? null
			this.roles = Array.isArray(window.roles) ? window.roles : []
			this.siteName = cleanWindowValue(window.site_name)
			this.ready = true
		},
		hasRole(role: string): boolean {
			return this.roles.includes(role)
		},
		hasAnyRole(roles: string[]): boolean {
			return roles.some((role) => this.roles.includes(role))
		},
		async logout() {
			await call('logout')
			window.location.href = '/login'
		},
	},
	getters: {
		isLoggedIn: (state) => Boolean(state.user) && state.user !== 'Guest',
		initials: (state) => (state.fullName || state.user || '?').slice(0, 2).toUpperCase(),
		isAdmin: (state) =>
			state.roles.includes('System Manager') || state.roles.includes('Hotel Administrator'),
	},
})
