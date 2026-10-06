import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  FiCheck, FiDownload, FiShield, FiClock, FiAlertCircle,
  FiSmartphone, FiDollarSign, FiRefreshCw, FiX,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import useToast from "../hooks/useToast"
import bookingApi from "../api/bookingApi"
import userApi from "../api/userApi"

/**
 * Payments & bookings.
 *
 * This page was a simulation. It showed a hardcoded booking ("Pokhara - 3
 * Nights", Himalaya Resort & Spa, NPR 26,265), offered Stripe / eSewa /
 * Khalti payment methods that have no integration anywhere in this codebase,
 * collected card number / expiry / CVV into component state, then decided the
 * outcome with `Math.random() > 0.1` and printed a receipt with an invented
 * "NYP-XXXX" reference. Booking has no `reference` column at all.
 *
 * Two things were wrong with that beyond being fake:
 *   - it gathered card details it had nowhere to send, while
 *     MarketplaceCheckoutView explicitly rejects card fields server-side
 *     ("Do not send card numbers, CVV or expiry details here");
 *   - it told travellers "A confirmation email has been sent" when no email
 *     was ever sent.
 *
 * It is now a real ledger: the traveller's actual bookings and marketplace
 * orders, with the real statuses the database holds, and a receipt generated
 * from the real record. There is no card form because there is no payment
 * service provider wired up -- payment is request-to-book, confirmed by the
 * partner, exactly as the backend models it.
 */

const STATUS_STYLES = {
  pending: "bg-amber-100 text-amber-800",
  requested: "bg-amber-100 text-amber-800",
  confirmed: "bg-emerald-100 text-emerald-800",
  completed: "bg-sky-100 text-sky-800",
  cancelled: "bg-gray-200 text-gray-700",
  archived: "bg-gray-200 text-gray-700",
  external: "bg-violet-100 text-violet-800",
  rejected: "bg-rose-100 text-rose-800",
}

const STATUS_MEANING = {
  pending: "Waiting for the hotel to confirm.",
  requested: "Request sent. The partner confirms by email — nothing has been charged.",
  confirmed: "Confirmed by the provider.",
  completed: "Stay completed.",
  cancelled: "Cancelled.",
  archived: "Closed.",
  external: "Paid directly with the provider.",
  rejected: "Declined by the provider.",
}

const statusBadge = (status) =>
  `px-2 py-0.5 rounded-full text-xs font-semibold ${STATUS_STYLES[status] || "bg-gray-100 text-gray-700"}`

const PAYMENT_METHODS = [
  { id: "request", label: "Request to book", icon: FiDollarSign, description: "No card needed — the partner confirms by email" },
  { id: "external", label: "Pay at the provider", icon: FiSmartphone, description: "You settle directly with the provider" },
]

/** Builds a plain-text receipt from the real record -- no invented fields. */
function receiptText(kind, record) {
  const lines = kind === "hotel"
    ? [
        ["Booking id", record.id],
        ["Status", record.status],
        ["Hotel", record.hotel_name],
        ["Check-in", record.check_in],
        ["Check-out", record.check_out],
        ["Guests", record.guests],
        ["Total", record.total_price != null ? `${record.currency} ${record.total_price}` : "Not priced"],
        ["Booked at", record.created_at],
      ]
    : [
        ["Reference", record.reference || `order-${record.id}`],
        ["Status", record.status_label || record.status],
        ["Offer", record.headline],
        ["Items", (record.items || []).map((i) => `${i.quantity} x ${i.title}`).join(", ")],
        ["Travellers", record.travelers],
        ["Start date", record.start_date || "Not set"],
        ["Subtotal", record.subtotal_npr ? `${record.currency} ${record.subtotal_npr}` : "—"],
        ["Total", record.total_npr ? `${record.currency} ${record.total_npr}` : "—"],
        ["Payment method", record.payment_method],
        ["Booked at", record.created_at],
      ]
  return [
    kind === "hotel" ? "BOOKING RECEIPT" : "REQUEST RECEIPT",
    "=".repeat(40),
    ...lines.map(([k, v]) => `${(k + ":").padEnd(16)} ${v ?? "—"}`),
    "",
    "This receipt reflects a request recorded on Nepal Yatra. It is not a card",
    "payment receipt — no card details are collected or stored by this site.",
  ].join("\n")
}

