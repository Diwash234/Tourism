import { useEffect, useMemo, useState } from "react"
import { FiCheck, FiPlus, FiRefreshCw, FiSave, FiSearch } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import useToast from "../../hooks/useToast"
import { ALL_LANGS } from "../../i18n"

/**
 * UI Strings — admin editor for the frontend's t("...") dictionary.
 *
 * Every row is one {key, language, value} override stored in the
 * UITranslation table. The public site fetches all rows for its active
 * language and merges them over the bundled dictionary, so an edit here
 * applies to every visitor the moment they switch language — no rebuild.
 *
 * - Search filters by key or English source text.
 * - "Missing" filter shows keys with no translation in the target language.
 * - "Add key" creates a brand-new UI string (key + English + translations).
 * - Blank value + save deletes the override (falls back to bundled string).
 */
const EDITABLE_LANGS = ALL_LANGS.filter((l) => l.code !== "en")

export default function UITranslationsPanel() {
  const { showToast } = useToast()
  const [lang, setLang] = useState(EDITABLE_LANGS[0]?.code || "ne")
  const [bundle, setBundle] = useState({}) // {key: {en, ne, hi}} from DB seed
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState("")
  const [showMissing, setShowMissing] = useState(false)
  const [drafts, setDrafts] = useState({})
  const [saving, setSaving] = useState(false)
  const [newKey, setNewKey] = useState("")
  const [newEn, setNewEn] = useState("")
  const [adding, setAdding] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [enRes, langRes] = await Promise.all([
        axiosClient.get("/translation/ui-strings/", { params: { lang: "en" } }),
        axiosClient.get("/translation/ui-strings/", { params: { lang } }),
      ])
      const enStrings = enRes.data || {}
      const langStrings = langRes.data || {}
      const merged = {}
      for (const key of Object.keys(enStrings)) {
        merged[key] = { en: enStrings[key] || "", [lang]: langStrings[key] || "" }
      }
      // Keys that exist in target lang but not in en (custom admin keys)
      for (const key of Object.keys(langStrings)) {
        if (!merged[key]) merged[key] = { en: "", [lang]: langStrings[key] || "" }
      }
      setBundle(merged)
      setDrafts({})
    } catch {
      showToast("Could not load UI strings.", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const t = setTimeout(() => { load() }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang])

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return Object.entries(bundle)
      .filter(([key, vals]) => {
        if (showMissing && (vals[lang] || "").trim()) return false
        if (!q) return true
        return key.toLowerCase().includes(q) || (vals.en || "").toLowerCase().includes(q)
      })
      .sort(([a], [b]) => a.localeCompare(b))
  }, [bundle, query, showMissing, lang])

  const dirtyCount = Object.keys(drafts).length
  const missingCount = useMemo(
    () => Object.values(bundle).filter((v) => !(v[lang] || "").trim()).length,
    [bundle, lang]
  )

  const save = async () => {
    const items = Object.entries(drafts).map(([key, value]) => ({ key, language: lang, value }))
    if (!items.length) return
    setSaving(true)
    try {
      const res = await axiosClient.post("/translation/ui-strings/bulk/", items)
      showToast(`Saved ${res.data?.saved ?? items.length} translation(s). Live on next language switch.`, "success")
      await load()
    } catch {
      showToast("Could not save translations.", "error")
    } finally {
      setSaving(false)
    }
  }

  const addKey = async () => {
    const key = newKey.trim()
    if (!key) {
      showToast("Enter a key like homepage.hero_title.", "error")
      return
    }
    if (bundle[key]) {
      showToast("That key already exists — edit it in the list.", "error")
      return
    }
    setAdding(true)
    try {
      await axiosClient.post("/translation/ui-strings/bulk/", [
        { key, language: "en", value: newEn.trim() || key },
        ...(drafts[`__new_${key}`]?.trim()
          ? [{ key, language: lang, value: drafts[`__new_${key}`].trim() }]
          : []),
      ])
      showToast(`Added "${key}".`, "success")
      setNewKey("")
      setNewEn("")
      setDrafts((d) => {
        const next = { ...d }
        delete next[`__new_${key}`]
        return next
      })
      await load()
    } catch {
      showToast("Could not add key.", "error")
    } finally {
      setAdding(false)
    }
  }

  const autoTranslateMissing = async () => {
    const missing = rows.filter(([, vals]) => !(vals[lang] || "").trim())
    if (!missing.length) {
      showToast("Nothing missing in this view.", "success")
      return
    }
    setSaving(true)
    try {
      const items = []
      for (const [key, vals] of missing.slice(0, 50)) {
        const res = await axiosClient.post("/translate/", {
          text: vals.en || key,
          target_language: lang,
          source_language: "en",
        })
        const translated = res.data?.translated_text || res.data?.translatedText || ""
        if (translated) items.push({ key, language: lang, value: translated })
      }
      if (items.length) {
        await axiosClient.post("/translation/ui-strings/bulk/", items)
        showToast(`Auto-translated ${items.length} string(s) — please review them.`, "success")
        await load()
      }
    } catch {
      showToast("Auto-translate failed.", "error")
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-500">Loading UI strings…</p>

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
            placeholder="Search by key or English text…"
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-lg"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={showMissing} onChange={(e) => setShowMissing(e.target.checked)} />
          Missing only ({missingCount})
        </label>
        <button
          onClick={autoTranslateMissing}
          disabled={saving}
          className="px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          title="Machine-translate up to 50 missing strings in this view (review afterwards)"
        >
          Auto-translate
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

      <div className="flex flex-wrap items-end gap-2 p-3 bg-gray-50 border rounded-lg">
        <div className="flex-1 min-w-[180px]">
          <label className="block text-xs font-medium text-gray-600">New key</label>
          <input value={newKey} onChange={(e) => setNewKey(e.target.value)} placeholder="section.title" className="w-full px-2 py-1.5 text-sm border rounded" />
        </div>
        <div className="flex-1 min-w-[180px]">
          <label className="block text-xs font-medium text-gray-600">English text</label>
          <input value={newEn} onChange={(e) => setNewEn(e.target.value)} placeholder="Section title" className="w-full px-2 py-1.5 text-sm border rounded" />
        </div>
        <div className="flex-1 min-w-[180px]">
          <label className="block text-xs font-medium text-gray-600">{EDITABLE_LANGS.find((l) => l.code === lang)?.native} text (optional)</label>
          <input
            value={drafts[`__new_${newKey.trim()}`] || ""}
            onChange={(e) => setDrafts((d) => ({ ...d, [`__new_${newKey.trim()}`]: e.target.value }))}
            placeholder="अनुवाद"
            className="w-full px-2 py-1.5 text-sm border rounded"
          />
        </div>
        <button onClick={addKey} disabled={adding || !newKey.trim()} className="flex items-center gap-1 px-3 py-1.5 text-sm text-white bg-green-600 rounded disabled:opacity-50">
          <FiPlus /> Add
        </button>
      </div>

      <div className="overflow-auto border rounded-lg max-h-[60vh]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-gray-100">
            <tr>
              <th className="text-left px-3 py-2 w-1/4">Key</th>
              <th className="text-left px-3 py-2 w-1/3">English (source)</th>
              <th className="text-left px-3 py-2 w-5/12">{EDITABLE_LANGS.find((l) => l.code === lang)?.native} translation</th>
              <th className="px-3 py-2 w-12" />
            </tr>
          </thead>
          <tbody>
            {rows.map(([key, vals]) => {
              const isDirty = key in drafts
              const current = isDirty ? drafts[key] : (vals[lang] || "")
              return (
                <tr key={key} className={`border-t ${isDirty ? "bg-yellow-50" : ""}`}>
                  <td className="px-3 py-2 font-mono text-xs text-gray-600 break-all">{key}</td>
                  <td className="px-3 py-2 text-gray-800">{vals.en || <span className="text-gray-400 italic">—</span>}</td>
                  <td className="px-3 py-2">
                    <textarea
                      value={current}
                      onChange={(e) => setDrafts((d) => ({ ...d, [key]: e.target.value }))}
                      rows={1}
                      placeholder={!(vals[lang] || "").trim() ? "Missing — type translation…" : ""}
                      className={`w-full px-2 py-1 text-sm border rounded resize-y ${!(vals[lang] || "").trim() && !isDirty ? "border-orange-300 bg-orange-50" : ""}`}
                    />
                  </td>
                  <td className="px-3 py-2 text-green-600">{isDirty && <FiCheck />}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {!rows.length && <p className="p-4 text-sm text-gray-500">No strings match.</p>}
      </div>
    </div>
  )
}
