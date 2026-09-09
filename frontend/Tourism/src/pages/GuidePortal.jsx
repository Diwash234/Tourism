import { useCallback, useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiUser, FiFileText, FiEdit3, FiCheckCircle, FiClock, FiAlertCircle, FiXCircle } from "react-icons/fi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import workforceApi from "../api/workforceApi"

const STATUS_META = {
  applied: { label: "Applied", cls: "bg-sky-100 text-sky-700", icon: <FiClock /> },
  under_review: { label: "Under Review", cls: "bg-amber-100 text-amber-800", icon: <FiClock /> },
  document_verification: { label: "Document Verification", cls: "bg-violet-100 text-violet-700", icon: <FiFileText /> },
  needs_info: { label: "Additional Info Requested", cls: "bg-orange-100 text-orange-800", icon: <FiAlertCircle /> },
  approved: { label: "Approved — Verified Guide", cls: "bg-emerald-100 text-emerald-700", icon: <FiCheckCircle /> },
  rejected: { label: "Rejected", cls: "bg-rose-100 text-rose-700", icon: <FiXCircle /> },
}

const csv = (v) => String(v || "").split(",").map((s) => s.trim()).filter(Boolean)

/**
 * Guide Portal (workforce spec §2/§3): apply to become a verified guide,
 * track the application workflow, and manage the professional profile.
 * Verification itself is server-controlled — never self-service.
 */