function downloadReceipt(kind, record) {
  const blob = new Blob([receiptText(kind, record)], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = `${kind === "hotel" ? "booking" : "request"}-${record.id}.txt`
  link.click()
  URL.revokeObjectURL(url)
}

const Payment = () => {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [bookings, setBookings] = useState([])
  const [orders, setOrders] = useState([])
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      // Both lists are optional: a failure in one must not blank the other.
      const [bookingRes, orderRes] = await Promise.allSettled([
        bookingApi.getMyBookings(),
        userApi.listMarketplaceOrders(),
      ])

      if (bookingRes.status === "fulfilled") {
        const d = bookingRes.value.data
        setBookings(Array.isArray(d) ? d : d?.results || [])
      } else {
        setBookings([])
      }

      if (orderRes.status === "fulfilled") {
        const d = orderRes.value.data
        setOrders(Array.isArray(d) ? d : d?.results || [])
      } else {
        setOrders([])
      }

      if (bookingRes.status === "rejected" && orderRes.status === "rejected") {
        setError(
          bookingRes.reason?.response?.data?.detail ||
            "We could not load your bookings right now."
        )
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const act = async (id, action) => {
    setBusyId(`${action}-${id}`)
    try {
      if (action === "cancel") await bookingApi.cancelBooking(id)
      else await bookingApi.confirmBooking(id)
      showToast(action === "cancel" ? "Booking cancelled" : "Booking confirmed", "success")
      await load()
    } catch (err) {
      showToast(err?.response?.data?.detail || `Could not ${action} that booking`, "error")
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <Loader fullScreen text="Loading your bookings..." />

  const isEmpty = bookings.length === 0 && orders.length === 0

  return (
    <div className="ny-page mx-auto w-full max-w-5xl space-y-6">
      <PageHeader
        title="Payments & Bookings"
        subtitle="Every request and booking recorded against your account."
        icon={FiShield}
        actions={
          <button onClick={load} className="btn-outline flex items-center gap-2 text-sm">
            <FiRefreshCw size={16} /> Refresh
          </button>
        }
      />

      {error && (
        <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <FiAlertCircle className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* How payment actually works here — stated plainly rather than implied
          by a card form that cannot submit anywhere. */}
      <section className="card-base p-5">
        <h2 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <FiShield size={18} className="text-emerald-600" />
          How payment works
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Nepal Yatra uses request-to-book. We never ask for or store card numbers,
          CVV or expiry details, so nothing is charged until the hotel or partner
          confirms your request.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PAYMENT_METHODS.map(({ id, label, icon: Icon, description }) => (
            <div key={id} className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl">
              <Icon className="mt-0.5 text-emerald-600 shrink-0" />
              <div>
                <p className="font-medium text-sm">{label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {isEmpty ? (
        <EmptyState
          title="No bookings yet"
          subtitle="Requests you send from the marketplace or hotels page will appear here with their real status."
          action={<Link to="/marketplace" className="btn-primary">Browse the marketplace</Link>}
        />
      ) : null}

      {bookings.length > 0 && (
        <section className="card-base p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Hotel bookings</h2>
          <div className="space-y-3">
            {bookings.map((b) => (
              <article key={b.id} className="p-4 border border-gray-200 rounded-xl">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold">{b.hotel_name || `Hotel #${b.hotel}`}</h3>
                      <span className={statusBadge(b.status)}>{b.status}</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {b.check_in} → {b.check_out} · {b.guests} guest{b.guests === 1 ? "" : "s"}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {STATUS_MEANING[b.status] || "Status recorded by the provider."}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-bold text-lg text-gray-900">
                      {b.total_price != null ? `${b.currency} ${Number(b.total_price).toLocaleString()}` : "Not priced"}
                    </p>
                    <p className="text-xs text-gray-500">booking #{b.id}</p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-3">
                  <button
                    type="button"
                    onClick={() => downloadReceipt("hotel", b)}
                    className="btn-outline text-xs flex items-center gap-1"
                  >
                    <FiDownload size={14} /> Receipt
                  </button>
                  {b.status === "pending" && (
                    <>
                      <button
                        type="button"
                        disabled={busyId === `confirm-${b.id}`}
                        onClick={() => act(b.id, "confirm")}
                        className="btn-primary text-xs flex items-center gap-1 disabled:opacity-50"
                      >
                        <FiCheck size={14} /> Confirm
                      </button>
                      <button
                        type="button"
                        disabled={busyId === `cancel-${b.id}`}
                        onClick={() => act(b.id, "cancel")}
                        className="btn-outline text-xs flex items-center gap-1 disabled:opacity-50"
                      >
                        <FiX size={14} /> Cancel
                      </button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {orders.length > 0 && (
        <section className="card-base p-5">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FiClock size={18} className="text-violet-600" />
            Marketplace requests
          </h2>
          <div className="space-y-3">
            {orders.map((o) => (
              <article key={o.id} className="p-4 border border-gray-200 rounded-xl">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold">{o.headline || `Request #${o.id}`}</h3>
                      <span className={statusBadge(o.status)}>{o.status_label || o.status}</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      <span className="font-mono">{o.reference}</span>
                      {" · "}{o.travelers} traveller{o.travelers === 1 ? "" : "s"}
                      {o.start_date ? ` · from ${o.start_date}` : ""}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {STATUS_MEANING[o.status] || "Status recorded by the partner."}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-bold text-lg text-gray-900">
                      {o.total_npr ? `${o.currency} ${Number(o.total_npr).toLocaleString()}` : "—"}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => downloadReceipt("order", o)}
                    className="btn-outline text-xs flex items-center gap-1 shrink-0"
                  >
                    <FiDownload size={14} /> Receipt
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

export default Payment