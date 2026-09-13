import { useEffect, useState } from "react"
import { FiCheck, FiEdit3, FiPlus, FiTrash2, FiX } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

/**
 * Redirects & URLs (CMS brief §14) — admin-managed URL redirects.
 *
 * Every rule is stored in the backend (RedirectRule) and exposed through the
 * public config, so the visitor site applies it immediately without any
 * rebuild or redeploy. All mutations await the API and only toast from the
 * backend's own response message (brief §16: no fake success).
 */
export default function RedirectsPanel() {
  const { showToast } = useToast()
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [draft, setDraft] = useState({ old_path: "", new_path: "", is_permanent: true, note: "" })
  const [confirmDelete, setConfirmDelete] = useState(null)

  const load = async () => {
    try {
      const res = await adminApi.getRedirects()
      setRules(res.data?.results || [])
    } catch (err) {
      showToast(err.response?.data?.error || "Could not load redirects.", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect flush.
    const t = setTimeout(() => { load() }, 0)
    return () => clearTimeout(t)
  }, [])

  const resetForm = () => {
    setDraft({ old_path: "", new_path: "", is_permanent: true, note: "" })
    setEditingId(null)
    setShowForm(false)
  }

  const submit = async (event) => {
    event.preventDefault()
    if (saving) return
    setSaving(true)
    try {
      const payload = {
        old_path: draft.old_path.trim(),
        new_path: draft.new_path.trim(),
        is_permanent: draft.is_permanent,
        note: draft.note.trim(),
      }
      const res = editingId
        ? await adminApi.updateRedirect(editingId, payload)
        : await adminApi.createRedirect(payload)
      await load()
      showToast(res.data?.message || "Redirect saved.", "success")
      resetForm()
    } catch (err) {
      const data = err.response?.data
      const message = Array.isArray(data) ? data[0]
        : (data?.error || data?.detail || (typeof data === "string" ? data : null))
        || "Save failed — check both paths and try again."
      showToast(message, "error")
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (rule) => {
    try {
      const res = await adminApi.updateRedirect(rule.id, { is_active: !rule.is_active })
      await load()
      showToast(res.data?.message || "Redirect updated.", "success")
    } catch (err) {
      showToast(err.response?.data?.error || "Update failed.", "error")
    }
  }

  const remove = async (rule) => {
    try {
      const res = await adminApi.deleteRedirect(rule.id)
      await load()
      showToast(res.data?.message || "Redirect deleted.", "success")
      setConfirmDelete(null)
    } catch (err) {
      showToast(err.response?.data?.error || "Delete failed.", "error")
    }
  }

  const startEdit = (rule) => {
    setDraft({ old_path: rule.old_path, new_path: rule.new_path, is_permanent: rule.is_permanent, note: rule.note || "" })
    setEditingId(rule.id)
    setShowForm(true)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mr-auto">
          <h2 className="text-lg font-bold text-slate-900">Redirects &amp; URLs</h2>
          <p className="text-xs text-slate-500">
            Send visitors from an old web address to a new one. Changes apply to the live site immediately — no rebuild needed.
          </p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true) }}
          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-800"
        >
          <FiPlus /> New redirect
        </button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-slate-600">From (old address)</span>
              <input
                value={draft.old_path}
                onChange={(e) => setDraft({ ...draft, old_path: e.target.value })}
                placeholder="/destinations/old-name"
                required
                className="mt-1 w-full rounded-lg border border-emerald-200 bg-white px-2.5 py-1.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </label>
            <label className="block">
              <span className="text-[11px] font-bold uppercase tracking-wide text-slate-600">To (new address)</span>
              <input
                value={draft.new_path}
                onChange={(e) => setDraft({ ...draft, new_path: e.target.value })}
                placeholder="/destinations/new-name"
                required
                className="mt-1 w-full rounded-lg border border-emerald-200 bg-white px-2.5 py-1.5 text-sm focus:border-emerald-600 focus:outline-none"
              />
            </label>
          </div>
          <label className="block">
            <span className="text-[11px] font-bold uppercase tracking-wide text-slate-600">Note (optional, admin only)</span>
            <input
              value={draft.note}
              onChange={(e) => setDraft({ ...draft, note: e.target.value })}
              placeholder="Why this redirect exists"
              className="mt-1 w-full rounded-lg border border-emerald-200 bg-white px-2.5 py-1.5 text-sm focus:border-emerald-600 focus:outline-none"
            />
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <label className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700">
              <input
                type="checkbox"
                checked={draft.is_permanent}
                onChange={(e) => setDraft({ ...draft, is_permanent: e.target.checked })}
                className="h-3.5 w-3.5 accent-emerald-700"
              />
              Permanent redirect
            </label>
            <div className="ml-auto flex gap-2">
              <button type="button" onClick={resetForm} className="inline-flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50">
                <FiX /> Cancel
              </button>
              <button type="submit" disabled={saving} className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-800 disabled:opacity-50">
                <FiCheck /> {saving ? "Saving…" : editingId ? "Save changes" : "Add redirect"}
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="rounded-xl border border-emerald-200 bg-white">
        {loading ? (
          <p className="p-6 text-center text-sm text-slate-500">Loading redirects…</p>
        ) : rules.length === 0 ? (
          <p className="p-6 text-center text-sm text-slate-500">
            No redirects yet. Add one when a page address changes so old links keep working.
          </p>
        ) : (
          <ul className="divide-y divide-emerald-100">
            {rules.map((rule) => (
              <li key={rule.id} className="flex flex-wrap items-center gap-2 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold text-slate-800">
                    <span className="font-mono text-xs">{rule.old_path}</span>
                    <span className="mx-1.5 text-slate-400">→</span>
                    <span className="font-mono text-xs text-emerald-800">{rule.new_path}</span>
                  </p>
                  {rule.note && <p className="truncate text-[11px] text-slate-500">{rule.note}</p>}
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${rule.is_permanent ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                  {rule.is_permanent ? "Permanent" : "Temporary"}
                </span>
                <button
                  onClick={() => toggleActive(rule)}
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${rule.is_active ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}
                  aria-label={rule.is_active ? "Pause redirect" : "Activate redirect"}
                >
                  {rule.is_active ? "Active" : "Paused"}
                </button>
                <button onClick={() => startEdit(rule)} aria-label="Edit redirect" title="Edit" className="rounded-md border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-emerald-50">
                  <FiEdit3 size={13} />
                </button>
                {confirmDelete === rule.id ? (
                  <span className="inline-flex items-center gap-1">
                    <button onClick={() => remove(rule)} className="rounded-md bg-rose-600 px-2 py-1 text-[10px] font-bold text-white hover:bg-rose-700">Delete?</button>
                    <button onClick={() => setConfirmDelete(null)} className="rounded-md border border-slate-200 px-2 py-1 text-[10px] font-bold text-slate-600">No</button>
                  </span>
                ) : (
                  <button onClick={() => setConfirmDelete(rule.id)} aria-label="Delete redirect" title="Delete" className="rounded-md border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-rose-50 hover:text-rose-600">
                    <FiTrash2 size={13} />
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
