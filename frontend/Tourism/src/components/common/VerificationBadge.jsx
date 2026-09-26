import { FiAlertCircle, FiCheckCircle } from "react-icons/fi"

/*
 * VerificationBadge
 *
 * Hotels, hospitals, police stations, banks/ATMs, pharmacies and restaurants
 * are imported from sourced datasets (OpenStreetMap, the MoHP hospital list,
 * project CSVs). Only rows an administrator has confirmed carry
 * `is_verified: true`. Everything else is still shown, because a real but
 * unconfirmed listing is more useful to a traveller than an empty page, but
 * it must never look verified. This badge is the single place that decides
 * the wording, so every page labels records the same way.
 *
 * Accepts either the model flag (`is_verified`) or the emergency directory
 * flag (`verified`).
 */
export const isRecordVerified = (record) =>
  Boolean(record && (record.is_verified === true || record.verified === true))

export default function VerificationBadge({ record, compact = false, className = "" }) {
  if (!record) return null
  const verified = isRecordVerified(record)
  const source = (record.source_name || record.source || "").toString().trim()
  const title = verified
    ? "An administrator has confirmed this listing."
    : `Imported listing that has not been confirmed by an administrator yet${source ? ` (source: ${source})` : ""}. Call ahead before relying on it.`

  const tone = verified
    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
    : "bg-amber-50 text-amber-900 border-amber-200"

  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-bold leading-tight ${tone} ${className}`}
    >
      {verified ? <FiCheckCircle aria-hidden="true" /> : <FiAlertCircle aria-hidden="true" />}
      {verified ? "Verified" : compact ? "Unverified" : "Unverified listing"}
      <span className="sr-only">. {title}</span>
    </span>
  )
}
