import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { FiArrowDown, FiArrowUp, FiEdit3, FiExternalLink, FiEye, FiEyeOff, FiSave } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

/**
 * Homepage Manager (brief §7) — manages the real homepage sections stored in
 * the CMS (ContentSection rows for the "/" ManagedPage). Everything here is
 * backed by the same admin CMS API the Pages panel uses:
 *   - hero fields edit  -> PATCH {resource:"sections", id, ...fields}
 *   - show/hide section -> PATCH {resource:"sections", id, is_visible}
 *   - reorder           -> PATCH {resource:"pages", id, action:"reorder", section_ids}
 * Every mutation awaits the backend, re-fetches from it, and only then shows
 * success — the backend response is the source of truth (brief §7/§16/§26).
 */
export default function HomepageManagerPanel() {
  const { showToast } = useToast()
  const [homePage, setHomePage] = useState(null)
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [heroDraft, setHeroDraft] = useState(null)
  const [busy, setBusy] = useState("")

  const load = async () => {
    try {
      const [pagesRes, sectionsRes] = await Promise.all([
        adminApi.getCMS("pages"),
        adminApi.getCMS("sections"),
      ])
      const pages = pagesRes.data.results || pagesRes.data || []
      const home = pages.find((page) => page.route === "/") || null
      const all = sectionsRes.data.results || sectionsRes.data || []
      const homeSections = all
        .filter((section) => home && section.page_id === home.id)
        .sort((a, b) => (a.display_order || 0) - (b.display_order || 0) || a.id - b.id)
      setHomePage(home)
      setSections(homeSections)
      const hero = homeSections.find((section) => section.key === "hero") || homeSections[0] || null
      setHeroDraft(hero ? {
        id: hero.id,
        title: hero.title || "",
        subtitle: hero.subtitle || "",
        body: hero.body || "",
        cta_text: hero.cta_text || "",
        cta_url: hero.cta_url || "",
        image_url: hero.image_url || "",
      } : null)
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load homepage content", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Deferred one tick: keeps synchronous setState out of the effect flush.
    const t = setTimeout(() => { load() }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const mutate = async (payload, successMessage, busyKey) => {
    setBusy(busyKey)
    try {
      await adminApi.updateCMS(payload)
      await load() // backend response is the new source of truth
      showToast(successMessage, "success")
    } catch (error) {
      showToast(error.response?.data?.detail || "Update failed", "error")
    } finally {
      setBusy("")
    }
  }

  const saveHero = async (event) => {
    event.preventDefault()
    if (!heroDraft) return
    await mutate(
      { resource: "sections", id: heroDraft.id, title: heroDraft.title, subtitle: heroDraft.subtitle, body: heroDraft.body, cta_text: heroDraft.cta_text, cta_url: heroDraft.cta_url, image_url: heroDraft.image_url },
      "Hero saved & live on the public homepage",
      "hero"
    )
  }

  const toggleSection = (section) =>
    mutate(
      { resource: "sections", id: section.id, is_visible: !section.is_visible },
      section.is_visible ? `"${section.title || section.key}" hidden on the public site` : `"${section.title || section.key}" shown on the public site`,
      `vis-${section.id}`
    )

  const move = async (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= sections.length || !homePage) return
    const ids = sections.map((section) => section.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    await mutate(
      { resource: "pages", id: homePage.id, action: "reorder", section_ids: ids },
      "Section order saved",
      "reorder"
    )
  }

  const field = "w-full rounded-xl border border-slate-600/50 bg-slate-800/60 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none"

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-emerald-950">Homepage Manager</h2>
          <p className="text-sm text-emerald-900/60">
            Edit the public homepage without touching code. Changes save to the CMS and appear on the live site immediately.
          </p>
        </div>
        <a href="/?as=traveller" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 self-start rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-black text-white hover:bg-emerald-600 whitespace-nowrap">
          <FiExternalLink /> Preview homepage
        </a>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading homepage sections…</p>}
      {!loading && !homePage && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          No page with route <code>/</code> exists in the CMS yet. Create the Home page in <Link className="font-bold underline" to="/admin?section=cms">Pages, Sections &amp; Menus</Link> first.
        </div>
      )}

      {!loading && heroDraft && (
        <form onSubmit={saveHero} className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5 space-y-3">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-300">Hero (top of homepage)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <label className="block text-xs font-bold text-slate-300">Title
              <input className={`${field} mt-1`} value={heroDraft.title} onChange={(e) => setHeroDraft({ ...heroDraft, title: e.target.value })} />
            </label>
            <label className="block text-xs font-bold text-slate-300">Subtitle
              <input className={`${field} mt-1`} value={heroDraft.subtitle} onChange={(e) => setHeroDraft({ ...heroDraft, subtitle: e.target.value })} />
            </label>
          </div>
          <label className="block text-xs font-bold text-slate-300">Description
            <textarea rows={2} className={`${field} mt-1`} value={heroDraft.body} onChange={(e) => setHeroDraft({ ...heroDraft, body: e.target.value })} />
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <label className="block text-xs font-bold text-slate-300">Primary button text
              <input className={`${field} mt-1`} value={heroDraft.cta_text} onChange={(e) => setHeroDraft({ ...heroDraft, cta_text: e.target.value })} />
            </label>
            <label className="block text-xs font-bold text-slate-300">Button link
              <input className={`${field} mt-1`} value={heroDraft.cta_url} onChange={(e) => setHeroDraft({ ...heroDraft, cta_url: e.target.value })} placeholder="/destinations" />
            </label>
            <label className="block text-xs font-bold text-slate-300">Background image URL
              <input className={`${field} mt-1`} value={heroDraft.image_url} onChange={(e) => setHeroDraft({ ...heroDraft, image_url: e.target.value })} placeholder="https://…" />
            </label>
          </div>
          <button type="submit" disabled={busy === "hero"} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-black text-white hover:bg-emerald-500 disabled:opacity-50">
            <FiSave /> {busy === "hero" ? "Saving…" : "Save hero"}
          </button>
        </form>
      )}

      {!loading && sections.length > 0 && (
        <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-3">Homepage sections ({sections.length})</h3>
          <ul className="space-y-2">
            {sections.map((section, index) => (
              <li key={section.id} className={`flex flex-wrap items-center gap-3 rounded-xl border px-4 py-3 ${section.is_visible ? "border-slate-600/40 bg-slate-800/50" : "border-slate-700/40 bg-slate-800/20 opacity-60"}`}>
                <span className="w-6 text-center text-xs font-black text-slate-400">{index + 1}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-bold text-white">{section.title || section.key}</span>
                  <span className="text-[11px] text-slate-400">{section.key} · {section.section_type || "section"}</span>
                </span>
                <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase ${section.is_visible ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-600/40 text-slate-300"}`}>
                  {section.is_visible ? "Visible" : "Hidden"}
                </span>
                <div className="flex items-center gap-1.5">
                  <button type="button" onClick={() => move(index, -1)} disabled={index === 0 || busy === "reorder"} aria-label={`Move ${section.title || section.key} up`} className="rounded-lg bg-slate-700/60 p-2 text-slate-200 hover:bg-slate-600 disabled:opacity-30"><FiArrowUp size={14} /></button>
                  <button type="button" onClick={() => move(index, 1)} disabled={index === sections.length - 1 || busy === "reorder"} aria-label={`Move ${section.title || section.key} down`} className="rounded-lg bg-slate-700/60 p-2 text-slate-200 hover:bg-slate-600 disabled:opacity-30"><FiArrowDown size={14} /></button>
                  <button type="button" onClick={() => toggleSection(section)} disabled={busy === `vis-${section.id}`} className="inline-flex items-center gap-1.5 rounded-lg bg-slate-700/60 px-3 py-2 text-xs font-bold text-slate-100 hover:bg-slate-600 disabled:opacity-50">
                    {section.is_visible ? <FiEyeOff size={14} /> : <FiEye size={14} />}
                    {busy === `vis-${section.id}` ? "Saving…" : section.is_visible ? "Hide" : "Show"}
                  </button>
                  <Link to="/admin?section=cms" className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600/80 px-3 py-2 text-xs font-bold text-white hover:bg-emerald-500" aria-label={`Edit ${section.title || section.key} in the page editor`}>
                    <FiEdit3 size={14} /> Edit
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
