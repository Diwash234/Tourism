import { useCallback, useEffect, useState } from "react"
import { FiRefreshCw, FiCheck, FiX, FiSearch, FiFileText, FiEye, FiEyeOff } from "react-icons/fi"
import workforceApi from "../../api/workforceApi"
import useToast from "../../hooks/useToast"

const TABS = [
  { id: "", label: "All", key: "all" },
  { id: "applied", label: "Applied" },
  { id: "under_review", label: "Under Review" },
  { id: "document_verification", label: "Documents" },
  { id: "needs_info", label: "Needs Info" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
]

const STATUS_STYLE = {
  applied: "bg-sky-100 text-sky-700",
  under_review: "bg-amber-100 text-amber-800",
  document_verification: "bg-violet-100 text-violet-700",
  needs_info: "bg-orange-100 text-orange-800",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
}

/**
 * Verification Center (workforce spec §11) — admin/staff with the marketplace
 * capability review guide applications and manage verified guide profiles.
 * Every transition is enforced, notified and audited server-side.
 */
export default function GuideVerificationPanel() {
  const { showToast } = useToast()
  const [tab, setTab] = useState("")
  const [data, setData] = useState({ counts: {}, results: [] })
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [noteFor, setNoteFor] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [overview, setOverview] = useState(null)

  const load = useCallback(async () => {
    workforceApi.adminOverview().then(({ data: d }) => setOverview(d)).catch(() => setOverview(null))
    setLoading(true)
    try {
      const { data: d } = await workforceApi.applications(tab)
      setData(d)
    } catch (error) {
      showToast(error.response?.data?.detail || "Verification queue unavailable", "error")
    } finally {
      setLoading(false)
    }
  }, [tab, showToast])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const act = async (app, action, note = "") => {
    if ((action === "needs_info" || action === "reject") && noteFor !== `${app.id}-${action}`) {
      setNoteFor(`${app.id}-${action}`)
      return
    }
    if ((action === "needs_info" || action === "reject") && !note) {
      showToast("A note is required", "error")
      return
    }
    setBusyId(app.id)
    try {
      await workforceApi.applicationAction(app.id, action, note)
      showToast(`Application ${action.replaceAll("_", " ")}`, "success")
      setNoteFor(null)
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Action denied", "error")
    } finally {
      setBusyId(null)
    }
  }

  const ovCards = overview ? [
    ["Guide applications", overview.guide_applications, ["applied", "under_review", "document_verification", "needs_info", "approved", "rejected"]],
    ["Jobs", overview.jobs, ["open", "paused", "filled", "closed"]],
    ["Job applications", overview.job_applications, ["applied", "shortlisted", "hired", "rejected"]],
    ["Guide bookings", overview.bookings, ["requested", "accepted", "completed", "declined", "cancelled"]],
  ] : []

  return (
    <div className="space-y-4">
      {overview && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
          {ovCards.map(([label, counts]) => (
            <div key={label} className="bg-white rounded-2xl border p-4">
              <p className="text-[10px] uppercase tracking-wider font-black text-slate-400">{label}</p>
              {Object.entries(counts).filter(([k]) => label !== "Guide applications" || k !== "needs_info" || counts[k] > 0).slice(0, 6).map(([k, v]) => (
                <p key={k} className="text-xs text-slate-600 flex justify-between mt-1">
                  <span className="capitalize">{k.replaceAll("_", " ")}</span><b>{v}</b>
                </p>
              ))}
            </div>
          ))}
          <div className="bg-violet-50 border border-violet-200 rounded-2xl p-4">
            <p className="text-[10px] uppercase tracking-wider font-black text-violet-400">Pending work</p>
            <p className="text-3xl font-black text-violet-700 mt-1">{overview.pending_work}</p>
            <p className="text-[10px] text-violet-500 mt-1">applications + job applications + booking requests awaiting action</p>
          </div>
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {TABS.map((t) => (
            <button key={t.id || "all"} onClick={() => setTab(t.id)} aria-pressed={tab === t.id}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition ${tab === t.id ? "bg-[#102A2E] text-white" : "bg-white border text-slate-600 hover:bg-slate-100"}`}>
              {t.label}
              <span className={`ml-1.5 ${tab === t.id ? "text-slate-300" : "text-slate-400"}`}>{data.counts?.[t.key ?? t.id] ?? 0}</span>
            </button>
          ))}
        </div>
        <button onClick={load} className="px-3 py-2 bg-white border rounded-xl text-xs font-bold flex items-center gap-2">
          <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      <section className="bg-white border rounded-2xl overflow-hidden divide-y">
        {data.results.map((a) => (
          <div key={a.id} className="p-4 space-y-2">
            <div className="flex flex-col lg:flex-row lg:items-center gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <b className="text-sm text-slate-900">#{a.id} {a.full_name}</b>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLE[a.status] || "bg-slate-100"}`}>{a.status.replaceAll("_", " ")}</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {a.user_email}{a.phone ? ` · ${a.phone}` : ""}{a.base_city ? ` · ${a.base_city}` : ""} · applied {new Date(a.created_at).toLocaleDateString()}
                  {a.expected_daily_rate_npr ? ` · NPR ${Number(a.expected_daily_rate_npr).toLocaleString()}/day` : ""}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button onClick={() => setExpanded(expanded === a.id ? null : a.id)} className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-xs font-bold flex items-center gap-1">
                  {expanded === a.id ? <FiEyeOff /> : <FiEye />} Details
                </button>
                {a.status === "applied" && (
                  <button onClick={() => act(a, "review")} disabled={busyId === a.id} className="px-3 py-1.5 bg-sky-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiSearch /> Start Review</button>
                )}
                {["applied", "under_review"].includes(a.status) && (
                  <button onClick={() => act(a, "verify_documents")} disabled={busyId === a.id} className="px-3 py-1.5 bg-violet-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiFileText /> Check Documents</button>
                )}
                {!["approved", "rejected"].includes(a.status) && (
                  <>
                    <button onClick={() => act(a, "approve")} disabled={busyId === a.id} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheck /> Approve & Verify</button>
                    <button onClick={() => act(a, "needs_info")} disabled={busyId === a.id} className="px-3 py-1.5 bg-orange-600 text-white rounded-lg text-xs font-bold">Request Info</button>
                    <button onClick={() => act(a, "reject")} disabled={busyId === a.id} className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiX /> Reject</button>
                  </>
                )}
              </div>
            </div>

            {expanded === a.id && (
              <div className="grid sm:grid-cols-2 gap-3 text-xs bg-slate-50 border rounded-xl p-3">
                <div><b className="text-slate-700 block mb-0.5">Experience</b><p className="text-slate-600">{a.experience_summary}</p></div>
                <div>
                  <p><b>Languages:</b> {(a.languages || []).join(", ") || "—"}</p>
                  <p><b>Skills:</b> {(a.skills || []).join(", ") || "—"}</p>
                  <p><b>Destinations:</b> {(a.destinations_covered || []).join(", ") || "—"}</p>
                  <p><b>License:</b> {a.license_info || "—"}</p>
                </div>
                {(a.document_urls || []).length > 0 && (
                  <div className="sm:col-span-2">
                    <b className="text-slate-700 block mb-0.5">Documents</b>
                    <ul className="space-y-0.5">{a.document_urls.map((u, i) => (
                      <li key={i}><a href={u} target="_blank" rel="noreferrer" className="text-[#1D5146] font-bold hover:underline break-all">{u}</a></li>
                    ))}</ul>
                  </div>
                )}
                {a.admin_note && <p className="sm:col-span-2 text-slate-600"><b>Last review note:</b> {a.admin_note}</p>}
              </div>
            )}

            {(noteFor === `${a.id}-needs_info` || noteFor === `${a.id}-reject`) && (
              <div className="flex flex-col sm:flex-row gap-2">
                <input autoFocus placeholder={noteFor.endsWith("reject") ? "Rejection reason (required) *" : "What information is needed? (required) *"}
                  className="flex-1 border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-[#1D5146]"
                  onChange={(e) => (a._note = e.target.value)} />
                <button onClick={() => act(a, noteFor.endsWith("reject") ? "reject" : "needs_info", (a._note || "").trim())}
                  className="px-3 py-1.5 bg-[#102A2E] text-white rounded-lg text-xs font-bold">Send</button>
              </div>
            )}
          </div>
        ))}
        {!loading && !data.results.length && (
          <p className="p-10 text-center text-slate-500 text-sm">No guide applications in this view.</p>
        )}
      </section>
    </div>
  )
}
