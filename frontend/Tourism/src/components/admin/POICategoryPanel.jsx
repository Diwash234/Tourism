import { useEffect, useState } from "react"
import { FiSave } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

/**
 * Nearby-place category catalogue (master spec §4). Admins rename, re-order,
 * enable/disable and cap every real-world POI category used by the public
 * Nearby page and destination "What's Actually Near" sections. OpenStreetMap
 * tag mappings stay code-managed — admins configure presentation, never raw
 * query strings (injection safety).
 */
export default function POICategoryPanel() {
  const { showToast } = useToast()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => {
      adminApi
        .getPOICategories()
        .then(({ data }) => setRows(data.categories || []))
        .catch(() => showToast("Could not load POI categories", "error"))
        .finally(() => setLoading(false))
    }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const update = (key, field, value) =>
    setRows((prev) => prev.map((row) => (row.key === key ? { ...row, [field]: value } : row)))

  const save = async () => {
    setSaving(true)
    try {
      const { data } = await adminApi.updatePOICategories({ categories: rows })
      setRows(data.categories || rows)
      showToast("Nearby-place categories updated — public nearby search follows immediately", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save categories", "error")
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="rounded-2xl border border-emerald-200 bg-white p-5 text-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-black text-lg text-emerald-950">Nearby-place categories</h3>
          <p className="text-xs text-slate-500">
            Controls the real-world categories (OpenStreetMap) on the public Nearby page and destination
            pages. Rename, re-order, enable/disable, and set result limits. Search tags stay code-managed
            for safety.
          </p>
        </div>
        <button
          type="button"
          onClick={save}
          disabled={saving || loading}
          className="inline-flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-2 text-sm font-black text-white disabled:opacity-50"
        >
          <FiSave size={14} /> {saving ? "Saving…" : "Save categories"}
        </button>
      </div>

      {loading ? (
        <p className="py-8 text-center text-sm text-slate-500">Loading categories…</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-3">Icon</th>
                <th className="py-2 pr-3">Label (public name)</th>
                <th className="py-2 pr-3">Order</th>
                <th className="py-2 pr-3">Max results</th>
                <th className="py-2">Enabled</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-slate-100">
                  <td className="py-2 pr-3">
                    <input
                      value={row.icon || ""}
                      onChange={(e) => update(row.key, "icon", e.target.value)}
                      className="w-14 rounded-lg border border-slate-300 px-2 py-1 text-center"
                      aria-label={`Icon for ${row.key}`}
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      value={row.label || ""}
                      onChange={(e) => update(row.key, "label", e.target.value)}
                      className="w-full min-w-40 rounded-lg border border-slate-300 px-2 py-1"
                      aria-label={`Label for ${row.key}`}
                    />
                    <p className="mt-0.5 text-[10px] text-slate-400">{row.key}</p>
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      type="number"
                      value={row.order ?? 0}
                      onChange={(e) => update(row.key, "order", Number(e.target.value))}
                      className="w-20 rounded-lg border border-slate-300 px-2 py-1"
                      aria-label={`Order for ${row.key}`}
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      type="number"
                      min="1"
                      max="25"
                      value={row.limit ?? 10}
                      onChange={(e) => update(row.key, "limit", Number(e.target.value))}
                      className="w-20 rounded-lg border border-slate-300 px-2 py-1"
                      aria-label={`Limit for ${row.key}`}
                    />
                  </td>
                  <td className="py-2">
                    <button
                      type="button"
                      onClick={() => update(row.key, "enabled", !row.enabled)}
                      className={`rounded-full px-3 py-1 text-xs font-black ${row.enabled ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}
                    >
                      {row.enabled ? "On" : "Off"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