export default function GuidePortal() {
  const { user, isAuthenticated } = useAuth() || {}
  const { showToast } = useToast()
  const [tab, setTab] = useState("apply")
  const [applications, setApplications] = useState([])
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({
    full_name: user?.full_name || "", phone: user?.phone_number || "", base_city: "",
    experience_summary: "", languages: "", skills: "", destinations_covered: "",
    license_info: "", document_urls: "", expected_daily_rate_npr: "",
  })

  const load = useCallback(() => {
    if (!isAuthenticated) { setLoading(false); return }
    setLoading(true)
    Promise.all([
      workforceApi.myApplications().catch(() => ({ data: { results: [] } })),
      workforceApi.myGuideProfile().catch(() => ({ data: { exists: false } })),
    ]).then(([apps, prof]) => {
      setApplications(apps.data.results || [])
      setProfile(prof.data.exists ? prof.data : null)
      if (prof.data.exists) setTab("profile")
      else if ((apps.data.results || []).length) setTab("status")
    }).finally(() => setLoading(false))
  }, [isAuthenticated])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const submitApplication = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await workforceApi.applyAsGuide({
        ...form,
        languages: csv(form.languages), skills: csv(form.skills),
        destinations_covered: csv(form.destinations_covered),
        document_urls: csv(form.document_urls),
        expected_daily_rate_npr: form.expected_daily_rate_npr ? Number(form.expected_daily_rate_npr) : null,
      })
      showToast("Application submitted — the verification team will review it", "success")
      setTab("status")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not submit application", "error")
    } finally {
      setBusy(false)
    }
  }

  const saveProfile = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const { data } = await workforceApi.saveGuideProfile({
        headline: profile.headline || "", bio: profile.bio || "", base_city: profile.base_city || "",
        license_number: profile.license_number || "",
        years_experience: Number(profile.years_experience || 0),
        daily_rate_npr: profile.daily_rate_npr ? Number(profile.daily_rate_npr) : null,
        languages: profile.languages || [], specializations: profile.specializations || [],
        regions: profile.regions || [], is_public: profile.is_public !== false,
      })
      setProfile(data)
      showToast("Profile saved", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save profile", "error")
    } finally {
      setBusy(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#F7F8F5] flex items-center justify-center p-6">
        <div className="bg-white rounded-3xl border p-10 text-center max-w-md">
          <FiUser className="mx-auto text-4xl text-[#1D5146]" />
          <h1 className="text-2xl font-black text-slate-900 mt-3">Guide Portal</h1>
          <p className="text-sm text-slate-500 mt-2">Sign in with your Nepal Yatra account to apply as a guide, track your verification and manage your professional profile.</p>
          <Link to="/login" className="inline-block mt-5 px-6 py-3 bg-[#1D5146] text-white rounded-xl font-bold text-sm">Sign In</Link>
          <p className="text-xs text-slate-400 mt-3">No account yet? <Link to="/register" className="text-[#1D5146] font-bold">Register free</Link></p>
        </div>
      </div>
    )
  }

  const latest = applications[0]
  const meta = latest ? STATUS_META[latest.status] : null
  const hasOpen = latest && ["applied", "under_review", "document_verification", "needs_info"].includes(latest.status)

  const field = "w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]"

  return (
    <div className="min-h-screen bg-[#F7F8F5]">
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <span className="text-xs uppercase tracking-widest font-black text-[#102A2E]">Tourism Workforce</span>
            <h1 className="text-3xl font-black text-slate-900">Guide Portal</h1>
            <p className="text-sm text-slate-500">Apply, verify and manage your professional guide profile.</p>
          </div>
          <Link to="/guides" className="text-sm font-bold text-[#1D5146] hover:underline">Browse verified guides →</Link>
        </div>

        <div className="flex gap-1.5">
          {[["apply", "Apply"], ["status", `My Applications${applications.length ? ` (${applications.length})` : ""}`], ["profile", profile ? "My Profile" : "Profile (after approval)"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} aria-pressed={tab === id}
              className={`px-4 py-2 rounded-full text-xs font-bold transition ${tab === id ? "bg-[#102A2E] text-white" : "bg-white border text-slate-600 hover:bg-slate-100"}`}>
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="bg-white rounded-3xl border p-12 text-center text-slate-400 text-sm animate-pulse">Loading your workspace…</div>
        ) : (
          <>
            {tab === "apply" && (
              <form onSubmit={submitApplication} className="bg-white rounded-3xl border p-6 space-y-4">
                <h2 className="font-black text-slate-900">Apply to Become a Verified Guide</h2>
                {hasOpen && (
                  <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
                    You already have an application {meta?.label?.toLowerCase()} — track it in “My Applications”.
                  </p>
                )}
                <div className="grid sm:grid-cols-2 gap-3">
                  <input required className={field} placeholder="Full name *" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
                  <input className={field} placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                  <input className={field} placeholder="Base city (e.g. Pokhara)" value={form.base_city} onChange={(e) => setForm({ ...form, base_city: e.target.value })} />
                  <input className={field} placeholder="License info (e.g. MoCTCA 1234)" value={form.license_info} onChange={(e) => setForm({ ...form, license_info: e.target.value })} />
                  <input className={field} placeholder="Languages (comma separated)" value={form.languages} onChange={(e) => setForm({ ...form, languages: e.target.value })} />
                  <input className={field} placeholder="Skills (trekking, cultural, wildlife…)" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} />
                  <input className={field} placeholder="Destinations covered (comma separated)" value={form.destinations_covered} onChange={(e) => setForm({ ...form, destinations_covered: e.target.value })} />
                  <input type="number" min="0" className={field} placeholder="Expected daily rate (NPR)" value={form.expected_daily_rate_npr} onChange={(e) => setForm({ ...form, expected_daily_rate_npr: e.target.value })} />
                </div>
                <textarea required rows={4} className={field} placeholder="Experience summary * — years, regions, notable treks/tours…" value={form.experience_summary} onChange={(e) => setForm({ ...form, experience_summary: e.target.value })} />
                <input className={field} placeholder="Document URLs (citizenship, license, certificates — comma separated)" value={form.document_urls} onChange={(e) => setForm({ ...form, document_urls: e.target.value })} />
                <button disabled={busy || hasOpen} className="px-6 py-3 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-sm font-black">
                  {busy ? "Submitting…" : "Submit Application"}
                </button>
                <p className="text-[11px] text-slate-400">Workflow: Applied → Under Review → Document Verification → Approved. The verification team may request additional information.</p>
              </form>
            )}

            {tab === "status" && (
              <div className="space-y-3">
                {applications.map((a) => {
                  const m = STATUS_META[a.status] || STATUS_META.applied
                  return (
                    <div key={a.id} className="bg-white rounded-3xl border p-5 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <b className="text-slate-900">{a.full_name}</b>
                        <span className={`text-[10px] px-2.5 py-1 rounded-full font-black uppercase flex items-center gap-1 ${m.cls}`}>{m.icon} {m.label}</span>
                      </div>
                      <p className="text-xs text-slate-500">Applied {new Date(a.created_at).toLocaleDateString()}{a.reviewed_at ? ` · last review ${new Date(a.reviewed_at).toLocaleDateString()}${a.reviewed_by ? ` by ${a.reviewed_by}` : ""}` : ""}</p>
                      {a.admin_note && (
                        <p className="text-xs bg-slate-50 border rounded-xl px-3 py-2 text-slate-600"><b>Review note:</b> {a.admin_note}</p>
                      )}
                    </div>
                  )
                })}
                {!applications.length && (
                  <div className="bg-white rounded-3xl border p-12 text-center text-sm text-slate-500">
                    No applications yet. <button onClick={() => setTab("apply")} className="text-[#1D5146] font-bold hover:underline">Apply now</button>
                  </div>
                )}
              </div>
            )}

            {tab === "profile" && (
              profile ? (
                <form onSubmit={saveProfile} className="bg-white rounded-3xl border p-6 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="font-black text-slate-900 flex items-center gap-2"><FiEdit3 /> My Guide Profile</h2>
                    <span className={`text-[10px] px-2.5 py-1 rounded-full font-black uppercase ${profile.verification_status === "verified" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                      {profile.verification_status}
                    </span>
                  </div>
                  <input className={field} placeholder="Professional headline" value={profile.headline || ""} onChange={(e) => setProfile({ ...profile, headline: e.target.value })} />
                  <textarea rows={4} className={field} placeholder="Bio" value={profile.bio || ""} onChange={(e) => setProfile({ ...profile, bio: e.target.value })} />
                  <div className="grid sm:grid-cols-3 gap-3">
                    <input className={field} placeholder="Base city" value={profile.base_city || ""} onChange={(e) => setProfile({ ...profile, base_city: e.target.value })} />
                    <input type="number" min="0" max="80" className={field} placeholder="Years of experience" value={profile.years_experience ?? ""} onChange={(e) => setProfile({ ...profile, years_experience: e.target.value })} />
                    <input type="number" min="0" className={field} placeholder="Daily rate (NPR)" value={profile.daily_rate_npr ?? ""} onChange={(e) => setProfile({ ...profile, daily_rate_npr: e.target.value })} />
                  </div>
                  <input className={field} placeholder="License number" value={profile.license_number || ""} onChange={(e) => setProfile({ ...profile, license_number: e.target.value })} />
                  <label className="text-xs font-bold text-slate-600 flex items-center gap-2">
                    <input type="checkbox" checked={profile.is_public !== false} onChange={(e) => setProfile({ ...profile, is_public: e.target.checked })} />
                    Listed in the public guide directory (when verified)
                  </label>
                  <button disabled={busy} className="px-6 py-3 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-sm font-black">{busy ? "Saving…" : "Save Profile"}</button>
                  <p className="text-[11px] text-slate-400">Verification status is managed by the platform verification team and cannot be edited here.</p>
                </form>
              ) : (
                <div className="bg-white rounded-3xl border p-12 text-center text-sm text-slate-500">
                  Your professional profile unlocks once your guide application is approved.
                </div>
              )
            )}
          </>
        )}
      </div>
    </div>
  )
}
