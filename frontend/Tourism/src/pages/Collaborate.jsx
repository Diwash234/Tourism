import { useState } from "react"
import { Link } from "react-router-dom"
import { FiBriefcase } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import userApi from "../api/userApi"
import useToast from "../hooks/useToast"

const KINDS = [
  ["hotel", "Hotel"],
  ["operator", "Tour Operator"],
  ["homestay", "Homestay"],
  ["other", "Other"],
  ["guide", "Local guide"],
  ["restaurant", "Restaurant"],
  ["transport", "Transport"],
  ["activity", "Activity provider"],
  ["agency", "Travel agency"],
]

const empty = {
  name: "", kind: "hotel", contact_name: "", email: "", phone: "",
  city: "", district: "", website: "", description: "", services: "",
  license_info: "", logo_url: "",
}

export default function Collaborate() {
  const { showToast } = useToast()
  const [form, setForm] = useState(empty)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.value })

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    try {
      const { data } = await userApi.applyMarketplacePartner(form)
      setDone(true)
      setForm(empty)
      showToast(data.message || "Application submitted successfully. Our team will review your application and contact you.", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not send application", "error")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container-app py-10" data-testid="collaborate-page">
      <PageHeader
        title="Partner with Nepal Tourism"
        subtitle="Submit your hotel or tour business for review. After approval you can add packages from the partner desk — an administrator still publishes each offer."
        icon={FiBriefcase}
        theme="forest"
      />
      {done ? (
        <div className="card-base p-8 max-w-xl space-y-3" data-testid="collaborate-success">
          <h2 className="text-xl font-black">Application submitted successfully</h2>
          <p className="text-slate-600">Our team will review your application and contact you.</p>
          <div className="flex flex-wrap gap-2">
            <Link to="/partner" className="btn-primary inline-flex">Open partner desk</Link>
            <Link to="/packages" className="btn-outline inline-flex">Browse current packages</Link>
          </div>
        </div>
      ) : (
        <form onSubmit={submit} className="card-base p-6 max-w-xl space-y-3" data-testid="collaborate-form">
          <input className="input-field" required name="name" data-testid="partner-name" placeholder="Business / hotel name" value={form.name} onChange={set("name")} />
          <select className="input-field" value={form.kind} onChange={set("kind")}>
            {KINDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
          <input className="input-field" placeholder="Contact person" value={form.contact_name} onChange={set("contact_name")} />
          <input className="input-field" required type="email" name="email" data-testid="partner-email" placeholder="Email" value={form.email} onChange={set("email")} />
          <input className="input-field" placeholder="Phone" value={form.phone} onChange={set("phone")} />
          <div className="grid grid-cols-2 gap-2">
            <input className="input-field" placeholder="Location / city" value={form.city} onChange={set("city")} />
            <input className="input-field" placeholder="District" value={form.district} onChange={set("district")} />
          </div>
          <input className="input-field" placeholder="Website (https://…)" value={form.website} onChange={set("website")} />
          <input className="input-field" placeholder="Logo / photo HTTPS URL (optional)" value={form.logo_url} onChange={set("logo_url")} />
          <textarea className="input-field min-h-[90px]" placeholder="About the business" value={form.description} onChange={set("description")} />
          <textarea className="input-field min-h-[90px]" placeholder="Services / packages you want to list" value={form.services} onChange={set("services")} />
          <input className="input-field" placeholder="Registration / license number" value={form.license_info} onChange={set("license_info")} />
          <p className="text-xs text-slate-500">Website and photos must start with https://. Do not send card or payment credentials.</p>
          <button type="submit" disabled={busy} className="btn-primary w-full">{busy ? "Sending…" : "Submit application"}</button>
        </form>
      )}
    </div>
  )
}
