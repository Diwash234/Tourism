import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import {
  FiArrowDown, FiArrowUp, FiCheckCircle, FiClock, FiEdit3, FiExternalLink,
  FiEye, FiEyeOff, FiImage, FiLayers, FiRotateCcw, FiSave, FiSearch, FiSend, FiX,
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import CMSBlock from "../cms/CMSBlock"
import { ContentBlocksBuilder } from "./CMSPanel"

const LAYOUT_VARIANTS = ["default", "compact", "wide", "cards", "hero", "split"]
const CONTENT_FIELDS = ["title", "subtitle", "body", "image_url", "cta_text", "cta_url", "icon", "section_type", "layout_variant", "config"]
const PREVIEW_WIDTHS = { Desktop: "100%", Tablet: "834px", Mobile: "390px" }

const hasPendingChanges = (section) => {
  const snap = section.published_snapshot
  if (!snap) return false // legacy: edits go live directly
  return CONTENT_FIELDS.some((f) => {
    const a = f === "config" ? JSON.stringify(section[f] || {}) : (section[f] ?? "")
    const b = f === "config" ? JSON.stringify(snap[f] || {}) : (snap[f] ?? "")
    return String(a) !== String(b)
  })
}

/**
 * Homepage Editor (CMS prompt §4–§35) — manages the real homepage sections
 * (ContentSection rows for the "/" ManagedPage) with the full
 * Edit → Save Draft → Preview → Publish flow:
 *   - Save Draft  PATCH {resource:"sections", id, ...fields}   (public unchanged)
 *   - Preview     renders the SAME CMSBlock component the public site uses,
 *                 at Desktop/Tablet/Mobile widths
 *   - Publish     PATCH {resource:"sections", id, action:"publish"} → the
 *                 backend freezes a snapshot the public config serves
 *   - Show/Hide + reorder stay immediate (structural), as before
 *   - History/rollback via the existing CMSRevision endpoints
 * Blocks (travel-planning style cards) reuse CMSPanel's ContentBlocksBuilder.
 */
export default function HomepageManagerPanel() {
  const { showToast } = useToast()
  const [homePage, setHomePage] = useState(null)
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState("")
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewWidth, setPreviewWidth] = useState("Desktop")
  const [historyFor, setHistoryFor] = useState(null)
  const [revisions, setRevisions] = useState([])
  const [mediaPicker, setMediaPicker] = useState(false)
  const [fullPreview, setFullPreview] = useState(false)
  const [scheduleAt, setScheduleAt] = useState("")
  const [seoOpen, setSeoOpen] = useState(false)
  const [seo, setSeo] = useState(null)
  const [mediaRows, setMediaRows] = useState([])
  const [mediaQ, setMediaQ] = useState("")

  const load = async (keepSelection = true) => {
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
      setSeo(home ? { title: home.title || "", meta_description: home.meta_description || "", seo_title: home.seo_title || "", og_image_url: home.og_image_url || "" } : null)
      setSections(homeSections)
      if (!keepSelection || !homeSections.some((s) => s.id === selectedId)) {
        const first = homeSections.find((s) => s.key === "hero") || homeSections[0] || null
        setSelectedId(first ? first.id : null)
      }
    } catch (error) {
      showToast(error.response?.data?.detail || "Could not load homepage content", "error")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const t = setTimeout(() => { load(false) }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Sync the editor draft from the server copy whenever selection/sections change.
  const selected = sections.find((s) => s.id === selectedId) || null
  useEffect(() => {
    const t = setTimeout(() => {
      setDraft(selected ? { ...selected } : null)
    }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, sections])

  const dirty = draft && selected && CONTENT_FIELDS.some((f) =>
    String(f === "config" ? JSON.stringify(draft[f] || {}) : (draft[f] ?? "")) !==
    String(f === "config" ? JSON.stringify(selected[f] || {}) : (selected[f] ?? "")))

  const mutate = async (payload, successMessage, busyKey) => {
    setBusy(busyKey)
    try {
      await adminApi.updateCMS(payload)
      await load()
      showToast(successMessage, "success")
      return true
    } catch (error) {
      showToast(error.response?.data?.detail || "Update failed", "error")
      return false
    } finally {
      setBusy("")
    }
  }

  const saveDraft = () => {
    if (!draft) return
    const payload = { resource: "sections", id: draft.id }
    for (const f of CONTENT_FIELDS) payload[f] = draft[f]
    return mutate(payload, "Draft saved — public homepage unchanged until you Publish", "save")
  }

  const publish = () => {
    if (!draft) return
    return mutate({ resource: "sections", id: draft.id, action: "publish" },
      `“${draft.title || draft.key}” published to the homepage`, "publish")
  }

  const saveAndPublish = async () => {
    if (await saveDraft()) await publish()
  }

  const toggleSection = (section) =>
    mutate({ resource: "sections", id: section.id, is_visible: !section.is_visible },
      section.is_visible ? `“${section.title || section.key}” hidden on the public site` : `“${section.title || section.key}” shown on the public site`,
      `vis-${section.id}`)

  const move = async (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= sections.length || !homePage) return
    const ids = sections.map((section) => section.id)
    ;[ids[index], ids[target]] = [ids[target], ids[index]]
    await mutate({ resource: "pages", id: homePage.id, action: "reorder", section_ids: ids }, "Section order saved", "reorder")
  }

  const openHistory = async (section) => {
    setHistoryFor(section)
    try {
      const { data } = await adminApi.getCMS("sections", { id: section.id, history: 1 })
      setRevisions(data.results || [])
    } catch {
      setRevisions([])
    }
  }

  const rollback = async (revision) => {
    const ok = await mutate({ resource: "sections", id: historyFor.id, action: "rollback", revision_id: revision.id },
      `Rolled back to revision #${revision.revision_number} (draft) — Publish to make it public`, "rollback")
    if (ok) setHistoryFor(null)
  }

  const openMediaPicker = async () => {
    setMediaPicker(true)
    try {
      const { data } = await adminApi.getMediaLibrary({ page_size: 24 })
      setMediaRows(data.results || data || [])
    } catch {
      setMediaRows([])
    }
  }

  const searchMedia = async (q) => {
    setMediaQ(q)
    try {
      const { data } = await adminApi.getMediaLibrary({ q, page_size: 24 })
      setMediaRows(data.results || data || [])
    } catch {
      setMediaRows([])
    }
  }

  const pendingSections = sections.filter((sct) => sct.status === "published" ? hasPendingChanges(sct) : sct.status !== "published")

  const publishAll = async () => {
    setBusy("publish-all")
    let ok = 0
    for (const sct of pendingSections) {
      try {
        await adminApi.updateCMS({ resource: "sections", id: sct.id, action: "publish" })
        ok += 1
      } catch (error) {
        showToast(error.response?.data?.detail || `Could not publish “${sct.title || sct.key}”`, "error")
      }
    }
    await load()
    setBusy("")
    showToast(`${ok} section${ok === 1 ? "" : "s"} published to the homepage`, "success")
  }

  const schedulePublish = () => {
    if (!draft || !scheduleAt) return
    return mutate({ resource: "sections", id: draft.id, action: "schedule", scheduled_publish_at: new Date(scheduleAt).toISOString() },
      `Scheduled “${draft.title || draft.key}” to publish at ${new Date(scheduleAt).toLocaleString()}`, "schedule")
  }

  const unpublish = () => {
    if (!draft) return
    if (!window.confirm(`Unpublish “${draft.title || draft.key}”? It will disappear from the public homepage until published again.`)) return
    return mutate({ resource: "sections", id: draft.id, action: "unpublish" },
      `“${draft.title || draft.key}” unpublished — hidden from the public homepage`, "unpublish")
  }

  const saveSeo = () => {
    if (!homePage || !seo) return
    return mutate({ resource: "pages", id: homePage.id, ...seo }, "Homepage SEO settings saved", "seo")
  }

  const field = "w-full rounded-xl border border-slate-600/50 bg-slate-800/60 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none"
  const statusChip = (section) => {
    if (section.status !== "published") return <span className="rounded-full bg-amber-500/20 px-2.5 py-1 text-[10px] font-black uppercase text-amber-300 flex items-center gap-1"><FiClock size={10} /> {section.status}</span>
    if (hasPendingChanges(section)) return <span className="rounded-full bg-sky-500/20 px-2.5 py-1 text-[10px] font-black uppercase text-sky-300 flex items-center gap-1"><FiEdit3 size={10} /> Draft pending</span>
    return <span className="rounded-full bg-emerald-500/20 px-2.5 py-1 text-[10px] font-black uppercase text-emerald-300 flex items-center gap-1"><FiCheckCircle size={10} /> Live</span>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black text-emerald-950">Homepage Editor</h2>
          <p className="text-sm text-emerald-900/60">
            Edit → Save Draft → Preview → Publish. Drafts never touch the public site; only Publish updates the homepage.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 self-start">
          {pendingSections.length > 0 && (
            <button type="button" onClick={publishAll} disabled={busy !== ""} className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-black text-slate-950 hover:bg-amber-400 disabled:opacity-50 whitespace-nowrap">
              <FiSend size={14} /> {busy === "publish-all" ? "Publishing…" : `Publish All Changes (${pendingSections.length})`}
            </button>
          )}
          <button type="button" onClick={() => setFullPreview(true)} className="inline-flex items-center gap-2 rounded-xl bg-sky-600/90 px-4 py-2.5 text-sm font-black text-white hover:bg-sky-500 whitespace-nowrap">
            <FiEye size={14} /> Preview full page
          </button>
          <button type="button" onClick={() => setSeoOpen((v) => !v)} className="inline-flex items-center gap-2 rounded-xl bg-slate-700 px-4 py-2.5 text-sm font-black text-slate-100 hover:bg-slate-600 whitespace-nowrap">
            <FiSearch size={14} /> SEO
          </button>
          <a href="/?as=traveller" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-black text-white hover:bg-emerald-600 whitespace-nowrap">
            <FiExternalLink /> View public homepage
          </a>
        </div>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading homepage sections…</p>}
      {!loading && !homePage && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          No page with route <code>/</code> exists in the CMS yet. Create the Home page in <Link className="font-bold underline" to="/admin?section=cms">Pages, Sections &amp; Menus</Link> first.
        </div>
      )}

      {!loading && homePage && seoOpen && seo && (
        <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5 space-y-3">
          <h3 className="text-sm font-black uppercase tracking-wider text-slate-300">Homepage SEO &amp; sharing</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <label className="block text-xs font-bold text-slate-300">Page title
              <input className={`${field} mt-1`} value={seo.title} onChange={(e) => setSeo({ ...seo, title: e.target.value })} />
            </label>
            <label className="block text-xs font-bold text-slate-300">Search-result title (optional)
              <input className={`${field} mt-1`} value={seo.seo_title} onChange={(e) => setSeo({ ...seo, seo_title: e.target.value })} />
            </label>
          </div>
          <label className="block text-xs font-bold text-slate-300">Meta description
            <textarea rows={2} className={`${field} mt-1`} value={seo.meta_description} onChange={(e) => setSeo({ ...seo, meta_description: e.target.value })} />
          </label>
          <label className="block text-xs font-bold text-slate-300">Social share (OG) image URL
            <input className={`${field} mt-1`} value={seo.og_image_url} onChange={(e) => setSeo({ ...seo, og_image_url: e.target.value })} placeholder="https://…" />
          </label>
          <button type="button" onClick={saveSeo} disabled={busy !== ""} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-black text-white hover:bg-emerald-500 disabled:opacity-50">
            <FiSave size={14} /> {busy === "seo" ? "Saving…" : "Save SEO settings"}
          </button>
        </div>
      )}

      {!loading && homePage && (
        <div className="grid gap-5 lg:grid-cols-5">
          {/* ── Left: section list ─────────────────────────────── */}
          <div className="lg:col-span-2 bg-slate-900/70 border border-slate-600/40 rounded-2xl p-4">
            <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2"><FiLayers size={14} /> Homepage sections ({sections.length})</h3>
            <ul className="space-y-2">
              {sections.map((section, index) => (
                <li key={section.id} className={`rounded-xl border px-3 py-2.5 transition ${selectedId === section.id ? "border-emerald-500/60 bg-emerald-500/10" : section.is_visible ? "border-slate-600/40 bg-slate-800/50" : "border-slate-700/40 bg-slate-800/20 opacity-60"}`}>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="w-6 text-center text-xs font-black text-slate-400">{String(index + 1).padStart(2, "0")}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-bold text-white">{section.title || section.key}</span>
                      <span className="text-[11px] text-slate-400">{section.key} · {section.section_type || "section"}</span>
                    </span>
                    {statusChip(section)}
                  </div>
                  <div className="flex items-center gap-1.5 mt-2">
                    <button type="button" onClick={() => move(index, -1)} disabled={index === 0 || busy === "reorder"} aria-label={`Move ${section.title || section.key} up`} className="rounded-lg bg-slate-700/60 p-2 text-slate-200 hover:bg-slate-600 disabled:opacity-30"><FiArrowUp size={13} /></button>
                    <button type="button" onClick={() => move(index, 1)} disabled={index === sections.length - 1 || busy === "reorder"} aria-label={`Move ${section.title || section.key} down`} className="rounded-lg bg-slate-700/60 p-2 text-slate-200 hover:bg-slate-600 disabled:opacity-30"><FiArrowDown size={13} /></button>
                    <button type="button" onClick={() => toggleSection(section)} disabled={busy === `vis-${section.id}`} className="inline-flex items-center gap-1.5 rounded-lg bg-slate-700/60 px-2.5 py-2 text-[11px] font-bold text-slate-100 hover:bg-slate-600 disabled:opacity-50">
                      {section.is_visible ? <FiEyeOff size={13} /> : <FiEye size={13} />}
                      {section.is_visible ? "Hide" : "Show"}
                    </button>
                    <button type="button" onClick={() => { if (dirty && !window.confirm("You have unsaved changes in the editor. Discard them?")) return; setSelectedId(section.id) }} className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600/80 px-2.5 py-2 text-[11px] font-bold text-white hover:bg-emerald-500">
                      <FiEdit3 size={13} /> Edit
                    </button>
                    <button type="button" onClick={() => openHistory(section)} className="inline-flex items-center gap-1.5 rounded-lg bg-slate-700/60 px-2.5 py-2 text-[11px] font-bold text-slate-200 hover:bg-slate-600"><FiRotateCcw size={13} /> History</button>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* ── Right: editor ──────────────────────────────────── */}
          <div className="lg:col-span-3 space-y-4">
            {draft ? (
              <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-black uppercase tracking-wider text-slate-300">Editing: {draft.title || draft.key}</h3>
                  <div className="flex items-center gap-2">
                    {dirty && <span className="rounded-full bg-amber-500/20 px-2.5 py-1 text-[10px] font-black uppercase text-amber-300">Unsaved changes</span>}
                    {statusChip(draft)}
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <label className="block text-xs font-bold text-slate-300">Section label
                    <input className={`${field} mt-1`} value={draft.subtitle || ""} onChange={(e) => setDraft({ ...draft, subtitle: e.target.value })} placeholder="PLAN YOUR TRIP" />
                  </label>
                  <label className="block text-xs font-bold text-slate-300">Heading / title
                    <input className={`${field} mt-1`} value={draft.title || ""} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
                  </label>
                </div>
                <label className="block text-xs font-bold text-slate-300">Description
                  <textarea rows={3} className={`${field} mt-1`} value={draft.body || ""} onChange={(e) => setDraft({ ...draft, body: e.target.value })} />
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <label className="block text-xs font-bold text-slate-300">Button text
                    <input className={`${field} mt-1`} value={draft.cta_text || ""} onChange={(e) => setDraft({ ...draft, cta_text: e.target.value })} />
                  </label>
                  <label className="block text-xs font-bold text-slate-300">Button route
                    <input className={`${field} mt-1`} value={draft.cta_url || ""} onChange={(e) => setDraft({ ...draft, cta_url: e.target.value })} placeholder="/travel-planning" />
                  </label>
                  <label className="block text-xs font-bold text-slate-300">Layout
                    <select className={`${field} mt-1`} value={draft.layout_variant || "default"} onChange={(e) => setDraft({ ...draft, layout_variant: e.target.value })}>
                      {LAYOUT_VARIANTS.map((v) => <option key={v} value={v}>{v.replaceAll("_", " ")}</option>)}
                    </select>
                  </label>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
                  <label className="block text-xs font-bold text-slate-300">Image URL
                    <input className={`${field} mt-1`} value={draft.image_url || ""} onChange={(e) => setDraft({ ...draft, image_url: e.target.value })} placeholder="https://… or /media/…" />
                  </label>
                  <button type="button" onClick={openMediaPicker} className="inline-flex items-center gap-2 rounded-xl bg-slate-700/70 px-4 py-2.5 text-xs font-bold text-slate-100 hover:bg-slate-600"><FiImage size={14} /> Media Library</button>
                </div>
                <label className="flex items-center gap-2 text-xs font-bold text-slate-300">
                  <input type="checkbox" checked={draft.is_visible !== false} onChange={(e) => setDraft({ ...draft, is_visible: e.target.checked })} />
                  Visible on the homepage
                </label>

                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-700/50">
                  <button type="button" onClick={saveDraft} disabled={busy !== "" || !dirty} className="inline-flex items-center gap-2 rounded-xl bg-slate-700 px-4 py-2.5 text-xs font-black text-white hover:bg-slate-600 disabled:opacity-40">
                    <FiSave size={14} /> {busy === "save" ? "Saving…" : "Save Draft"}
                  </button>
                  <button type="button" onClick={() => setPreviewOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-sky-600/90 px-4 py-2.5 text-xs font-black text-white hover:bg-sky-500">
                    <FiEye size={14} /> Preview
                  </button>
                  <button type="button" onClick={saveAndPublish} disabled={busy !== ""} className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-black text-white hover:bg-emerald-500 disabled:opacity-50">
                    <FiSend size={14} /> {busy === "publish" ? "Publishing…" : "Save & Publish"}
                  </button>
                  <button type="button" onClick={publish} disabled={busy !== "" || !hasPendingChanges(selected || {})} className="inline-flex items-center gap-2 rounded-xl bg-emerald-800/80 px-4 py-2.5 text-xs font-black text-emerald-100 hover:bg-emerald-700 disabled:opacity-40">
                    Publish current draft
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-700/50">
                  <input type="datetime-local" value={scheduleAt} onChange={(e) => setScheduleAt(e.target.value)}
                    className="rounded-xl border border-slate-600/50 bg-slate-800/60 px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none" aria-label="Schedule publish time" />
                  <button type="button" onClick={schedulePublish} disabled={busy !== "" || !scheduleAt} className="inline-flex items-center gap-2 rounded-xl bg-slate-700 px-3 py-2 text-[11px] font-black text-slate-100 hover:bg-slate-600 disabled:opacity-40">
                    <FiClock size={13} /> Schedule publish
                  </button>
                  <button type="button" onClick={unpublish} disabled={busy !== "" || draft.status !== "published"} className="inline-flex items-center gap-2 rounded-xl bg-rose-700/70 px-3 py-2 text-[11px] font-black text-rose-100 hover:bg-rose-600 disabled:opacity-40">
                    <FiEyeOff size={13} /> Unpublish
                  </button>
                </div>
                <p className="text-[11px] text-slate-500">
                  Hero visuals are driven by the hero slides system; the hero section&apos;s text fields still feed CMS-rendered hero blocks.
                </p>
              </div>
            ) : (
              !loading && <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-10 text-center text-sm text-slate-400">Select a section to edit.</div>
            )}

            {selected && (
              <div className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5">
                <h3 className="text-sm font-black uppercase tracking-wider text-slate-300 mb-1">Cards / blocks inside “{selected.title || selected.key}”</h3>
                <p className="text-[11px] text-slate-500 mb-3">Blocks are part of the draft: after editing them, press Publish in the editor above to push them live.</p>
                <ContentBlocksBuilder key={selected.id} sectionId={selected.id} onToast={(msg, kind) => showToast(msg, kind)} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Preview modal: the SAME CMSBlock component the public site renders ── */}
      {previewOpen && draft && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
          <div className="flex max-h-[92vh] w-full max-w-6xl flex-col rounded-2xl bg-slate-950 border border-slate-700">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 p-4">
              <h3 className="text-sm font-black text-white">Preview — {draft.title || draft.key} <span className="text-slate-400 font-normal">(draft state, not yet public)</span></h3>
              <div className="flex items-center gap-2">
                {Object.keys(PREVIEW_WIDTHS).map((w) => (
                  <button key={w} type="button" onClick={() => setPreviewWidth(w)}
                    className={`rounded-lg px-3 py-1.5 text-[11px] font-black ${previewWidth === w ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}>{w}</button>
                ))}
                <button type="button" onClick={() => setPreviewOpen(false)} aria-label="Close preview" className="rounded-lg bg-slate-800 p-2 text-slate-300 hover:bg-slate-700"><FiX size={16} /></button>
              </div>
            </div>
            <div className="flex-1 overflow-auto bg-white p-4">
              <div className="mx-auto transition-all" style={{ maxWidth: PREVIEW_WIDTHS[previewWidth] }}>
                <CMSBlock section={draft} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── History / rollback ─────────────────────────────────── */}
      {historyFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-xl rounded-2xl bg-slate-950 border border-slate-700 p-5 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-black text-white">Revision history — {historyFor.title || historyFor.key}</h3>
              <button type="button" onClick={() => setHistoryFor(null)} aria-label="Close history" className="rounded-lg bg-slate-800 p-2 text-slate-300 hover:bg-slate-700"><FiX size={16} /></button>
            </div>
            {!revisions.length && <p className="text-sm text-slate-400">No revisions recorded yet.</p>}
            <ul className="space-y-2">
              {revisions.map((rev) => (
                <li key={rev.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-700/60 bg-slate-800/50 px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-white">#{rev.revision_number} · {rev.action}</p>
                    <p className="text-[11px] text-slate-400">{new Date(rev.created_at).toLocaleString()}{rev.created_by ? ` · ${rev.created_by}` : ""}</p>
                  </div>
                  <button type="button" onClick={() => rollback(rev)} disabled={busy === "rollback"} className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600/90 px-3 py-2 text-[11px] font-black text-white hover:bg-amber-500 disabled:opacity-50">
                    <FiRotateCcw size={13} /> Roll back to this
                  </button>
                </li>
              ))}
            </ul>
            <p className="text-[11px] text-slate-500 mt-3">Rollback restores the revision as a DRAFT — press Publish afterwards to make it public.</p>
          </div>
        </div>
      )}

      {/* ── Full-page draft preview: every visible section stacked in order ── */}
      {fullPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
          <div className="flex max-h-[92vh] w-full max-w-6xl flex-col rounded-2xl bg-slate-950 border border-slate-700">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 p-4">
              <h3 className="text-sm font-black text-white">Full homepage — draft state <span className="text-slate-400 font-normal">(specially-styled sections are approximated by the generic CMS renderer)</span></h3>
              <div className="flex items-center gap-2">
                {Object.keys(PREVIEW_WIDTHS).map((w) => (
                  <button key={w} type="button" onClick={() => setPreviewWidth(w)}
                    className={`rounded-lg px-3 py-1.5 text-[11px] font-black ${previewWidth === w ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"}`}>{w}</button>
                ))}
                <button type="button" onClick={() => setFullPreview(false)} aria-label="Close full preview" className="rounded-lg bg-slate-800 p-2 text-slate-300 hover:bg-slate-700"><FiX size={16} /></button>
              </div>
            </div>
            <div className="flex-1 overflow-auto bg-white p-4">
              <div className="mx-auto transition-all space-y-2" style={{ maxWidth: PREVIEW_WIDTHS[previewWidth] }}>
                {sections.filter((sct) => sct.is_visible).map((sct) => (
                  <CMSBlock key={sct.id} section={sct.id === draft?.id ? draft : sct} />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Media library picker ───────────────────────────────── */}
      {mediaPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-3xl rounded-2xl bg-slate-950 border border-slate-700 p-5 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between gap-3 mb-3">
              <h3 className="text-sm font-black text-white">Choose from Media Library</h3>
              <button type="button" onClick={() => setMediaPicker(false)} aria-label="Close media picker" className="rounded-lg bg-slate-800 p-2 text-slate-300 hover:bg-slate-700"><FiX size={16} /></button>
            </div>
            <div className="relative mb-3">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input autoFocus value={mediaQ} onChange={(e) => searchMedia(e.target.value)} placeholder="Search media…"
                className="w-full rounded-xl border border-slate-600/50 bg-slate-800/60 py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {mediaRows.map((row) => (
                <button key={row.id} type="button"
                  onClick={() => { setDraft((d) => (d ? { ...d, image_url: row.url || row.external_url || "" } : d)); setMediaPicker(false); showToast("Image selected — remember to Publish", "success") }}
                  className="group rounded-xl border border-slate-700/60 overflow-hidden text-left hover:border-emerald-500">
                  <img src={row.url} alt={row.caption || "Media"} loading="lazy" className="h-24 w-full object-cover" />
                  <span className="block truncate px-2 py-1.5 text-[10px] font-bold text-slate-300 group-hover:text-emerald-300">{row.caption || row.url}</span>
                </button>
              ))}
              {!mediaRows.length && <p className="col-span-4 py-6 text-center text-sm text-slate-400">No media found. Upload images in the Media Library panel first.</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
