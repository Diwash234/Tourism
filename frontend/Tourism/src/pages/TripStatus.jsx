import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { FiClipboard } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import EmptyState from "../components/common/EmptyState"
import userApi from "../api/userApi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"

const LABELS = {
  requested: "Requested",
  under_review: "Under Review",
  confirmed: "Confirmed",
  cancelled: "Cancelled",
  external: "Sent to partner site",
}

export default function TripStatus() {
  const { reference: routeRef } = useParams()
  const { user, isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [form, setForm] = useState({ reference: routeRef || "", email: user?.email || "" })
  const [order, setOrder] = useState(null)
  const [mine, setMine] = useState([])
  const [mineLoading, setMineLoading] = useState(false)
  const [lookupError, setLookupError] = useState("")
  const [busy, setBusy] = useState(false)

  const lookup = async (event) => {
    event?.preventDefault()
    if (!form.reference || !form.email) return showToast("Reference and email are required", "info")
    setBusy(true)
    setLookupError("")
    try {
      const { data } = await userApi.lookupMarketplaceOrder(form.reference, form.email)
      setOrder(data.order)
    } catch (error) {
      setOrder(null)
      setLookupError(error.response?.data?.detail || "No matching request was found.")
      showToast(error.response?.data?.detail || "No matching request", "error")
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect
    // flush (react-hooks/set-state-in-effect) without changing behavior.
    const t = setTimeout(() => {
    if (routeRef && form.email) lookup()
    if (isAuthenticated) {
      setMineLoading(true)
      userApi.listMarketplaceOrders().then(({ data }) => setMine(data.results || [])).catch(() => { setMine([]); setLookupError("Your saved requests could not be loaded.") }).finally(() => setMineLoading(false))
    }
     
    }, 0)
    return () => clearTimeout(t)
  }, [routeRef, isAuthenticated])

  const card = (row) => {
    const titles = (row.items || []).map((item) => item.title).join(" & ")
    return (
      <article key={row.id || row.reference} className="card-base p-5 space-y-2" data-testid="trip-result">
        <p className="text-xs font-black uppercase text-emerald-800">Trip request {row.reference}</p>
        <h2 className="text-xl font-black">{titles || row.headline}</h2>
        <p className="text-[var(--ny-text-secondary)]">{row.duration_days ? `${row.duration_days} day${row.duration_days === 1 ? "" : "s"}` : "Duration unavailable"}{row.total_npr != null ? ` · NPR ${Number(row.total_npr).toLocaleString()}` : " · Total unavailable"}</p>
        <p className="font-bold">Status: {LABELS[row.status] || row.status_label || row.status || "Status unavailable"}</p>
        <ul className="text-sm text-slate-600 space-y-1">
          {(row.items || []).map((item) => <li key={item.id}>{item.quantity} × {item.title}</li>)}
        </ul>
        <p className="text-xs text-slate-500">No payment is processed on Nepal Yatra. Confirm payment arrangements directly with the operator.</p>
      </article>
    )
  }

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8" data-testid="trip-page">
      <PageHeader
        title="Trip request status"
        subtitle="Look up a request with the reference and email used at checkout. If you made a guest request, keep the confirmation details provided by the operator. Statuses are Requested → Under Review → Confirmed or Cancelled."
        icon={FiClipboard}
        theme="gold"
      />
      <form onSubmit={lookup} className="card-base p-5 max-w-xl grid sm:grid-cols-[1fr_1fr_auto] gap-2" data-testid="trip-lookup-form">
        <input className="input-field" name="reference" aria-label="Request reference" data-testid="trip-reference" placeholder="Reference (e.g. NP260823ABC123)" value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
        <input className="input-field" type="email" name="email" aria-label="Email used at checkout" data-testid="trip-email" placeholder="Email used at checkout" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <button type="submit" disabled={busy} data-testid="trip-lookup" className="btn-primary">{busy ? "Looking…" : "Look up"}</button>
      </form>
      {lookupError && <p className="rounded-[var(--ny-radius-md)] border border-[#E9B9B9] bg-[var(--ny-soft-red)] p-3 text-sm text-[var(--ny-danger)]" role="alert">{lookupError}</p>}
       {order && card(order)}
       {isAuthenticated && mineLoading && <p className="text-sm text-[var(--ny-text-secondary)]">Loading your requests…</p>}
       {isAuthenticated && !mineLoading && !order && mine.length === 0 && <EmptyState title="No saved requests" subtitle="Requests linked to your account will appear here after you submit one." action={<Link to="/packages" className="ny-btn ny-btn-primary">Browse packages</Link>} />}
      {mine.length > 0 && (
        <section className="space-y-3">
          <h3 className="font-black">Your requests</h3>
          {mine.map(card)}
        </section>
      )}
      <Link to="/packages" className="text-sm font-bold text-emerald-800">Browse packages</Link>
    </div>
  )
}
