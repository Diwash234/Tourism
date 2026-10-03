import { useCallback, useEffect, useState } from "react"
import { FiPlus, FiTrash2, FiEdit2, FiFileText, FiBookOpen, FiCalendar, FiUser, FiExternalLink, FiRefreshCw } from "react-icons/fi"
import adminApi from "../../../api/adminApi"
import { notifyCmsUpdated } from "../../../hooks/usePublicConfig"
import useToast from "../../../hooks/useToast"

export default function CmsJournalsEditor({ journalType = "abstracts", onCountChange }) {
  const { showToast } = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [formData, setFormData] = useState({
    title: "",
    author: "",
    institution: "",
    date: "2026-09",
    status: "published",
    abstract: "",
    doi: "",
  })

  const settingKey = journalType === "abstracts" ? "cms_content_abstracts" : "cms_content_journals"

  const loadItems = useCallback(async () => {
    
    try {
      const res = await adminApi.getCMS("settings")
      const rows = res.data?.results || []
      const match = rows.find(r => r.key === settingKey)
      const data = Array.isArray(match?.value) ? match.value : []
      setItems(data)
      if (onCountChange) onCountChange(journalType, data.length)
    } catch {
      setItems([])
    } finally {
      Promise.resolve().then(() => setLoading(false))
    }
  }, [journalType, onCountChange])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  const saveCollection = async (updatedItems, msg = "Saved") => {
    setBusy(true)
    try {
      await adminApi.updateCMS({
        resource: "settings",
        key: settingKey,
        value: updatedItems,
        is_public: true,
      })
      setItems(updatedItems)
      if (onCountChange) onCountChange(journalType, updatedItems.length)
      notifyCmsUpdated()
      showToast(msg, "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Action failed", "error")
    } finally {
      setBusy(false)
    }
  }

  const handleOpenAdd = () => {
    setEditItem(null)
    setFormData({
      title: "",
      author: "",
      institution: "Nepal Research Council",
      date: "2026-09",
      status: "published",
      abstract: "",
      doi: "",
    })
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    let nextItems
    if (editItem) {
      nextItems = items.map(i => i.id === editItem.id ? { ...i, ...formData } : i)
    } else {
      nextItems = [{ id: Date.now(), ...formData }, ...items]
    }
    setIsFormOpen(false)
    await saveCollection(nextItems, editItem ? "Updated journal entry" : "Added new research entry")
  }

  const handleDelete = async (id) => {
    if (!window.confirm("Remove this research journal entry?")) return
    const nextItems = items.filter(i => i.id !== id)
    await saveCollection(nextItems, "Removed journal entry")
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-[#0E1E1B] p-5 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black capitalize text-slate-900 dark:text-white">
              {journalType === "abstracts" ? "Research Abstracts" : "Journal Section"}
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
              {items.length} Publications
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Academic research papers, high-altitude biodiversity abstracts, and Himalayan conservation studies.
          </p>
        </div>

        <button
          type="button"
          onClick={handleOpenAdd}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30 transition hover:scale-[1.02] shrink-0"
        >
          <FiPlus size={14} />
          <span>Add New {journalType === "abstracts" ? "Abstract" : "Publication"}</span>
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center text-slate-400">
          <FiRefreshCw className="animate-spin mr-2" /> Loading research data…
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            <div
              key={item.id}
              className="bg-white dark:bg-[#0E1E1B] p-5 rounded-xl border border-slate-200 dark:border-emerald-900/40 shadow-sm space-y-2 hover:border-blue-400/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white leading-snug">
                    {item.title}
                  </h3>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {item.author && <span className="flex items-center gap-1"><FiUser size={11} /> {item.author}</span>}
                    {item.institution && <span>· {item.institution}</span>}
                    {item.editor && <span>Editor: {item.editor}</span>}
                    {item.issn && <span>· ISSN: {item.issn}</span>}
                    {item.date && <span>· {item.date}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                    Live
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDelete(item.id)}
                    className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                    title="Delete"
                  >
                    <FiTrash2 size={13} />
                  </button>
                </div>
              </div>

              {item.abstract && (
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed pt-1">
                  {item.abstract}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-lg rounded-2xl bg-white dark:bg-[#0E1E1B] p-6 shadow-2xl border border-slate-200 dark:border-emerald-900/50 my-8">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              Add New Research {journalType === "abstracts" ? "Abstract" : "Publication"}
            </h3>

            <form onSubmit={handleFormSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Paper Title *</label>
                <input
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Glacial Lake Outburst Vulnerability in Sagarmatha..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Author / Researcher</label>
                  <input
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    placeholder="e.g. Dr. K. P. Sharma"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Institution</label>
                  <input
                    value={formData.institution}
                    onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
                    placeholder="e.g. Tribhuvan University"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Abstract Summary</label>
                <textarea
                  rows={4}
                  value={formData.abstract}
                  onChange={(e) => setFormData({ ...formData, abstract: e.target.value })}
                  placeholder="Key research findings, methodology, and recommendations..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsFormOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30"
                >
                  Save & Publish
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
