import { useState } from "react"
import { Link } from "react-router-dom"
import { FiBriefcase } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"

const KINDS = [
  ["hotel", "Hotel / stay"],
  ["operator", "Tour operator"],
  ["guide", "Local guide"],
  ["restaurant", "Restaurant"],
  ["transport", "Transport"],
  ["activity", "Activity provider"],
  ["agency", "Travel agency"],
]

const empty = { name: "", kind: "hotel", email: "", contact_name: "", phone: "", website: "", city: "", district: "", description: "" }

export default function Collaborate() {
  const { showToast } = useToast()
  const [form, setForm] = useState(empty)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    try {
      await userApi.applyMarketplacePartner(form)
      setDone(true)
      setForm(empty)
      showToast("Application received", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not send application", "error")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container-app py-10">
      <PageHeader
        title="Collaborate with Nepal Tourism"
        subtitle="Hotels, operators and guides can apply to list a stay, tour or package. An administrator reviews the application — no code required to go live."
        icon={FiBriefcase}
        theme="forest"
      />
      {done ? (
        <div className="card-base p-8 max-w-xl space-y-3">
          <h2 className="text-xl font-black">Application received</h2>
          <p className="text-slate-600">An administrator will review your business and can publish offers from the Packages & partners desk.</p>
          <Link to="/packages" className="btn-primary inline-flex">Browse current packages</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="card-base p-6 max-w-xl space-y-3">
          <input className="input-field" required placeholder="Business name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <select className="input-field" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            {KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          <input className="input-field" required type="email" placeholder="Work email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input-field" placeholder="Contact person" value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} />
          <input className="input-field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="input-field" placeholder="Website (https://…)" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" placeholder="City" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
            <input className="input-field" placeholder="District" value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} />
          </div>
          <textarea className="input-field min-h-[120px]" placeholder="What would you like to list?" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <p className="text-xs text-slate-500">If you include a website it must start with https://. Do not send card or payment credentials.</p>
          <button type="submit" disabled={busy} className="btn-primary w-full">{busy ? "Sending…" : "Apply to collaborate"}</button>
        </form>
      )}
    </div>
  )
}
