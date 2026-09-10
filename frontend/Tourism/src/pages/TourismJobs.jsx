import { useCallback, useEffect, useState } from "react"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { Link } from "react-router-dom"
import { FiBriefcase, FiMapPin, FiClock, FiDollarSign, FiSearch, FiCheckCircle } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import workforceApi from "../api/workforceApi"

const ROLE_LABEL = {
  guide: "Tour Guide", trek_assistant: "Trek Assistant", photographer: "Photographer",
  content_creator: "Content Creator", translator: "Translator", customer_support: "Customer Support",
  hotel_staff: "Hotel Staff", travel_coordinator: "Travel Coordinator", experience_host: "Experience Host",
  event_staff: "Event Staff", data_contributor: "Data Contributor", other: "Other",
}

/**
 * Tourism work & gig marketplace (workforce spec §9).
 * Public open-job board with inline apply; applications tracked per account.
 */
export default function TourismJobs() {
  const { isAuthenticated } = useAuth() || {}
  const { showToast } = useToast()
  const [data, setData] = useState({ count: 0, results: [] })
  const [myApps, setMyApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState("")
  const [role, setRole] = useState("")
  const [applyingTo, setApplyingTo] = useState(null)
  const [form, setForm] = useState({ cover_letter: "", experience_summary: "", skills: "", availability: "", cv_url: "", portfolio_url: "" })
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    const jobsReq = workforceApi.jobs({ q: q || undefined, role_type: role || undefined })
      .then(({ data: d }) => setData(d)).catch(() => setData({ count: 0, results: [] }))
    const appsReq = isAuthenticated
      ? workforceApi.myJobApplications().then(({ data: d }) => setMyApps(d.results || [])).catch(() => {})
      : Promise.resolve()
    Promise.all([jobsReq, appsReq]).finally(() => setLoading(false))
  }, [q, role, isAuthenticated])

  useEffect(() => {
    const t = setTimeout(() => load(), 250)
    return () => clearTimeout(t)
  }, [load])

  const appliedJobIds = new Set(myApps.map((a) => a.job_id))
  const statusOf = (jobId) => myApps.find((a) => a.job_id === jobId)?.status

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await workforceApi.applyToJob({
        job: applyingTo.id,
        ...form,
        skills: String(form.skills || "").split(",").map((s) => s.trim()).filter(Boolean),
      })
      showToast("Application submitted — track it below", "success")
      setApplyingTo(null)
      setForm({ cover_letter: "", experience_summary: "", skills: "", availability: "", cv_url: "", portfolio_url: "" })
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not apply", "error")
    } finally {
      setBusy(false)
    }
  }

  const field = "w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]"
  const badge = {
    applied: "bg-sky-100 text-sky-700", shortlisted: "bg-amber-100 text-amber-800",
    hired: "bg-emerald-100 text-emerald-700", rejected: "bg-rose-100 text-rose-700",
  }

  return (
    <div className="min-h-screen bg-[#F7F8F5]">
      <CMSPageIntro pageKey="tourism-jobs" />
      <PageHeader
        title="Tourism Work & Gigs"
        subtitle="Seasonal and contract work across Nepal's tourism industry — guiding, hosting, content, support and more."
      />
      <div className="max-w-5xl mx-auto px-4 pb-16 -mt-6">
        <div className="bg-white rounded-3xl border shadow-sm p-4 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search jobs by title, description or city…" aria-label="Search jobs"
              className="w-full pl-10 pr-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]" />
          </div>
          <select value={role} onChange={(e) => setRole(e.target.value)} aria-label="Filter by role"
            className="px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:border-[#1D5146]">
            <option value="">All roles</option>
            {Object.entries(ROLE_LABEL).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
        </div>

        <div className="flex items-center justify-between mt-6 mb-3">
          <p className="text-sm text-slate-600"><b>{data.count}</b> open position{data.count === 1 ? "" : "s"}</p>
          <Link to="/guide-portal" className="text-sm font-bold text-[#1D5146] hover:underline">Become a verified guide →</Link>
        </div>

        <div className="space-y-3">
          {data.results.map((job) => (
            <div key={job.id} className="bg-white rounded-3xl border shadow-sm p-5">
              <div className="flex flex-col lg:flex-row lg:items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-black text-slate-900">{job.title}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#1D5146] text-white font-bold uppercase">{job.role_type_label}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-bold uppercase">{job.employment_type_label}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1.5 line-clamp-2">{job.description}</p>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500 mt-2">
                    {job.city && <span className="flex items-center gap-1"><FiMapPin /> {job.city}</span>}
                    {job.compensation && <span className="flex items-center gap-1"><FiDollarSign /> {job.compensation}</span>}
                    {job.application_deadline && <span className="flex items-center gap-1"><FiClock /> Apply by {job.application_deadline}</span>}
                    <span className="flex items-center gap-1"><FiBriefcase /> {job.application_count} applicant{job.application_count === 1 ? "" : "s"}</span>
                  </div>
                  {job.skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.skills.slice(0, 6).map((s) => (
                        <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-50 border text-slate-500 font-bold">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="shrink-0">
                  {appliedJobIds.has(job.id) ? (
                    <span className={`inline-flex items-center gap-1 text-[10px] px-3 py-2 rounded-full font-black uppercase ${badge[statusOf(job.id)] || "bg-slate-100"}`}>
                      <FiCheckCircle /> {statusOf(job.id)}
                    </span>
                  ) : isAuthenticated ? (
                    <button onClick={() => setApplyingTo(job)} className="px-4 py-2 bg-[#1D5146] hover:bg-[#102A2E] text-white rounded-xl text-xs font-black">
                      Apply Now
                    </button>
                  ) : (
                    <Link to="/login" className="inline-block px-4 py-2 bg-[#1D5146] text-white rounded-xl text-xs font-black">Sign in to Apply</Link>
                  )}
                </div>
              </div>
            </div>
          ))}
          {!loading && !data.results.length && (
            <div className="bg-white rounded-3xl border p-12 text-center">
              <FiBriefcase className="mx-auto text-3xl text-slate-300" />
              <p className="text-slate-600 font-bold mt-2">No open positions match this search right now.</p>
              <p className="text-xs text-slate-400 mt-1">Try a different role or check back soon — seasonal hiring peaks before spring and autumn trekking seasons.</p>
            </div>
          )}
        </div>

        {isAuthenticated && myApps.length > 0 && (
          <section className="mt-8">
            <h2 className="font-black text-slate-900 mb-3">My Applications</h2>
            <div className="bg-white rounded-3xl border divide-y">
              {myApps.map((a) => (
                <div key={a.id} className="p-4 flex flex-col sm:flex-row sm:items-center gap-2">
                  <div className="min-w-0 flex-1">
                    <b className="text-sm text-slate-900">{a.job_title}</b>
                    <p className="text-xs text-slate-500">Applied {new Date(a.created_at).toLocaleDateString()}{a.reviewed_at ? ` · reviewed ${new Date(a.reviewed_at).toLocaleDateString()}` : ""}</p>
                    {a.admin_note && <p className="text-xs text-slate-600 mt-1 italic">“{a.admin_note}”</p>}
                  </div>
                  <span className={`text-[10px] px-3 py-1.5 rounded-full font-black uppercase w-fit ${badge[a.status] || "bg-slate-100"}`}>{a.status}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {applyingTo && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <form onSubmit={submit} className="bg-white rounded-3xl p-6 w-full max-w-lg space-y-3 max-h-[90vh] overflow-y-auto">
            <h3 className="font-black text-slate-900">Apply: {applyingTo.title}</h3>
            <textarea required rows={4} className={field} placeholder="Cover letter * — why you fit this role…" value={form.cover_letter} onChange={(e) => setForm({ ...form, cover_letter: e.target.value })} />
            <textarea rows={3} className={field} placeholder="Relevant experience" value={form.experience_summary} onChange={(e) => setForm({ ...form, experience_summary: e.target.value })} />
            <input className={field} placeholder="Skills (comma separated)" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} />
            <input className={field} placeholder="Availability (e.g. Oct–Nov 2026)" value={form.availability} onChange={(e) => setForm({ ...form, availability: e.target.value })} />
            <input type="url" className={field} placeholder="CV URL (optional)" value={form.cv_url} onChange={(e) => setForm({ ...form, cv_url: e.target.value })} />
            <input type="url" className={field} placeholder="Portfolio URL (optional)" value={form.portfolio_url} onChange={(e) => setForm({ ...form, portfolio_url: e.target.value })} />
            <div className="flex gap-2 pt-1">
              <button type="button" onClick={() => setApplyingTo(null)} className="flex-1 px-4 py-2.5 border rounded-xl text-sm font-bold text-slate-600">Cancel</button>
              <button disabled={busy} className="flex-1 px-4 py-2.5 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-sm font-black">{busy ? "Submitting…" : "Submit Application"}</button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}
