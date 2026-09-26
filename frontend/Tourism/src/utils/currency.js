// Currency display backed by the official NRB rate snapshot returned by
// /api/v1/fx/rates/. There is no hard-coded fallback rate: when a rate is
// unavailable the amount is reported as unavailable instead of guessed.

export const DISPLAY_CURRENCIES = {
  NPR: { symbol: "रू", label: "Nepali Rupee" },
  USD: { symbol: "$", label: "US Dollar" },
  EUR: { symbol: "€", label: "Euro" },
  GBP: { symbol: "£", label: "British Pound" },
  INR: { symbol: "₹", label: "Indian Rupee" },
  AUD: { symbol: "A$", label: "Australian Dollar" },
  CAD: { symbol: "C$", label: "Canadian Dollar" },
  CNY: { symbol: "¥", label: "Chinese Yuan" },
  JPY: { symbol: "¥", label: "Japanese Yen" },
}

export const NATIONALITY_OPTIONS = [
  { value: "foreign", label: "Foreign national" },
  { value: "saarc", label: "SAARC national (Bangladesh, Bhutan, India, Maldives, Pakistan, Sri Lanka, Afghanistan)" },
  { value: "chinese", label: "Chinese national" },
  { value: "nepali", label: "Nepali citizen" },
]

/** NPR per 1 unit of `code` from an NRB rates payload, or null. */
export function nprPerUnit(rates, code) {
  if (code === "NPR") return 1
  const entry = rates?.currencies?.[code]
  const value = entry ? Number(entry.npr_per_unit) : NaN
  return Number.isFinite(value) && value > 0 ? value : null
}

/** Convert an NPR amount into `code`; null when not convertible. */
export function fromNpr(amountNpr, code, rates) {
  if (amountNpr == null || !Number.isFinite(Number(amountNpr))) return null
  const rate = nprPerUnit(rates, code)
  return rate ? Number(amountNpr) / rate : null
}

export function formatCurrency(amount, code) {
  if (amount == null || !Number.isFinite(Number(amount))) return "Unavailable"
  const c = DISPLAY_CURRENCIES[code] || { symbol: `${code} ` }
  const digits = Math.abs(amount) < 100 && code !== "NPR" && code !== "JPY" ? 2 : 0
  return `${c.symbol}${Number(amount).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 })}`
}

export function rateLabel(rates) {
  if (!rates?.available) return "Official NRB exchange rate unavailable — showing NPR/USD only where the estimate provides them."
  const stale = rates.stale ? ` (${rates.age_days} days old — refresh pending)` : ""
  return `${rates.source} ${rates.rate_type || "rate"} as of ${rates.rate_date}${stale}`
}
