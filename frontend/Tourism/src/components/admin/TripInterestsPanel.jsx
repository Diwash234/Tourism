import { useEffect, useState } from "react"
import { FiPlus, FiSave } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

/**
 * "Build your trip" interest categories (master spec §22). Admins add,
 * rename, re-order, enable/disable categories — the public recommendation
 * page renders them immediately, no code changes. The `key` doubles as the
 * mood term sent to the recommendation engine (lowercase letters/numbers/
 * underscores), so meaningful keys like `paragliding` match destination data.
 */
export default function TripInterestsPanel() {
  const { showToast } = useToast()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => {
      adminApi
        .getTripInterests()
        .then(({ data }) => setRows(data.interests || []))
        .catch(() => showToast("Could not load trip interests", "error"))
        .finally(() => setLoading(false))
    }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const update = (index, field, value) =>
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, [field]: value } : row)))

  const addRow = () =>
    setRows((prev) => [...prev, { key: "", label: "", emoji: "✨", enabled: true, order: prev.length + 1 }])

  const save = async () => {
    setSaving(true)
    try {
      const { data } = await adminApi.updateTripInterests({ interests: rows })
      setRows(data.interests || rows)
      showToast("Trip interest categories updated — the recommendation page follows immediately", "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not save interests", "error")
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="rounded-2xl border border-emerald-200 bg-white p-5 text-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-black text-lg text-emerald-950">Build-Your-Trip interest categories</h3>
          <p className="text-xs text-slate-500">
            Add/remove/rename the interest chips on the AI recommendation page — any number. Keys are the
            mood terms matched against destination data: use lowercase words like <code>paragliding</code>.
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={addRow} className="inline-flex items-center gap-2 rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-black text-emerald-800">
            <FiPlus size={14} /> Add category
          </button>
          <button type="button" onClick={save} disabled={saving || loading} className="inline-flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-2 text-sm font-black text-white disabled:opacity-50">
            <FiSave size={14} /> {saving ? "Saving…" : "Save interests"}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="py-8 text-center text-sm text-slate-500">Loading interests…</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-3">Key (mood term)</th>
                <th className="py-2 pr-3">Label (public name)</th>
                <th className="py-2 pr-3">Emoji</th>
                <th className="py-2 pr-3">Order</th>
                <th className="py-2">Enabled</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={`${row.key || "new"}-${index}`} className="border-b border-slate-100">
                  <td className="py-2 pr-3">
                    <input
                      value={row.key || ""}
                      onChange={(e) => update(index, "key", e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                      className="w-36 rounded-lg border border-slate-300 px-2 py-1 font-mono text-xs"
                      placeholder="paragliding"
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      value={row.label || ""}
                      onChange={(e) => update(index, "label", e.target.value)}
                      className="w-full min-w-40 rounded-lg border border-slate-300 px-2 py-1"
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      value={row.emoji || ""}
                      onChange={(e) => update(index, "emoji", e.target.value)}
                      className="w-16 rounded-lg border border-slate-300 px-2 py-1 text-center"
                    />
                  </td>
                  <td className="py-2 pr-3">
                    <input
                      type="number"
                      value={row.order ?? index + 1}
                      onChange={(e) => update(index, "order", Number(e.target.value))}
                      className="w-20 rounded-lg border border-slate-300 px-2 py-1"
                    />
                  </td>
                  <td className="py-2">
                    <button
                      type="button"
                      onClick={() => update(index, "enabled", !row.enabled)}
                      className={`rounded-full px-3 py-1 text-xs font-black ${row.enabled !== false ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}
                    >
                      {row.enabled !== false ? "On" : "Off"}
                    </button>
                  </td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan="5" className="py-6 text-center text-sm text-slate-500">
                    No custom categories yet — the built-in defaults are shown publicly. Add your first one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
