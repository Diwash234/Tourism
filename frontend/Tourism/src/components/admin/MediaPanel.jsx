import { useCallback, useEffect, useState } from "react"
import { FiRefreshCw, FiPlus, FiCheck, FiX, FiImage } from "react-icons/fi"
import adminPanelApi from "../../api/adminPanelApi"
import useToast from "../../hooks/useToast"

const TABS = [
  { id: "pending", label: "Needs Review" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "", label: "All" },
]

const STATUS_STYLE = {
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
}

/**
 * Destination image review queue (Staff Ops spec §15).
 * Staff add images by URL (they land as pending); reviewers approve/reject.
 */
export default function MediaPanel({ canReview = false }) {
  const { showToast } = useToast()
  const [tab, setTab] = useState("pending")
  const [data, setData] = useState({ counts: {}, results: [] })
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ destination: "", external_url: "", caption: "", alt_text: "" })

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data: d } = await adminPanelApi.mediaQueue(tab)
      setData(d)
    } catch (error) {
      showToast(error.response?.data?.detail || "Media queue unavailable", "error")
    } finally {
      setLoading(false)
    }
  }, [tab, showToast])

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [load])

  const add = async (e) => {
    e.preventDefault()
    setBusyId("add")
    try {
      await adminPanelApi.mediaAdd(form)
      showToast("Image submitted to the review queue", "success")
      setShowForm(false)
      setForm({ destination: "", external_url: "", caption: "", alt_text: "" })
      setTab("pending")
      load()
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not add image", "error")
    } finally {
      setBusyId(null)
    }
  }

  const act = async (img, action) => {
    setBusyId(img.id)
    try {
      await adminPanelApi.mediaAction(img.id, action)
      showToast(`Image ${action}d`, "success")
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
              <span className={`ml-1.5 ${tab === t.id ? "text-slate-300" : "text-slate-400"}`}>{data.counts?.[t.id || "all"] ?? 0}</span>
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="px-3 py-2 bg-white border rounded-xl text-xs font-bold flex items-center gap-2">
            <FiRefreshCw className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => setShowForm((v) => !v)} className="px-3 py-2 bg-[#1D5146] text-white rounded-xl text-xs font-bold flex items-center gap-1.5">
            <FiPlus /> Add Image
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={add} className="bg-white border rounded-2xl p-4 grid sm:grid-cols-2 gap-3">
          <input required type="number" value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} placeholder="Destination ID *" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <input required type="url" value={form.external_url} onChange={(e) => setForm({ ...form, external_url: e.target.value })} placeholder="Image URL *" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <input value={form.caption} onChange={(e) => setForm({ ...form, caption: e.target.value })} placeholder="Caption" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <input value={form.alt_text} onChange={(e) => setForm({ ...form, alt_text: e.target.value })} placeholder="Alt text (accessibility)" className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#1D5146]" />
          <button disabled={busyId === "add"} className="sm:col-span-2 px-4 py-2 bg-[#1D5146] disabled:opacity-40 text-white rounded-xl text-xs font-black">Submit to Review Queue</button>
        </form>
      )}

      <section className="bg-white border rounded-2xl overflow-hidden divide-y">
        {data.results.map((img) => (
          <div key={img.id} className="p-4 flex flex-col sm:flex-row gap-3">
            {img.image_url ? (
              <img src={img.image_url} alt={img.alt_text || img.caption || ""} className="w-full sm:w-28 h-20 object-cover rounded-lg border" loading="lazy" />
            ) : (
              <div className="w-full sm:w-28 h-20 rounded-lg border bg-slate-50 flex items-center justify-center text-slate-300"><FiImage size={24} /></div>
            )}
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <b className="text-sm text-slate-900">{img.destination_name}</b>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${STATUS_STYLE[img.status] || "bg-slate-100"}`}>{img.status}</span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{img.caption || img.alt_text || "no caption"} · added {new Date(img.created_at).toLocaleDateString()}</p>
            </div>
            {canReview && img.status === "pending" && (
              <div className="flex gap-2">
                <button onClick={() => act(img, "approve")} disabled={busyId === img.id} className="px-3 py-1.5 bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiCheck /> Approve</button>
                <button onClick={() => act(img, "reject")} disabled={busyId === img.id} className="px-3 py-1.5 bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1"><FiX /> Reject</button>
              </div>
            )}
          </div>
        ))}
        {!loading && !data.results.length && (
          <p className="p-10 text-center text-slate-500 text-sm">No images in this view.</p>
        )}
      </section>
    </div>
  )
}
