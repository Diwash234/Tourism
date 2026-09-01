import { useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { FiClipboard } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
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
  const [busy, setBusy] = useState(false)

  const lookup = async (event) => {
    event?.preventDefault()
    if (!form.reference || !form.email) return showToast("Reference and email are required", "info")
    setBusy(true)
    try {
      const { data } = await userApi.lookupMarketplaceOrder(form.reference, form.email)
      setOrder(data.order)
    } catch (error) {
      setOrder(null)
      showToast(error.response?.data?.detail || "No matching request", "error")
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    if (routeRef && form.email) lookup()
    if (isAuthenticated) {
      userApi.listMarketplaceOrders().then(({ data }) => setMine(data.results || [])).catch(() => setMine([]))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeRef, isAuthenticated])

  const card = (row) => {
    const titles = (row.items || []).map((item) => item.title).join(" & ")
    return (
      <article key={row.id || row.reference} className="card-base p-5 space-y-2" data-testid="trip-result">
        <p className="text-xs font-black uppercase text-emerald-800">Trip request {row.reference}</p>
        <h2 className="text-xl font-black">{titles || row.headline}</h2>
        <p className="text-slate-600">{row.duration_days} day{row.duration_days === 1 ? "" : "s"} · NPR {row.total_npr}</p>
        <p className="font-bold">Status: {LABELS[row.status] || row.status_label || row.status}</p>
        <ul className="text-sm text-slate-600 space-y-1">
          {(row.items || []).map((item) => <li key={item.id}>{item.quantity} × {item.title}</li>)}
        </ul>
        <p className="text-xs text-slate-500">No payment is processed on Nepal Tourism. Pay with the operator if the request is confirmed.</p>
      </article>
    )
  }

  return (
    <div className="container-app py-10 space-y-6" data-testid="trip-page">
      <PageHeader
        title="Trip request status"
        subtitle="Look up a booking request with the reference we emailed you. Statuses are Requested → Under Review → Confirmed or Cancelled."
        icon={FiClipboard}
        theme="gold"
      />
      <form onSubmit={lookup} className="card-base p-5 max-w-xl grid sm:grid-cols-[1fr_1fr_auto] gap-2" data-testid="trip-lookup-form">
        <input className="input-field" name="reference" data-testid="trip-reference" placeholder="Reference (e.g. NP260823ABC123)" value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} />
        <input className="input-field" type="email" name="email" data-testid="trip-email" placeholder="Email used at checkout" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <button type="submit" disabled={busy} data-testid="trip-lookup" className="btn-primary">{busy ? "Looking…" : "Look up"}</button>
      </form>
      {order && card(order)}
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
