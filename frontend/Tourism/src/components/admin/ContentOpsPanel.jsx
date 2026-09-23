import { useCallback, useEffect, useState } from "react"
import { FiRefreshCw, FiPlus, FiSend, FiCheck, FiX, FiRotateCcw, FiChevronDown } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import useToast from "../../hooks/useToast"

const TABS = [
  { id: "", label: "In Pipeline" },
  { id: "draft", label: "Drafts" },
  { id: "submitted", label: "Submitted" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
]

const STATUS_STYLE = {
  draft: "bg-slate-100 text-slate-600",
  submitted: "bg-sky-100 text-sky-700",
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
  archived: "bg-slate-100 text-slate-400",
}

/**
 * Destination data entry pipeline (Staff Ops spec §13-14).
 * Staff author drafts and submit for review; only reviewers (admin role /
 * destinations:approve capability) can approve or reject — enforced server-side.
 */
export default function ContentOpsPanel({ canReview = false }) {
  const { showToast } = useToast()
  const [tab, setTab] = useState("")
  const [data, setData] = useState({ counts: {}, results: [] })
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: "", district: "", city: "", short_description: "", latitude: "", longitude: "" })
  const [noteFor, setNoteFor] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data: d } = await adminPanelApi.dataEntries(tab)
      setData(d)
    } catch (error) {
      showToast(error.response?.data?.detail || "Data entry queue unavailable", "error")
    } finally {
      setLoading(false)
    }
  }, [tab, showToast])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const create = async (e) => {
    e.preventDefault()
    setBusyId("create")
    try {
      await adminPanelApi.dataEntryCreate(form)
      showToast("Draft saved — review it, then submit for review", "success")
      setShowForm(false)
      setForm({ name: "", district: "", city: "", short_description: "", latitude: "", longitude: "" })
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save draft", "error")
    } finally {
      setBusyId(null)
    }
  }

  const act = async (entry, action, note = "") => {
    if (action === "reject" && noteFor !== entry.id) {
      setNoteFor(entry.id)
      return
    }
    setBusyId(entry.id)
    try {
      await adminPanelApi.dataEntryAction(entry.id, action, note)
      showToast(`Entry ${action}ed`, "success")
      setNoteFor(null)
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Action denied", "error")
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          {TABS.map((t) => (
            <button
              key={t.id || "all"}
              onClick={() => setTab(t.id)}
              aria-pressed={tab === t.id}
              className={`px-3 py-1.5 rounded-full text-xs font-bold transition ${tab === t.id ? "bg-[#102A2E] text-white" : "bg-white border text-slate-600 hover:bg-slate-100"}`}
            >
              {t.label}
              <span className={`ml-1.5 ${tab === t.id ? "text-slate-300" : "text-slate-400"}`}>{data.counts?.[t.id || "draft"] ?? ""}</span>
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="px-3 py-2 bg-white border rounded-xl text-xs font-bold flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => setShowForm((v) => !v)} className="px-3 py-2 bg-[#1D5146] text-white rounded-xl text-xs font-bold flex items-center gap-1.5">
            <FiPlus /> New Destination
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={create} className="bg-white border rounded-2xl p-4 grid sm:grid-cols-2 gap-3">
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Destination name *" className="border rounded-lg px-3 py-2 text-sm sm:col-span-2 focus:outline-none focus:border-[#1D5146]" />
          <input value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} placeholder="District" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} placeholder="City / area" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <input value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} placeholder="Latitude (optional)" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <input value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} placeholder="Longitude (optional)" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <textarea value={form.short_description} onChange={(e) => setForm({ ...form, short_description: e.target.value })} rows={2} placeholder="Short description for cards and search" className="border rounded-lg px-3 py-2 text-sm sm:col-span-2 focus:outline-none focus:border-[#1D5146]" />
          <button disabled={busyId === "create" || !form.name.trim()} className="sm:col-span-2 px-4 py-2 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-xs font-black">
            Save as Draft
          </button>
        </form>
      )}

      <section className="bg-white border rounded-2xl overflow-hidden divide-y">
        {data.results.map((d) => (
          <div key={d.id} className="p-4">
            <div className="flex flex-col lg:flex-row lg:items-center gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <b className="text-sm text-slate-900">{d.name}</b>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLE[d.status] || "bg-slate-100"}`}>{d.status}</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {d.district || d.city || "Nepal"}{d.submitted_by ? ` · by ${d.submitted_by}` : ""} · updated {new Date(d.updated_at).toLocaleDateString()}
                </p>
                {d.review_note && <p className="text-xs text-rose-700 mt-1 italic">Review note: {d.review_note}</p>}
              </div>
              <div className="flex flex-wrap gap-2">
                {["draft", "rejected"].includes(d.status) && (
                  <button onClick={() => act(d, "submit")} disabled={busyId === d.id} className="px-3 py-1.5 bg-sky-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5"><FiSend /> Submit for Review</button>
                )}
                {canReview && ["submitted", "pending"].includes(d.status) && (
                  <>
                    <button onClick={() => act(d, "approve")} disabled={busyId === d.id} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheck /> Approve</button>
                    <button onClick={() => act(d, "reject")} disabled={busyId === d.id} className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiX /> Reject</button>
                  </>
                )}
                {canReview && ["approved", "rejected"].includes(d.status) && (
                  <button onClick={() => act(d, "reopen")} disabled={busyId === d.id} className="px-3 py-1.5 bg-slate-600 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiRotateCcw /> Reopen</button>
                )}
              </div>
            </div>
            {noteFor === d.id && (
              <div className="mt-2 flex flex-col sm:flex-row gap-2">
                <input autoFocus placeholder="Rejection note — tell the author what to fix *" className="flex-1 border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-rose-500" onChange={(e) => (d._note = e.target.value)} />
                <button onClick={() => d._note?.trim() && act(d, "reject", d._note.trim())} className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiChevronDown /> Confirm rejection</button>
              </div>
            )}
          </div>
        ))}
        {!loading && !data.results.length && (
          <p className="p-10 text-center text-slate-500 text-sm">Nothing in this view — create a new destination draft to get started.</p>
        )}
      </section>
    </div>
  )
}
