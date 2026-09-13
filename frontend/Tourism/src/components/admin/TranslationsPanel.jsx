import { useEffect, useMemo, useState } from "react"
import { FiCheck, FiSave } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import { ALL_LANGS } from "../../i18n"
import {
  TRANSLATION_FIELDS,
  TYPE_LABELS,
  buildTranslationKey,
  cleanTranslationContent,
  translatedKeySet,
} from "../../utils/translationHelpers"

/**
 * Content Translations (brief §42) — the natural flow: Language → Search →
 * Edit. Translators pick a language, find a page/section/menu item, and fill
 * in fields next to the original text. Everything is stored through the same
 * CMS API as the Pages panel (resource: "translations", one row per
 * record + language) and the public site applies it the moment a visitor
 * switches language — no rebuild, no redeploy.
 */
export default function TranslationsPanel() {
  const { showToast } = useToast()
  const languages = ALL_LANGS.filter((l) => l.code !== "en")
  const [lang, setLang] = useState(languages[0]?.code || "ne")
  const [records, setRecords] = useState([])
  const [translations, setTranslations] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState("")
  const [selected, setSelected] = useState(null)
  const [drafts, setDrafts] = useState({})
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    try {
      const [pages, sections, navigation, translationsRes] = await Promise.all([
        adminApi.getCMS("pages"),
        adminApi.getCMS("sections"),
        adminApi.getCMS("navigation"),
        adminApi.getCMS("translations"),
      ])
      const flat = [
        ...(pages.data.results || []).map((r) => ({ type: "pages", id: r.id, title: r.title, hint: r.route, source: r })),
        ...(sections.data.results || []).map((r) => ({ type: "sections", id: r.id, title: r.title || r.key, hint: `${r.page_title || "section"} · ${r.key}`, source: r })),
        ...(navigation.data.results || []).map((r) => ({ type: "navigation", id: r.id, title: r.label, hint: `${r.location} menu`, source: r })),
      ]
      setRecords(flat)
      setTranslations(translations.data.results || [])
    } catch {
      showToast("Could not load translatable content.", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect flush.
    const t = setTimeout(() => { load() }, 0)
    return () => clearTimeout(t)
  }, [])

  const translatedKeys = useMemo(() => translatedKeySet(translations, lang), [translations, lang])
  const existingRow = (record) =>
    translations.find((row) => row.target_resource === record.type && Number(row.object_id) === Number(record.id) && row.language_code === lang)

  const visible = records.filter((record) => {
    const q = query.trim().toLowerCase()
    if (!q) return true
    return [record.title, record.hint, TYPE_LABELS[record.type]].some((value) => String(value || "").toLowerCase().includes(q))
  })
  const doneCount = records.filter((r) => translatedKeys.has(buildTranslationKey(r.type, r.id, lang))).length

  const choose = (record) => {
    if (dirty && !window.confirm("Discard unsaved translation changes?")) return
    const row = existingRow(record)
    setSelected(record)
    setDrafts(row?.content || {})
    setDirty(false)
  }

  const changeLang = (code) => {
    if (dirty && !window.confirm("Discard unsaved translation changes?")) return
    setLang(code)
    setDrafts(selected ? existingRow(selected)?.content || {} : {})
    setDirty(false)
  }

  const save = async () => {
    if (!selected || saving) return
    setSaving(true)
    try {
      const content = cleanTranslationContent(drafts, selected.type)
      const row = existingRow(selected)
      const res = row
        ? await adminApi.runCMSAction({ resource: "translations", id: row.id, content })
        : await adminApi.createCMS({ resource: "translations", target_resource: selected.type, object_id: selected.id, language_code: lang, content })
      await load()
      setDirty(false)
      showToast(res.data?.message || "Translation saved.", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Save failed — please try again.", "error")
    } finally {
      setSaving(false)
    }
  }

  const langName = languages.find((l) => l.code === lang)?.label || lang
  const fields = selected ? TRANSLATION_FIELDS[selected.type] || [] : []

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mr-auto">
          <h2 className="text-lg font-bold text-slate-900">Content Translations</h2>
          <p className="text-xs text-slate-500">
            Translate pages, sections and menu items. Visitors see the translation as soon as they switch the site language — no rebuild needed.
          </p>
        </div>
        <div className="flex gap-1.5">
          {languages.map((l) => (
            <button
              key={l.code}
              onClick={() => changeLang(l.code)}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold ${lang === l.code ? "bg-emerald-700 text-white" : "border border-emerald-200 bg-white text-slate-600 hover:bg-emerald-50"}`}
            >
              {l.flag} {l.native}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
        <section className="rounded-xl border border-emerald-200 bg-white">
          <div className="border-b border-emerald-100 p-3 space-y-2">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search pages, sections, menus…"
              aria-label="Search translatable content"
              className="w-full rounded-lg border border-emerald-200 px-2.5 py-1.5 text-xs focus:border-emerald-600 focus:outline-none"
            />
            <p className="text-[10px] font-bold text-slate-500">
              {doneCount} of {records.length} translated into {langName}
            </p>
          </div>
          <div className="max-h-[60vh] overflow-y-auto p-2 space-y-1">
            {loading && <p className="p-6 text-center text-sm text-slate-500">Loading…</p>}
            {!loading && visible.length === 0 && <p className="p-6 text-center text-sm text-slate-500">Nothing matches the search.</p>}
            {visible.map((record) => {
              const key = buildTranslationKey(record.type, record.id, lang)
              const isDone = translatedKeys.has(key)
              const isActive = selected && selected.type === record.type && selected.id === record.id
              return (
                <button
                  key={key}
                  onClick={() => choose(record)}
                  className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs ${isActive ? "bg-emerald-700 text-white" : "hover:bg-emerald-50"}`}
                >
                  <span className={isDone ? "text-emerald-500" : "text-slate-300"} aria-hidden>
                    <FiCheck size={13} className={isDone ? "" : "opacity-40"} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className={`block truncate font-bold ${isActive ? "text-white" : "text-slate-800"}`}>{record.title}</span>
                    <span className={`block truncate text-[10px] ${isActive ? "text-emerald-100" : "text-slate-500"}`}>
                      {TYPE_LABELS[record.type]} · {record.hint}
                    </span>
                  </span>
                </button>
              )
            })}
          </div>
        </section>

        <section className="rounded-xl border border-emerald-200 bg-white p-4 min-w-0">
          {!selected ? (
            <p className="p-8 text-center text-sm text-slate-500">
              Pick a page, section or menu item to translate it into {langName}.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <div className="mr-auto">
                  <h3 className="text-sm font-black text-slate-900">{selected.title}</h3>
                  <p className="text-[11px] text-slate-500">{TYPE_LABELS[selected.type]} · {selected.hint} · into {langName}</p>
                </div>
                <button
                  onClick={save}
                  disabled={saving || !dirty}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-bold text-white hover:bg-emerald-800 disabled:opacity-40"
                >
                  <FiSave /> {saving ? "Saving…" : dirty ? "Save translation" : "Saved"}
                </button>
              </div>
              {fields.map((field) => (
                <label key={field.name} className="block">
                  <span className="text-[11px] font-bold uppercase tracking-wide text-slate-600">{field.label}</span>
                  <span className="mt-1 block rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs text-slate-500">
                    <b className="text-slate-400">Original:</b> {String(selected.source[field.name] || "—").slice(0, 180) || "—"}
                  </span>
                  {field.multiline ? (
                    <textarea
                      value={drafts[field.name] || ""}
                      onChange={(event) => { setDrafts({ ...drafts, [field.name]: event.target.value }); setDirty(true) }}
                      rows={3}
                      lang={lang}
                      className="mt-1 w-full rounded-lg border border-emerald-200 px-2.5 py-1.5 text-sm focus:border-emerald-600 focus:outline-none"
                    />
                  ) : (
                    <input
                      value={drafts[field.name] || ""}
                      onChange={(event) => { setDrafts({ ...drafts, [field.name]: event.target.value }); setDirty(true) }}
                      lang={lang}
                      className="mt-1 w-full rounded-lg border border-emerald-200 px-2.5 py-1.5 text-sm focus:border-emerald-600 focus:outline-none"
                    />
                  )}
                </label>
              ))}
              <p className="text-[11px] text-slate-400">
                Fields left empty fall back to the original text on the public site.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
