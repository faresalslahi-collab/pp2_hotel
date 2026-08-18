// frappe-ui's frappeRequest (configured as the resourceFetcher in main.ts)
// wraps a non-2xx response into an Error with a `.messages` array of
// server-thrown message text (frappe.throw()/ValidationError etc. -- see
// node_modules/frappe-ui/src/utils/frappeRequest.js). This is the one bit of
// shared logic every Phase 2 write action (create/confirm/cancel/no-show/
// check-in) needs to turn that into a human-readable reason instead of a
// generic failure banner.
export function getErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
	const err = error as { messages?: string[]; message?: string } | null | undefined
	return err?.messages?.[0] || err?.message || fallback
}
