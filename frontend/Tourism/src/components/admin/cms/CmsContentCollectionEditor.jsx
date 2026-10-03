import { useCallback, useEffect, useState } from "react"
import {
  FiPlus, FiTrash2, FiEdit2, FiCheck, FiSend, FiSave, FiSearch,
  FiFilter, FiRotateCcw, FiRefreshCw, FiExternalLink, FiCalendar,
  FiUser, FiTag, FiAlertTriangle
} from "react-icons/fi"
import adminApi from "../../../api/adminApi"
import { notifyCmsUpdated } from "../../../hooks/usePublicConfig"
import useToast from "../../../hooks/useToast"

const COLLECTION_KEY_MAP = {
  news: "cms_content_news",
  blogs: "cms_content_blogs",
  notices: "cms_content_notices",
  results: "cms_content_results",
  events: "cms_content_events",
  programs: "cms_content_programs",
  scholarships: "cms_content_scholarships",
  faqs: "cms_content_faqs",
  applications: "cms_content_applications",
  enquiries: "cms_content_enquiries",
  feedback: "cms_content_feedback",
  testimonials: "cms_content_testimonials",
  surveys: "cms_content_surveys",
  survey_responses: "cms_content_survey_responses",
  trash: "cms_content_trash",
}

export default function CmsContentCollectionEditor({
  contentType = "news",
  onCountChange,
}) {
  const { showToast } = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")

  // Modal / Form state for Add or Edit
  const [editItem, setEditItem] = useState(null)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [formData, setFormData] = useState({
    title: "",
    summary: "",
    category: "",
    author: "",
    date: new Date().toISOString().split("T")[0],
    level: "info",
    status: "published",
    question: "",
    answer: "",
    quote: "",
  })

  const settingKey = COLLECTION_KEY_MAP[contentType] || `cms_content_${contentType}`

  const loadItems = useCallback(async () => {
    
    try {
      const res = await adminApi.getCMS("settings")
      const rows = res.data?.results || []
      const match = rows.find(r => r.key === settingKey)
      const data = Array.isArray(match?.value) ? match.value : []
      setItems(data)
      if (onCountChange) onCountChange(contentType, data.length)
    } catch {
      setItems([])
    } finally {
      window.setTimeout(() => setLoading(false), 0)
    }
  }, [contentType, onCountChange])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  const saveCollection = async (updatedItems, successMsg = "Saved successfully") => {
    setBusy(true)
    try {
      await adminApi.updateCMS({
        resource: "settings",
        key: settingKey,
        value: updatedItems,
        description: `Content collection for ${contentType}`,
        is_public: true,
      })
      setItems(updatedItems)
      if (onCountChange) onCountChange(contentType, updatedItems.length)
      notifyCmsUpdated()
      showToast(successMsg, "success")
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
      summary: "",
      category: "Official",
      author: "Tourism Team",
      date: new Date().toISOString().split("T")[0],
      level: "info",
      status: "published",
      question: "",
      answer: "",
      quote: "",
    })
    setIsFormOpen(true)
  }

  const handleOpenEdit = (item) => {
    setEditItem(item)
    setFormData({
      title: item.title || item.question || item.author || "",
      summary: item.summary || item.answer || item.comment || item.quote || "",
      category: item.category || item.route || "",
      author: item.author || item.user_name || item.applicant_name || "",
      date: item.date || new Date().toISOString().split("T")[0],
      level: item.level || "info",
      status: item.status || "published",
      question: item.question || "",
      answer: item.answer || "",
      quote: item.quote || "",
    })
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    let nextItems
    if (editItem) {
      // Update existing item
      nextItems = items.map(item => {
        if (item.id === editItem.id) {
          return {
            ...item,
            ...formData,
            title: formData.title || item.title,
            summary: formData.summary || item.summary,
            question: formData.question || item.question,
            answer: formData.answer || item.answer,
          }
        }
        return item
      })
    } else {
      // Create new item
      const newItem = {
        id: Date.now(),
        ...formData,
      }
      nextItems = [newItem, ...items]
    }

    setIsFormOpen(false)
    await saveCollection(nextItems, editItem ? "Item updated & published live" : "New item added & published live")
  }

  const handleDelete = async (id) => {
    if (contentType === "trash") {
      // Permanent delete
      if (!window.confirm("Permanently delete this record? This cannot be undone.")) return
      const nextItems = items.filter(item => item.id !== id)
      await saveCollection(nextItems, "Permanently deleted from trash")
      return
    }

    const toDelete = items.find(item => item.id === id)
    const nextItems = items.filter(item => item.id !== id)

    // Save trash
    try {
      const res = await adminApi.getCMS("settings")
      const rows = res.data?.results || []
      const trashMatch = rows.find(r => r.key === "cms_content_trash")
      const currentTrash = Array.isArray(trashMatch?.value) ? trashMatch.value : []
      const updatedTrash = [{ ...toDelete, _originalType: contentType, _deletedAt: new Date().toISOString() }, ...currentTrash]

      await adminApi.updateCMS({
        resource: "settings",
        key: "cms_content_trash",
        value: updatedTrash,
        is_public: true,
      })
      if (onCountChange) onCountChange("trash", updatedTrash.length)
    } catch {
      // Continue
    }

    await saveCollection(nextItems, `Moved to Content Trash`)
  }

  const handleRestoreFromTrash = async (item) => {
    const origKey = COLLECTION_KEY_MAP[item._originalType || "news"] || "cms_content_news"
    try {
      const res = await adminApi.getCMS("settings")
      const rows = res.data?.results || []
      const targetMatch = rows.find(r => r.key === origKey)
      const currentTarget = Array.isArray(targetMatch?.value) ? targetMatch.value : []
      const cleanItem = { ...item }
      delete cleanItem._originalType
      delete cleanItem._deletedAt
      const updatedTarget = [cleanItem, ...currentTarget]

      await adminApi.updateCMS({
        resource: "settings",
        key: origKey,
        value: updatedTarget,
        is_public: true,
      })

      const nextTrash = items.filter(t => t.id !== item.id)
      await saveCollection(nextTrash, `Restored item back to ${item._originalType || "content"}`)
    } catch (err) {
      showToast(err.response?.data?.detail || "Restore failed", "error")
    }
  }

  const handleToggleStatus = async (item) => {
    const nextStatus = item.status === "published" ? "draft" : "published"
    const nextItems = items.map(i => i.id === item.id ? { ...i, status: nextStatus } : i)
    await saveCollection(nextItems, `Status changed to ${nextStatus}`)
  }

  const filteredItems = items.filter(item => {
    if (filterStatus !== "all" && item.status !== filterStatus) return false
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      (item.title || "").toLowerCase().includes(q) ||
      (item.summary || "").toLowerCase().includes(q) ||
      (item.category || "").toLowerCase().includes(q) ||
      (item.author || "").toLowerCase().includes(q) ||
      (item.question || "").toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-[#0E1E1B] p-5 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black capitalize text-slate-900 dark:text-white">
              {contentType.replace('_', ' ')} Management
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-200/60">
              {items.length} Records
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage, publish, and organize website {contentType.replace('_', ' ')}. Published items appear live on the public website.
          </p>
        </div>

        {contentType !== "trash" && (
          <button
            type="button"
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30 transition hover:scale-[1.02] shrink-0"
          >
            <FiPlus size={14} />
            <span>Add New {contentType.slice(0, -1)}</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-[#0E1E1B] p-4 rounded-xl border border-slate-200 dark:border-emerald-900/50">
        <div className="relative flex-1 w-full sm:max-w-md">
          <FiSearch className="absolute left-3 top-2.5 text-slate-400" size={14} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${contentType} by title, category, author...`}
            className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 pl-9 pr-3 py-1.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end text-xs">
          <FiFilter className="text-slate-400" size={13} />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-2.5 py-1.5 text-xs text-slate-700 dark:text-slate-300"
          >
            <option value="all">All Statuses</option>
            <option value="published">Published Live</option>
            <option value="draft">Drafts Only</option>
          </select>
        </div>
      </div>

      {/* Items List */}
      {loading ? (
        <div className="flex h-64 items-center justify-center text-slate-400">
          <FiRefreshCw className="animate-spin mr-2" /> Loading records…
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white dark:bg-[#0E1E1B] p-12 text-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800">
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">
            {contentType === "trash" ? "The Content Trash is empty." : `No ${contentType} records found matching your filter.`}
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {filteredItems.map(item => {
            const displayTitle = item.title || item.question || item.author || `Record #${item.id}`
            const displayBody = item.summary || item.answer || item.comment || item.quote || item.abstract || ""
            const isLive = item.status === "published"

            return (
              <div
                key={item.id}
                className="bg-white dark:bg-[#0E1E1B] p-4 rounded-xl border border-slate-200 dark:border-emerald-900/40 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-blue-400/50 transition-colors"
              >
                <div className="space-y-1 max-w-3xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-sm text-slate-900 dark:text-white">
                      {displayTitle}
                    </span>

                    {/* Status badge */}
                    <button
                      type="button"
                      onClick={() => handleToggleStatus(item)}
                      title="Click to toggle Draft / Published"
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase transition ${
                        isLive
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 hover:bg-emerald-200"
                          : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 hover:bg-amber-200"
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${isLive ? "bg-emerald-500 shadow-[0_0_4px_rgba(16,185,129,0.8)]" : "bg-amber-500"}`} />
                      <span>{isLive ? "Live" : "Draft"}</span>
                    </button>

                    {item.category && (
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-semibold text-slate-600 dark:text-slate-300">
                        {item.category}
                      </span>
                    )}

                    {item.level && (
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        item.level === "danger" ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300" :
                        item.level === "warning" ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" :
                        "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                      }`}>
                        {item.level}
                      </span>
                    )}
                  </div>

                  {displayBody && (
                    <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed">
                      {displayBody}
                    </p>
                  )}

                  <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                    {item.date && (
                      <span className="flex items-center gap-1">
                        <FiCalendar size={11} /> {item.date}
                      </span>
                    )}
                    {item.author && (
                      <span className="flex items-center gap-1">
                        <FiUser size={11} /> {item.author}
                      </span>
                    )}
                    {item._originalType && (
                      <span className="text-amber-500 font-semibold">
                        Deleted from {item._originalType}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  {contentType === "trash" ? (
                    <>
                      <button
                        type="button"
                        onClick={() => handleRestoreFromTrash(item)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition"
                      >
                        <FiRotateCcw size={12} /> Restore
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(item.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white transition"
                      >
                        <FiTrash2 size={12} /> Delete
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => handleOpenEdit(item)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition"
                      >
                        <FiEdit2 size={12} /> Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(item.id)}
                        className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition"
                        title="Move to Content Trash"
                      >
                        <FiTrash2 size={14} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Add / Edit Form Modal */}
      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-lg rounded-2xl bg-white dark:bg-[#0E1E1B] p-6 shadow-2xl border border-slate-200 dark:border-emerald-900/50 my-8">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
              {editItem ? `Edit ${contentType.slice(0, -1)}` : `New ${contentType.slice(0, -1)}`}
            </h3>

            <form onSubmit={handleFormSubmit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Title / Headline *
                </label>
                <input
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Enter clear title..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Category / Tag
                  </label>
                  <input
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g. Safety, Culture, Trek"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Author / Department
                  </label>
                  <input
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    placeholder="e.g. Nepal Yatra Team"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Summary / Body Text *
                </label>
                <textarea
                  required
                  rows={4}
                  value={formData.summary}
                  onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                  placeholder="Detailed content, advisories or announcements..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Publication Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  >
                    <option value="published">Published Live</option>
                    <option value="draft">Draft (Private)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Date
                  </label>
                  <input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>
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
