import { useEffect, useMemo, useState } from "react"
import { FiCheck, FiRefreshCw, FiSave, FiSearch } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import { ALL_LANGS } from "../../i18n"

/**
 * Destination Translations — admin editor for per-destination name /
 * description translations (tourist.DestinationTranslation).
 *
 * Flow: pick a language → search a destination → edit name/description
 * next to the English source. Rows flagged "auto" were machine-generated
 * and should be reviewed; saving clears the auto flag (human-approved).
 * "Auto-fill" machine-translates all missing destinations for the language
 * via the backend engine (best-effort — rate limits may skip some).
 */
const EDITABLE_LANGS = ALL_LANGS.filter((l) => l.code !== "en")

export default function DestinationTranslationsPanel() {
  const { showToast } = useToast()
  const [lang, setLang] = useState(EDITABLE_LANGS[0]?.code || "ne")
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState("")
  const [showMissing, setShowMissing] = useState(false)
  const [showAuto, setShowAuto] = useState(false)
  const [drafts, setDrafts] = useState({})
  const [saving, setSaving] = useState(false)
  const [autoFilling, setAutoFilling] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminApi.getTranslations({ language__code: lang, page_size: 500 })
      setRows(res.data?.results || res.data || [])
      setDrafts({})
    } catch {
      showToast("Could not load destination translations.", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const t = setTimeout(() => { load() }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((r) => {
      const name = (r.destination_name || r.name || "").toLowerCase()
      if (q && !name.includes(q)) return false
      if (showMissing && (r.name || "").trim() && (r.description || "").trim()) return false
      if (showAuto && !r.is_auto_generated) return false
      return true
    })
  }, [rows, query, showMissing, showAuto])

  const dirtyCount = Object.keys(drafts).length

  const save = async () => {
    const entries = Object.entries(drafts)
    if (!entries.length) return
    setSaving(true)
    try {
      for (const [id, vals] of entries) {
        await adminApi.updateTranslation(id, { ...vals, is_auto_generated: false })
      }
      showToast(`Saved ${entries.length} translation(s) and marked human-approved.`, "success")
      await load()
    } catch {
      showToast("Could not save translations.", "error")
    } finally {
      setSaving(false)
    }
  }

  const autoFill = async () => {
    setAutoFilling(true)
    try {
      // Fetch destinations missing a translation in this language.
      const destRes = await axiosClient.get("/destinations/", {
        params: { page_size: 100, untranslated_lang: lang },
      }).catch(() => ({ data: { results: [] } }))
      const dests = destRes.data?.results || destRes.data || []
      let filled = 0
      for (const d of dests.slice(0, 30)) {
        try {
          await axiosClient.post(`/destinations/${d.slug || d.id}/translate/`, { language_code: lang })
          filled += 1
        } catch {
          /* rate-limited or MT down — skip, admin can retry */
        }
      }
      showToast(filled ? `Auto-filled ${filled} destination(s) — please review.` : "Nothing to fill or translation service unavailable.", filled ? "success" : "error")
      await load()
    } finally {
      setAutoFilling(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-500">Loading destination translations…</p>

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex rounded-lg border overflow-hidden">
          {EDITABLE_LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => setLang(l.code)}
              className={`px-4 py-2 text-sm font-medium ${lang === l.code ? "bg-blue-600 text-white" : "bg-white text-gray-700 hover:bg-gray-50"}`}
            >
              {l.flag} {l.native}
            </button>
          ))}
        </div>
        <div className="relative flex-1 min-w-[200px]">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search destination…"
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={showMissing} onChange={(e) => setShowMissing(e.target.checked)} />
          Incomplete only
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={showAuto} onChange={(e) => setShowAuto(e.target.checked)} />
          Auto-generated only
        </label>
        <button onClick={autoFill} disabled={autoFilling} className="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50" title="Machine-translate up to 30 missing destinations">
          {autoFilling ? "Filling…" : "Auto-fill missing"}
        </button>
        <button onClick={load} className="p-2 border rounded-lg hover:bg-gray-50" title="Reload">
          <FiRefreshCw />
        </button>
        <button
          onClick={save}
          disabled={!dirtyCount || saving}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg disabled:opacity-50"
        >
          <FiSave /> Save ({dirtyCount})
        </button>
      </div>

      <div className="overflow-auto border rounded-lg max-h-[60vh]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-gray-100">
            <tr>
              <th className="text-left px-3 py-2">Destination</th>
              <th className="text-left px-3 py-2">Name ({EDITABLE_LANGS.find((l) => l.code === lang)?.native})</th>
              <th className="text-left px-3 py-2">Description</th>
              <th className="px-3 py-2 w-16">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => {
              const d = drafts[r.id] || {}
              const isDirty = r.id in drafts
              return (
                <tr key={r.id} className={`border-t ${isDirty ? "bg-yellow-50" : ""}`}>
                  <td className="px-3 py-2 font-medium whitespace-nowrap">
                    {r.destination_name || r.destination}
                    <div className="text-xs font-normal text-gray-500">{r.destination_slug}</div>
                  </td>
                  <td className="px-3 py-2 min-w-[180px]">
                    <input
                      value={d.name ?? r.name ?? ""}
                      onChange={(e) => setDrafts((prev) => ({ ...prev, [r.id]: { ...prev[r.id], name: e.target.value } }))}
                      className="w-full px-2 py-1 text-sm border rounded"
                    />
                  </td>
                  <td className="px-3 py-2 min-w-[240px]">
                    <textarea
                      value={d.description ?? r.description ?? ""}
                      onChange={(e) => setDrafts((prev) => ({ ...prev, [r.id]: { ...prev[r.id], description: e.target.value } }))}
                      rows={2}
                      className="w-full px-2 py-1 text-sm border rounded resize-y"
                    />
                  </td>
                  <td className="px-3 py-2 text-center">
                    {isDirty
                      ? <span className="text-green-600"><FiCheck /></span>
                      : r.is_auto_generated
                        ? <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-800">auto</span>
                        : <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">human</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {!filtered.length && <p className="p-4 text-sm text-gray-500">No translations match. Use Auto-fill to generate missing ones.</p>}
      </div>
    </div>
  )
}
