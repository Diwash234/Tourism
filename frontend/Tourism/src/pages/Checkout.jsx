import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { FiShoppingBag, FiTrash2 } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import { basketTotal, clearTripBasket, getTripBasket, removeFromTripBasket } from "../utils/tripBasket"

export default function Checkout() {
  const { user, isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [items, setItems] = useState(getTripBasket())
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [form, setForm] = useState({
    guest_name: user?.full_name || `${user?.first_name || ""} ${user?.last_name || ""}`.trim(),
    guest_email: user?.email || "",
    guest_phone: user?.phone_number || "",
    travelers: 1,
    start_date: "",
    notes: "",
    payment_method: "request",
  })

  const total = useMemo(() => basketTotal(items), [items])
  const remove = (id) => setItems(removeFromTripBasket(id))

  const submit = async (event) => {
    event.preventDefault()
    if (!items.length) return showToast("Add at least one offer to the trip basket", "info")
    setBusy(true)
    try {
      const { data } = await userApi.checkoutMarketplace({
        ...form,
        items: items.map((row) => ({ listing_id: row.listing_id, quantity: row.quantity })),
      })
      setResult(data)
      setItems(clearTripBasket())
      showToast(data.message || "Booking request saved", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not submit trip request", "error")
    } finally {
      setBusy(false)
    }
  }

  const reference = result?.order?.reference
  const titles = (result?.order?.items || []).map((item) => item.title).join(" & ")
  const days = result?.order?.duration_days

  return (
    <div className="container-app py-10" data-testid="checkout-page">
      <PageHeader
        title="Review & Request Booking"
        subtitle="No payment is being processed on Nepal Tourism at this stage. Card numbers are never accepted here."
        icon={FiShoppingBag}
        theme="gold"
      />

      {result ? (
        <div className="card-base p-6 max-w-2xl space-y-3" data-testid="checkout-result">
          <h2 className="text-xl font-black" data-testid="checkout-reference">Your trip request {result.order?.reference}</h2>
          <p className="text-slate-600">{titles}{days ? ` — ${days} days` : ""}</p>
          <p className="font-bold">Status: {result.order?.status_label || result.order?.status}</p>
          <p className="text-slate-600">{result.message}</p>
          <p className="font-bold">Total NPR {result.order?.total_npr}</p>
          {form.payment_method === "external" && (
            <p className="text-sm text-slate-600">Payment will be completed securely through the partner.</p>
          )}
          {(result.external_links || []).length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-bold">Continue on partner sites:</p>
              {result.external_links.map((link) => (
                <a key={link.url} href={link.url} target="_blank" rel="noreferrer" className="block text-emerald-800 font-semibold underline">{link.title}</a>
              ))}
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            {reference && <Link to={`/trip/${reference}`} className="btn-primary inline-flex">Track this request</Link>}
            <Link to="/packages" className="btn-outline inline-flex">Add more offers</Link>
          </div>
        </div>
      ) : (
        <div className="grid lg:grid-cols-[1.2fr_1fr] gap-6">
          <section className="card-base p-5 space-y-3">
            <h2 className="font-black">Trip basket</h2>
            {items.length === 0 && (
              <p className="text-sm text-slate-600">Nothing here yet. <Link to="/packages" className="font-bold text-emerald-800">Browse packages</Link>.</p>
            )}
            {items.map((row) => (
              <div key={row.listing_id} className="flex justify-between gap-3 border-b border-slate-100 pb-3">
                <div>
                  <p className="font-bold">{row.title}</p>
                  <p className="text-xs text-slate-500">{row.quantity} × NPR {Number(row.price_npr).toLocaleString()}</p>
                </div>
                <button type="button" onClick={() => remove(row.listing_id)} className="text-rose-700" aria-label="Remove"><FiTrash2 /></button>
              </div>
            ))}
            <p className="text-xl font-black">Total NPR {total.toLocaleString()}</p>
          </section>
          <form onSubmit={submit} className="card-base p-5 space-y-3" data-testid="checkout-form">
            {!isAuthenticated && (
              <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-xl p-3">
                You can request as a guest, or <Link to="/login?next=/checkout" className="font-bold underline">log in</Link> so we can attach the request to your account.
              </p>
            )}
            <input className="input-field" required name="guest_name" data-testid="checkout-name" placeholder="Traveller name" value={form.guest_name} onChange={(e) => setForm({ ...form, guest_name: e.target.value })} />
            <input className="input-field" required type="email" name="guest_email" data-testid="checkout-email" placeholder="Email" value={form.guest_email} onChange={(e) => setForm({ ...form, guest_email: e.target.value })} />
            <input className="input-field" name="guest_phone" data-testid="checkout-phone" placeholder="Phone" value={form.guest_phone} onChange={(e) => setForm({ ...form, guest_phone: e.target.value })} />
            <div className="grid grid-cols-2 gap-2">
              <input className="input-field" type="number" min="1" max="20" value={form.travelers} onChange={(e) => setForm({ ...form, travelers: e.target.value })} />
              <input className="input-field" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
            </div>
            <textarea className="input-field" placeholder="Notes for the operator" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            <fieldset className="space-y-2 text-sm">
              <legend className="font-bold text-slate-900">How do you want to proceed?</legend>
              <label className="flex gap-2 items-start">
                <input type="radio" name="pay" checked={form.payment_method === "request"} onChange={() => setForm({ ...form, payment_method: "request" })} />
                <span>Request to book — pay later with the operator. No payment is being processed on Nepal Tourism at this stage.</span>
              </label>
              <label className="flex gap-2 items-start">
                <input type="radio" name="pay" checked={form.payment_method === "external"} onChange={() => setForm({ ...form, payment_method: "external" })} />
                <span>Payment will be completed securely through the partner (HTTPS site only).</span>
              </label>
            </fieldset>
            <p className="text-xs text-slate-500">Do not enter card numbers, CVV or PAN here. Those fields are rejected on purpose.</p>
            <button type="submit" disabled={busy || !items.length} data-testid="checkout-submit" className="btn-primary w-full">{busy ? "Sending…" : "Request booking"}</button>
          </form>
        </div>
      )}
    </div>
  )
}
