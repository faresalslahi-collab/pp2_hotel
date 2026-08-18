// Currency-code prefixed, not symbol-prefixed (matches the product spec's
// own examples verbatim: "SAR 28,450", "SAR 696.25") -- and drops
// unnecessary trailing ".00" for whole amounts while still showing cents
// when the value actually has them (folio balances, e.g. 696.25).
export function formatCurrency(amount: number, currency: string): string {
	const formatted = new Intl.NumberFormat('en-US', {
		minimumFractionDigits: 0,
		maximumFractionDigits: 2,
	}).format(amount)
	return `${currency} ${formatted}`
}

export function formatDate(value: string | null | undefined): string {
	if (!value) return '—'
	const date = new Date(value)
	if (Number.isNaN(date.getTime())) return value
	return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}
