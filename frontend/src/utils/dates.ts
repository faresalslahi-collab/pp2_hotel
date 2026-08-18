// ISO (YYYY-MM-DD) date helpers for native <input type="date"> defaults --
// deliberately separate from utils/format.ts's formatDate, which produces a
// human-readable display string ("Aug 17, 2026"), not the machine-readable
// value these inputs bind to. Needed by both Availability.vue (default
// today -> tomorrow range) and NewReservation.vue (default room-line dates).
//
// Local-timezone-based throughout, deliberately -- toIsoDate() used to format
// via `date.toISOString()`, which is always UTC, while addDaysIso() parses
// `${isoDate}T00:00:00` (no offset suffix, so JS interprets it as *local*
// time) and calls the *local* `.setDate()`. Mixing the two silently shifted
// every date back by one day in any positive-UTC-offset timezone (this
// bench's own Asia/Riyadh, UTC+3, included) -- e.g. `addDaysIso(todayIso(),
// 0)` round-tripped local midnight through a UTC read and came back as
// *yesterday*. Caught in Phase 10 when ReservationCalendar.vue displayed
// "today" as literally the wrong date; NewReservation.vue/Availability.vue's
// default arrival/departure fields had the exact same latent bug, just
// harder to notice in a date <input> than in grid-header text.
export function toIsoDate(date: Date): string {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')
	return `${year}-${month}-${day}`
}

export function todayIso(): string {
	return toIsoDate(new Date())
}

export function addDaysIso(isoDate: string, days: number): string {
	const date = new Date(`${isoDate}T00:00:00`)
	date.setDate(date.getDate() + days)
	return toIsoDate(date)
}
