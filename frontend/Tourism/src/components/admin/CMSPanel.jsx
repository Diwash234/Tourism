import { useEffect, useRef, useState, useMemo } from "react"
import { notifyCmsUpdated } from "../../hooks/usePublicConfig"
import { diffSnapshots, formatSnapshotValue } from "../../utils/revisionDiff"
import {
  FiActivity, FiClock, FiExternalLink, FiEye, FiFilePlus, FiRefreshCw,
  FiRotateCcw, FiSave, FiSend, FiX, FiCheckCircle, FiChevronDown, FiPlus,
  FiArrowUp, FiArrowDown, FiTrash2, FiEdit2
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"
import RichTextEditor from "./RichTextEditor"
import CMSBlock, { CMSExtras } from "../cms/CMSBlock"
import SafeHtml from "../cms/SafeHtml"
import BlockFieldsEditor, { blockIssues } from "./cms/BlockFieldsEditor"
import CmsSubSidebar from "./cms/CmsSubSidebar"
import CmsGlobalSectionEditor from "./cms/CmsGlobalSectionEditor"
import CmsContentCollectionEditor from "./cms/CmsContentCollectionEditor"
import CmsJournalsEditor from "./cms/CmsJournalsEditor"
import CmsDashboardOverview from "./cms/CmsDashboardOverview"
import ImageSearchImportPanel from "./cms/ImageSearchImportPanel"
import MediaLibraryPanel from "./MediaLibraryPanel"

const sectionTypes = ["text", "heading", "image", "gallery", "cards", "faq", "cta", "map", "video", "audio", "marquee", "animation", "media", "form", "table", "figure", "testimonials", "contact", "breadcrumbs", "search"]

const templates = {
  settings: { key: "", value: {}, description: "", is_public: true },
  pages: { route: "/", key: "new-page", title: "New page", meta_description: "", seo_title: "", og_image_url: "", search_visible: true, is_enabled: true, status: "draft" },
  sections: { page_id: null, key: "new-section", title: "New section", subtitle: "", body: "", image_url: "", cta_text: "", cta_url: "", icon: "", section_type: "text", layout_variant: "default", config: {}, display_order: 0, is_visible: true, is_reusable: false, status: "draft" },
  navigation: { location: "navbar", label: "New link", route: "/", icon: "", parent_id: null, allowed_roles: [], display_order: 0, is_active: true },
}

const clean = (row) => Object.fromEntries(Object.entries(row || {}).filter(([key]) => !["updated_at", "published_at", "scheduled_publish_at"].includes(key)))

export default function CMSPanel({ defaultResource = "pages" }) {
  const { showToast } = useToast()

  // Navigation state: "overview" | "page" | "global_section" | "content" | "journals"
  const [activeView, setActiveView] = useState(() => {
    if (defaultResource === "sections" || defaultResource === "global_content") return "global_section"
    if (defaultResource === "announcements") return "content"
    if (defaultResource === "publishing") return "overview"
    return "overview"
  })

  const [activeSubId, setActiveSubId] = useState(() => {
    if (defaultResource === "sections") return "navbar"
    if (defaultResource === "global_content") return "topbar"
    if (defaultResource === "announcements") return "notices"
    return "topbar"
  })

  const [pages, setPages] = useState([])
  const [sections, setSections] = useState([])
  const [selectedPage, setSelectedPage] = useState(null)
  const [selectedSection, setSelectedSection] = useState(null)
  const [contentCounts, setContentCounts] = useState({
    news: 12, blogs: 2, notices: 19, results: 5, events: 4, programs: 3,
    scholarships: 1, faqs: 4, applications: 1, enquiries: 0, feedback: 1,
    testimonials: 1, surveys: 1, survey_responses: 3, abstracts: 5, journals: 2, trash: 0,
  })

  // Editor states
  const [busy, setBusy] = useState(false)
  const [preview, setPreview] = useState(null)
  const [previewMode, setPreviewMode] = useState("desktop")
  const [previewKind, setPreviewKind] = useState("live")
  const [seoPreview, setSeoPreview] = useState(false)
  const [history, setHistory] = useState([])
  const [health, setHealth] = useState(null)
  const [builderTick, setBuilderTick] = useState(0)

  // Load all pages, sections, and content counts on mount
  const loadInitialData = async () => {
    try {
      const [pagesRes, sectionsRes, settingsRes] = await Promise.allSettled([
        adminApi.getCMS("pages"),
        adminApi.getCMS("sections"),
        adminApi.getCMS("settings"),
      ])

      if (pagesRes.status === "fulfilled") {
        const pageList = pagesRes.value.data?.results || []
        setPages(pageList)
        // Default to Home page
        const home = pageList.find(p => p.route === "/" || p.key === "home") || pageList[0]
        if (!selectedPage && home) setSelectedPage(home)
      }

      if (sectionsRes.status === "fulfilled") {
        const secList = sectionsRes.value.data?.results || []
        setSections(secList)
      }

      if (settingsRes.status === "fulfilled") {
        const settingsList = settingsRes.value.data?.results || []
        const counts = { ...contentCounts }
        settingsList.forEach(s => {
          if (Array.isArray(s.value)) {
            const shortKey = s.key.replace(/^cms_content_/, '')
            counts[shortKey] = s.value.length
          }
        })
        setContentCounts(counts)
      }
    } catch {
      // Graceful fallback
    }
  }

  useEffect(() => {
    loadInitialData()
  }, [])

  // Page sections for current selected page
  const currentPageSections = useMemo(() => {
    if (!selectedPage?.id) return []
    return sections
      .filter(s => s.page_id === selectedPage.id || s.page === selectedPage.id)
      .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
  }, [sections, selectedPage])

  const handleSelectView = (view, subId = null) => {
    setActiveView(view)
    if (subId) setActiveSubId(subId)
  }

  const handleSelectPage = (page) => {
    setSelectedPage(page)
    setActiveView("page")
    setSelectedSection(null)
  }

  const handleSelectSection = (section) => {
    setSelectedSection(section)
    setActiveView("page")
  }

  const handleContentCountChange = (type, count) => {
    setContentCounts(prev => ({ ...prev, [type]: count }))
  }

  // Save Page metadata draft
  const handleSavePageDraft = async () => {
    if (!selectedPage) return
    setBusy(true)
    try {
      const payload = {
        title: selectedPage.title,
        seo_title: selectedPage.seo_title || "",
        meta_description: selectedPage.meta_description || "",
        search_visible: selectedPage.search_visible !== false,
        resource: "pages",
        id: selectedPage.id,
      }
      await adminApi.updateCMS(payload)
      showToast("Page draft saved in database", "info")
      loadInitialData()
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not save page", "error")
    } finally {
      setBusy(false)
    }
  }

  // Publish Page live to website
  const handlePublishPageLive = async () => {
    if (!selectedPage?.id) return
    setBusy(true)
    try {
      // 1. Update fields
      await adminApi.updateCMS({
        title: selectedPage.title,
        seo_title: selectedPage.seo_title || "",
        meta_description: selectedPage.meta_description || "",
        search_visible: selectedPage.search_visible !== false,
        resource: "pages",
        id: selectedPage.id,
      })
      // 2. Run publish action
      await adminApi.runCMSAction({
        resource: "pages",
        id: selectedPage.id,
        action: "publish",
      })

      notifyCmsUpdated()
      showToast(`Published ${selectedPage.title} live to the website!`, "success")
      loadInitialData()
    } catch (err) {
      showToast(err.response?.data?.detail || "Publish failed", "error")
    } finally {
      setBusy(false)
    }
  }

  // Section ordering
  const handleMoveSection = async (section, dir) => {
    const list = [...currentPageSections]
    const idx = list.findIndex(s => s.id === section.id)
    const target = idx + dir
    if (idx < 0 || target < 0 || target >= list.length) return
    const ids = list.map(s => s.id)
    ;[ids[idx], ids[target]] = [ids[target], ids[idx]]

    setBusy(true)
    try {
      await adminApi.updateCMS({
        resource: "sections",
        action: "reorder",
        id: ids[0],
        section_ids: ids,
      })
      notifyCmsUpdated()
      showToast("Section order updated & published", "success")
      loadInitialData()
    } catch (err) {
      showToast(err.response?.data?.detail || "Reorder failed", "error")
    } finally {
      setBusy(false)
    }
  }

  // Toggle section visibility
  const handleToggleSectionVisibility = async (sec) => {
    setBusy(true)
    try {
      await adminApi.updateCMS({
        resource: "sections",
        id: sec.id,
        is_visible: !sec.is_visible,
      })
      notifyCmsUpdated()
      showToast(`Section ${sec.is_visible ? "hidden" : "visible"} on traveller site`, "info")
      loadInitialData()
    } catch (err) {
      showToast("Could not update visibility", "error")
    } finally {
      setBusy(false)
    }
  }

  // Create new section on this page
  const handleCreateNewSection = async () => {
    if (!selectedPage?.id) return
    setBusy(true)
    try {
      const key = `section-${Date.now().toString().slice(-4)}`
      const res = await adminApi.createCMS({
        resource: "sections",
        page_id: selectedPage.id,
        key: key,
        title: "New Section",
        subtitle: "",
        body: "<p>Write your section content here...</p>",
        section_type: "text",
        layout_variant: "default",
        display_order: currentPageSections.length * 10,
        is_visible: true,
      })
      showToast("New section created", "success")
      await loadInitialData()
      if (res.data?.id) {
        setSelectedSection(res.data.record || { id: res.data.id, title: "New Section", key })
      }
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not create section", "error")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="ny-cms-studio flex flex-col lg:flex-row gap-5 items-start text-slate-900 dark:text-slate-100 min-h-[85vh]">
      {/* Sub-Sidebar matching the reference images */}
      <CmsSubSidebar
        activeView={activeView}
        activeSubId={activeSubId}
        onSelectView={handleSelectView}
        pages={pages}
        sections={sections}
        contentCounts={contentCounts}
        onSelectPage={handleSelectPage}
        activePageId={selectedPage?.id}
        activeSectionId={selectedSection?.id}
        onSelectSection={handleSelectSection}
      />

<<<<<<< HEAD
        <section className="bg-white border border-emerald-200 rounded-2xl overflow-hidden h-fit max-h-[72vh]">
          <div className="p-3 border-b border-emerald-100 flex justify-between">
            <b>{RESOURCE_LABELS[resource]} <span className="ml-1 text-xs font-normal text-emerald-700">({rows.length})</span></b>
            <button onClick={() => load()} title="Refresh" aria-label="Refresh list"><FiRefreshCw /></button>
          </div>
          {resource === "sections" && (
            <div className="p-2 border-b border-emerald-100 bg-emerald-50">
              <label className="block text-[11px] font-bold text-slate-700">
                Page
                <select value={sectionPageId} onChange={(event) => setSectionPageId(event.target.value)} className="input-field mt-1">
                  <option value="">All pages</option>
                  {pageRows.map((page) => <option key={page.id} value={page.id}>{page.title || page.key} · {page.route}</option>)}
                </select>
              </label>
            </div>
          )}
          <div className="p-2 space-y-2 border-b border-emerald-100">
            <input
              value={listQuery}
              onChange={(event) => setListQuery(event.target.value)}
              placeholder={`Search ${resource}…`}
              aria-label={`Search ${resource}`}
              className="w-full rounded-lg border border-emerald-200 px-2.5 py-1.5 text-xs focus:border-emerald-600 focus:outline-none"
            />
            <div className="flex gap-1.5">
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} aria-label="Filter by status" className="flex-1 rounded-lg border border-emerald-200 px-1.5 py-1 text-[11px] capitalize">
                {statuses.map((value) => <option key={value} value={value}>{value === "all" ? "All statuses" : value}</option>)}
              </select>
              <select value={sortMode} onChange={(event) => setSortMode(event.target.value)} aria-label="Sort records" className="flex-1 rounded-lg border border-emerald-200 px-1.5 py-1 text-[11px]">
                <option value="default">Default order</option>
                <option value="name">Name A–Z</option>
                <option value="updated">Recently updated</option>
              </select>
            </div>
            {(listQuery || statusFilter !== "all") && (
              <p className="text-xs font-bold text-slate-500">Showing {visibleRows.length} of {rows.length}</p>
            )}
          </div>
          <div className="overflow-y-auto max-h-[58vh] p-2 space-y-1">
            {rows.length === 0 && <p className="p-6 text-center text-sm text-slate-500">No records found.</p>}
            {rows.length > 0 && visibleRows.length === 0 && <p className="p-6 text-center text-sm text-slate-500">No records match the filter.</p>}
            {visibleRows.map((row) => (
              <div key={row.id} className="flex items-stretch gap-1">
                <button onClick={() => choose(row)} className={`block flex-1 min-w-0 text-left p-3 rounded-xl text-xs ${selected?.id === row.id ? "bg-emerald-50 ring-1 ring-emerald-600" : "bg-slate-50 hover:bg-emerald-50"}`}>
                  <span className="font-bold text-slate-900">{displayName(row)}</span>
                  <span className="flex justify-between mt-1 text-xs text-slate-500">
                    <span>#{row.id}</span>
                    {row.status && <span className={row.status === "published" ? "text-emerald-700" : row.status === "scheduled" ? "text-sky-700" : "text-amber-700"}>{row.status}</span>}
                  </span>
                </button>
                {resource === "sections" && rows.length > 1 && (
                  <div className="flex flex-col justify-center gap-0.5">
                    <button
                      onClick={() => moveSection(row, -1)}
                      disabled={rows.findIndex((r) => r.id === row.id) === 0 || busy}
                      aria-label={`Move ${displayName(row)} up`}
                      title="Move up"
                      className="rounded-md border border-slate-200 bg-white px-1.5 py-0.5 text-xs font-bold text-slate-600 hover:bg-emerald-50 disabled:opacity-30"
                    >↑</button>
                    <button
                      onClick={() => moveSection(row, 1)}
                      disabled={rows.findIndex((r) => r.id === row.id) === rows.length - 1 || busy}
                      aria-label={`Move ${displayName(row)} down`}
                      title="Move down"
                      className="rounded-md border border-slate-200 bg-white px-1.5 py-0.5 text-xs font-bold text-slate-600 hover:bg-emerald-50 disabled:opacity-30"
                    >↓</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
=======
      {/* Main CMS Workspace Container */}
      <main className="flex-1 min-w-0 w-full space-y-5">
>>>>>>> origin/arena/01a0ed99-tourism

        {/* 1. OVERVIEW DASHBOARD */}
        {activeView === "overview" && (
          <CmsDashboardOverview
            totalPages={pages.length || 65}
            totalSections={sections.length || 150}
            contentCounts={contentCounts}
            onNavigate={(view, id) => {
              if (view === "page") {
                const target = pages.find(p => p.key === id || p.route === `/${id}`) || pages[0]
                if (target) handleSelectPage(target)
              } else {
                handleSelectView(view, id)
              }
            }}
          />
        )}

<<<<<<< HEAD
      {preview && (
        <div className="fixed inset-0 z-[80] bg-black/75 grid place-items-center p-4">
          <div className="flex h-[90vh] w-full max-w-7xl flex-col rounded-2xl bg-slate-100 p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <div className="mr-auto">
                <span className="text-xs uppercase font-black text-emerald-700">Preview as traveller</span>
                <h2 className="text-xl font-black text-slate-900">{preview.seo_title || displayName(preview)}</h2>
              </div>
              {[["live", "Live logged-out site"], ["draft", "Draft content"]].map(([id, label]) => (
                <button key={id} onClick={() => setPreviewKind(id)} className={`rounded-lg px-3 py-1 text-xs font-bold ${previewKind === id ? "bg-emerald-700 text-white" : "bg-white"}`}>{label}</button>
              ))}
              {[["desktop", "Desktop"], ["tablet", "Tablet"], ["mobile", "Mobile"]].map(([id, label]) => (
                <button key={id} onClick={() => setPreviewMode(id)} className={`rounded-lg px-2 py-1 text-xs font-bold ${previewMode === id ? "bg-slate-900 text-white" : "bg-white"}`}>{label}</button>
              ))}
              <button onClick={() => setPreview(null)}><FiX size={22} /></button>
            </div>
            <div className="flex min-h-0 flex-1 justify-center overflow-hidden">
              <div className={`overflow-hidden rounded-[1.5rem] border-8 border-slate-900 bg-white shadow-2xl max-w-full ${previewMode === "mobile" ? "h-full w-[390px]" : previewMode === "tablet" ? "h-full w-[768px]" : "h-full w-full"}`}>
                {previewKind === "live" && preview.route ? (
                  <iframe title="Logged-out traveller preview" src={travellerPreviewSrc()} className="h-full w-full bg-white" />
                ) : (
                  <div className="h-full overflow-y-auto p-6 text-slate-900">
                    <p className="text-xs text-slate-500">Draft CMS content. Live site uses the published traveller page. Search visibility: {preview.search_visible === false ? "hidden" : "allowed"}.</p>
                    {preview.meta_description && <p className="mt-2 text-slate-500">{preview.meta_description}</p>}
                    {preview.og_image_url && <img src={preview.og_image_url} alt="" className="mt-4 max-h-48 w-full rounded-xl object-cover" />}
                    {/* Rendered with the SAME component the public pages use
                        (CMSExtras -> CMSBlock), so the preview cannot drift
                        from what travellers actually see. */}
                    {preview.sections?.length > 0 && (
                      <div className="mt-4">
                        <CMSExtras sections={preview.sections} />
                      </div>
                    )}
                    {!preview.sections && <SafeHtml html={preview.body || ""} className="prose prose-sm mt-5" />}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {seoPreview && resource === "pages" && (
        <div className="fixed inset-0 z-[80] bg-black/75 flex justify-end">
          <aside className="bg-white border-l w-full max-w-lg p-5 overflow-y-auto">
            <div className="flex justify-between">
              <h3 className="text-xl font-black">SEO & social preview</h3>
              <button onClick={() => setSeoPreview(false)} aria-label="Close SEO preview"><FiX /></button>
            </div>
            <p className="text-xs text-slate-500 mt-1 mb-4">How this page is likely to appear. Uses the current draft values — nothing is published by previewing.</p>
            {(() => {
              let value = {}
              try { value = JSON.parse(json || "{}") } catch { /* invalid draft JSON — preview stays empty */ }
              const seoTitle = value.seo_title || value.title || ""
              const desc = value.meta_description || ""
              const route = value.route || "/"
              const og = value.og_image_url || ""
              return (
                <div className="space-y-6">
                  <div>
                    <p className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Google search result</p>
                    <div className="rounded-xl border border-slate-200 bg-white p-4">
                      <p className="text-xs text-emerald-800">nepalyatra.com{route}</p>
                      <p className="text-lg text-[#1a0dab] leading-snug">{seoTitle.length > 60 ? seoTitle.slice(0, 60) + "…" : seoTitle || "(no title)"}</p>
                      <p className="text-sm text-slate-600">{desc.length > 155 ? desc.slice(0, 155) + "…" : desc || "(no meta description — Google will invent one)"}</p>
                    </div>
                    <p className="mt-2 text-[11px] text-slate-500">
                      Title: {seoTitle.length}/60 chars {seoTitle.length > 60 ? "⚠ will be truncated" : "✓"} · Description: {desc.length}/155 {desc.length > 155 ? "⚠ will be truncated" : desc.length ? "✓" : "⚠ missing"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">Social share card</p>
                    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                      {og
                        ? <img src={og} alt="" className="aspect-[1.91/1] w-full object-cover" />
                        : <div className="aspect-[1.91/1] w-full bg-slate-100 flex items-center justify-center text-xs text-slate-400">No OG image set — shares will look plain</div>}
                      <div className="p-3">
                        <p className="text-xs uppercase text-slate-400">nepalyatra.com</p>
                        <p className="text-sm font-bold text-slate-900">{seoTitle || "(no title)"}</p>
                        <p className="text-xs text-slate-500 line-clamp-2">{desc || "(no description)"}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })()}
          </aside>
        </div>
      )}
=======
        {/* 2. GLOBAL SECTION EDITORS (Navbar, Topbar, Footer, CTA Banners, Action Buttons, Tickers, Chat Widget, Admission Modal) */}
        {activeView === "global_section" && (
          <CmsGlobalSectionEditor
            sectionId={activeSubId || "topbar"}
          />
        )}

        {/* 3. CONTENT COLLECTION EDITORS (News, Blogs, Notices, Results, Events, Programs, Scholarships, FAQs, Applications, Enquiries, Feedback, Testimonials, Surveys, Responses, Trash) */}
        {activeView === "content" && (
          <CmsContentCollectionEditor
            contentType={activeSubId || "news"}
            onCountChange={handleContentCountChange}
          />
        )}
>>>>>>> origin/arena/01a0ed99-tourism

        {/* 4. JOURNALS EDITORS (Abstracts, Journal Section) */}
        {activeView === "journals" && (
          <CmsJournalsEditor
            journalType={activeSubId || "abstracts"}
            onCountChange={handleContentCountChange}
          />
        )}

        {/* 5. MEDIA & IMAGE SEARCH IMPORT STUDIO */}
        {activeView === "media" && (
          <div>
            {activeSubId === "image_search_import" || !activeSubId ? (
              <ImageSearchImportPanel />
            ) : (
              <MediaLibraryPanel />
            )}
          </div>
        )}

        {/* 6. PAGE & SECTIONS WORKSPACE */}
        {activeView === "page" && selectedPage && (
          <div className="space-y-6">
            {/* Page Header Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-[#0E1E1B] p-5 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-black text-slate-900 dark:text-white">
                    {selectedPage.title || "Page Editor"}
                  </h2>
                  <span className="font-mono text-xs px-2.5 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                    {selectedPage.route}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      selectedPage.status === "published"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                    }`}
                  >
                    {selectedPage.status === "published" ? "● Published" : "Draft"}
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Manage sections, SEO, and visual blocks for this page. Changes published here reflect immediately on {selectedPage.route}.
                </p>
              </div>

<<<<<<< HEAD
function VisibilityFields({ value, set }) {
  const config = value.config || {}
  const vis = config.visibility || {}
  const setVis = (patch) => {
    const next = { ...vis, ...patch }
    // Drop empty keys so the stored config stays clean.
    Object.keys(next).forEach((k) => {
      const v = next[k]
      if (!v || (Array.isArray(v) && !v.length)) delete next[k]
    })
    const cleaned = { ...config }
    if (Object.keys(next).length) cleaned.visibility = next
    else delete cleaned.visibility
    set("config", cleaned)
  }
  const toggleIn = (list, item) => (list || []).includes(item) ? (list || []).filter((x) => x !== item) : [...(list || []), item]
  return (
    <details className="sm:col-span-2 rounded-xl border border-emerald-200 bg-white p-3">
      <summary className="cursor-pointer text-xs font-black text-emerald-800">
        Conditional visibility {vis.start_date || vis.end_date || vis.roles?.length || vis.devices?.length ? "(rules active)" : "(optional)"}
      </summary>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="text-xs font-semibold">Show from (date)
          <input type="date" className="input-field mt-1" value={vis.start_date || ""} onChange={(e) => setVis({ start_date: e.target.value })} />
        </label>
        <label className="text-xs font-semibold">Show until (date)
          <input type="date" className="input-field mt-1" value={vis.end_date || ""} onChange={(e) => setVis({ end_date: e.target.value })} />
        </label>
        <div className="text-xs font-semibold sm:col-span-2">
          Audience (empty = everyone)
          <div className="mt-1 flex flex-wrap gap-3">
            {["guest", "tourist", "staff", "admin"].map((role) => (
              <label key={role} className="flex items-center gap-1.5 font-normal capitalize">
                <input type="checkbox" checked={(vis.roles || []).includes(role)} onChange={() => setVis({ roles: toggleIn(vis.roles, role) })} />
                {role}
              </label>
            ))}
          </div>
        </div>
        <div className="text-xs font-semibold sm:col-span-2">
          Devices (empty = all)
          <div className="mt-1 flex flex-wrap gap-3">
            {["desktop", "tablet", "mobile"].map((device) => (
              <label key={device} className="flex items-center gap-1.5 font-normal capitalize">
                <input type="checkbox" checked={(vis.devices || []).includes(device)} onChange={() => setVis({ devices: toggleIn(vis.devices, device) })} />
                {device}
              </label>
            ))}
          </div>
        </div>
        <p className="text-xs text-slate-500 sm:col-span-2">
          Date + audience rules are enforced by the API (hidden content is never sent). Device rules hide the section in the browser.
        </p>
      </div>
    </details>
  )
}
=======
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setSeoPreview(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition"
                >
                  <FiEye size={13} />
                  <span>SEO Preview</span>
                </button>
>>>>>>> origin/arena/01a0ed99-tourism

                <a
                  href={selectedPage.route?.includes(":") ? selectedPage.route.split("/:")[0] : selectedPage.route || "/"}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition"
                >
                  <FiExternalLink size={13} />
                  <span>Live Site</span>
                </a>

                <button
                  type="button"
                  disabled={busy}
                  onClick={handleSavePageDraft}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition"
                >
                  <FiSave size={13} />
                  <span>Save Draft</span>
                </button>

                <button
                  type="button"
                  disabled={busy}
                  onClick={handlePublishPageLive}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/30 transition hover:scale-[1.02]"
                >
                  <FiSend size={13} />
                  <span>Publish Live to Website</span>
                </button>
              </div>
            </div>

            {/* Page Metadata Drawer */}
            <div className="bg-white dark:bg-[#0E1E1B] p-5 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm space-y-3.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Page Identity & Search Optimization
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Page Title *
                  </label>
                  <input
                    value={selectedPage.title || ""}
                    onChange={(e) => setSelectedPage({ ...selectedPage, title: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    SEO Meta Title
                  </label>
                  <input
                    value={selectedPage.seo_title || ""}
                    onChange={(e) => setSelectedPage({ ...selectedPage, seo_title: e.target.value })}
                    placeholder="Title for Google and social previews"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Meta Description
                  </label>
                  <textarea
                    rows={2}
                    value={selectedPage.meta_description || ""}
                    onChange={(e) => setSelectedPage({ ...selectedPage, meta_description: e.target.value })}
                    placeholder="Short description shown in search engine snippets..."
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-white resize-none"
                  />
                </div>
              </div>
            </div>

            {/* Page Sections List & Section Builder */}
            <div className="bg-white dark:bg-[#0E1E1B] p-5 rounded-2xl border border-slate-200 dark:border-emerald-900/50 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                    Page Content Sections ({currentPageSections.length})
                  </h3>
                  <p className="text-xs text-slate-500">
                    Reorder, edit, and attach structured content blocks to this page.
                  </p>
                </div>

                <button
                  type="button"
                  disabled={busy}
                  onClick={handleCreateNewSection}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm"
                >
                  <FiPlus size={13} />
                  <span>Add Section</span>
                </button>
              </div>

              {/* Sections List */}
              <div className="space-y-2">
                {currentPageSections.length === 0 ? (
                  <p className="text-xs text-slate-500 italic p-6 text-center border border-dashed rounded-xl border-slate-200 dark:border-slate-800">
                    This page currently renders standard components. Click "Add Section" to create a bespoke CMS section.
                  </p>
                ) : (
                  currentPageSections.map((sec, idx) => (
                    <div
                      key={sec.id}
                      className={`p-3.5 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                        selectedSection?.id === sec.id
                          ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30"
                          : "border-slate-200 dark:border-emerald-900/40 bg-slate-50/50 dark:bg-slate-900/50 hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-slate-400 font-bold">
                          #{idx + 1}
                        </span>
                        <div>
                          <span className="font-bold text-xs text-slate-900 dark:text-white block">
                            {sec.title || sec.key}
                          </span>
                          <span className="text-[11px] text-slate-500">
                            key: <span className="font-mono">{sec.key}</span> · type: {sec.section_type || "text"}
                          </span>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            sec.status === "published"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                          }`}
                        >
                          {sec.status === "published" ? "Live" : "Draft"}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 self-end sm:self-center">
                        <button
                          type="button"
                          onClick={() => handleMoveSection(sec, -1)}
                          disabled={idx === 0 || busy}
                          className="p-1 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 disabled:opacity-30"
                          title="Move up"
                        >
                          <FiArrowUp size={12} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleMoveSection(sec, 1)}
                          disabled={idx === currentPageSections.length - 1 || busy}
                          className="p-1 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 disabled:opacity-30"
                          title="Move down"
                        >
                          <FiArrowDown size={12} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleSectionVisibility(sec)}
                          className={`px-2 py-1 rounded text-[11px] font-semibold border ${
                            sec.is_visible
                              ? "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                              : "bg-rose-50 text-rose-700 border-rose-200"
                          }`}
                        >
                          {sec.is_visible ? "Visible" : "Hidden"}
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedSection(sec)}
                          className="px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs"
                        >
                          Edit Content
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Selected Section Editor & Block Builder */}
              {selectedSection && (
                <div className="mt-6 p-5 rounded-2xl bg-slate-900 text-white border border-slate-800 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <span className="font-bold text-sm text-amber-400">
                      Editing Section: {selectedSection.title || selectedSection.key}
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelectedSection(null)}
                      className="text-slate-400 hover:text-white"
                    >
                      <FiX size={16} />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <label className="block text-slate-400 mb-1">Section Title</label>
                      <input
                        value={selectedSection.title || ""}
                        onChange={(e) => setSelectedSection({ ...selectedSection, title: e.target.value })}
                        className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1">Subtitle</label>
                      <input
                        value={selectedSection.subtitle || ""}
                        onChange={(e) => setSelectedSection({ ...selectedSection, subtitle: e.target.value })}
                        className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-white"
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block text-slate-400 mb-1">Rich Text Body</label>
                      <RichTextEditor
                        value={selectedSection.body || ""}
                        onChange={(html) => setSelectedSection({ ...selectedSection, body: html })}
                      />
                    </div>
                  </div>

                  {/* Content Blocks Builder */}
                  <div className="pt-3 border-t border-slate-800">
                    <ContentBlocksBuilder
                      sectionId={selectedSection.id}
                      section={selectedSection}
                      onToast={showToast}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </main>
    </div>
  )
}

<<<<<<< HEAD
function CMSFriendlyEditor({ resource, json, setJson }) {
  let value = {}
  try { value = JSON.parse(json || "{}") } catch {
    return <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">Fix the syntax in Advanced before using the form.</p>
  }
  const set = (key, next) => setJson(JSON.stringify({ ...value, [key]: next }, null, 2))
  const field = (key, label, type = "text") => (
    <label key={key} className="text-xs font-semibold text-slate-700">
      {label}
      {type === "textarea"
        ? <textarea rows="4" className="input-field mt-1" value={value[key] ?? ""} onChange={e => set(key, e.target.value)} />
        : type === "checkbox"
          ? <input type="checkbox" className="ml-3" checked={Boolean(value[key])} onChange={e => set(key, e.target.checked)} />
          : <input type={type} className="input-field mt-1" value={value[key] ?? ""} onChange={e => set(key, type === "number" ? Number(e.target.value) : e.target.value)} />}
    </label>
  )
  if (resource === "pages") return (
    <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">
      {field("title", "Page title")}
      {field("seo_title", "SEO title")}
      {field("key", "Page key")}
      {field("route", "Page route")}
      {field("meta_description", "Search description", "textarea")}
      {field("og_image_url", "Social image URL")}
      <label className="text-xs font-semibold text-slate-700">Publication status
        <select className="input-field mt-1" value={value.status || "draft"} onChange={e => set("status", e.target.value)}>
          <option>draft</option><option>scheduled</option><option>published</option>
        </select>
      </label>
      {field("is_enabled", "Show this page", "checkbox")}
      {field("search_visible", "Allow search engines", "checkbox")}
      <SeoSuite value={value} />
    </div>
  )
  if (resource === "sections") return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">
        {field("page_id", "Parent page ID", "number")}
        {field("key", "Section key")}
        {field("title", "Section title")}
        {field("subtitle", "Subtitle")}
        <label className="sm:col-span-2 text-xs font-semibold text-slate-700">Body content
          <RichTextEditor value={value.body || ""} onChange={html => set("body", html)} />
        </label>
        {field("image_url", "Image URL")}
        <label className="text-xs font-semibold text-slate-700">Media URL (HTTPS or /)
          <input className="input-field mt-1" value={value.config?.media_url || ""} onChange={e => set("config", { ...(value.config || {}), media_url: e.target.value })} />
        </label>
        <label className="text-xs font-semibold text-slate-700">Background Theme / Style
          <select className="input-field mt-1" value={value.config?.background_style || "clean-white"} onChange={e => set("config", { ...(value.config || {}), background_style: e.target.value })}>
            <option value="clean-white">Clean White (Standard Card)</option>
            <option value="gradient-emerald">Gradient Emerald (Himalayan Forest)</option>
            <option value="dark-slate">Dark Slate (Modern Dark Theme)</option>
            <option value="saffron-warm">Saffron Gold (Warm Cultural Accent)</option>
            <option value="hero-dark">Hero Dark (Cinematic Hero Banner)</option>
            <option value="border-accent">Border Accent (Gold Border Highlighting)</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">Padding & Spacing
          <select className="input-field mt-1" value={value.config?.padding_style || "medium"} onChange={e => set("config", { ...(value.config || {}), padding_style: e.target.value })}>
            <option value="compact">Compact (p-4)</option>
            <option value="medium">Medium (p-6)</option>
            <option value="spacious">Spacious (p-10)</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">Text Size
          <select className="input-field mt-1" value={value.config?.text_scale || "base"} onChange={e => set("config", { ...(value.config || {}), text_scale: e.target.value })}>
            <option value="sm">Small</option>
            <option value="base">Normal</option>
            <option value="lg">Large</option>
            <option value="xl">Extra large</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">Alignment
          <select className="input-field mt-1" value={value.config?.align || "left"} onChange={e => set("config", { ...(value.config || {}), align: e.target.value })}>
            <option value="left">Left</option>
            <option value="center">Center</option>
            <option value="right">Right</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">Background Image (HTTPS, optional)
          <input className="input-field mt-1" value={value.config?.bg_image || ""} onChange={e => set("config", { ...(value.config || {}), bg_image: e.target.value })} placeholder="https://…" />
        </label>
        <label className="text-xs font-semibold text-slate-700">Animation
          <select className="input-field mt-1" value={value.config?.effect || "none"} onChange={e => set("config", { ...(value.config || {}), effect: e.target.value })}>
            {["none", "marquee", "fade", "slide"].map(item => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">Placement
          <select className="input-field mt-1" value={value.config?.placement || "main"} onChange={e => set("config", { ...(value.config || {}), placement: e.target.value })}>
            {["main", "hero", "sidebar", "footer"].map(item => <option key={item}>{item}</option>)}
          </select>
        </label>
        {field("cta_text", "Button text")}
        {field("cta_url", "Button route")}
        {field("icon", "Icon")}
        <SectionConfigFields value={value} set={set} />
        <VisibilityFields value={value} set={set} />
        <label className="text-xs font-semibold text-slate-700">Section type
          <select className="input-field mt-1" value={value.section_type || "text"} onChange={e => set("section_type", e.target.value)}>
            {sectionTypes.map(type => <option key={type}>{type}</option>)}
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">Layout Variant
          <select className="input-field mt-1" value={value.layout_variant || "default"} onChange={e => set("layout_variant", e.target.value)}>
            {["default", "compact", "wide", "cards", "hero", "split"].map(item => <option key={item}>{item}</option>)}
          </select>
        </label>
        {field("display_order", "Display order", "number")}
        {field("is_visible", "Visible on user page", "checkbox")}
        {field("is_reusable", "Reusable section", "checkbox")}
      </div>

      {/* Live Visual Section Preview */}
      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
        <span className="text-xs font-black uppercase text-amber-400">Live Visual Section Preview</span>
        <div className="p-2">
          <CMSBlock section={value} />
        </div>
      </div>
    </div>
  )
  if (resource === "navigation") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2"><label className="text-xs font-semibold text-slate-700">Location<select className="input-field mt-1" value={value.location || "navbar"} onChange={e => set("location", e.target.value)}><option>navbar</option><option>sidebar</option><option>footer</option></select></label>{field("label", "Visible label")}{field("route", "Internal route")}{field("parent_id", "Parent item ID")}{field("icon", "Icon")}{field("display_order", "Display order", "number")}<label className="text-xs font-semibold text-slate-700">Allowed roles (comma separated)<input className="input-field mt-1" value={(value.allowed_roles || []).join(", ")} onChange={e => set("allowed_roles", e.target.value.split(",").map(x => x.trim()).filter(Boolean))} /></label>{field("is_active", "Active", "checkbox")}</div>
  if (resource === "translations") return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("target_resource", "Target type")}{field("object_id", "Target record ID", "number")}{field("language_code", "Language code")}<label className="text-xs font-semibold text-slate-700">Translated fields<textarea rows="5" className="input-field mt-1 font-mono" value={JSON.stringify(value.content || {}, null, 2)} onChange={e => { try { set("content", JSON.parse(e.target.value)) } catch { /* keep until valid */ } }} /></label></div>
  return <div className="grid gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:grid-cols-2">{field("key", "Setting key")}{field("description", "Description")}{field("is_public", "Public setting", "checkbox")}<label className="text-xs font-semibold text-slate-700">Structured value<textarea rows="6" className="input-field mt-1 font-mono" value={JSON.stringify(value.value || {}, null, 2)} onChange={e => { try { set("value", JSON.parse(e.target.value)) } catch { /* keep until valid */ } }} /></label></div>
}

// Exact preview: the parent section rendered by the same CMSBlock component the
// public pages use, with the unsaved block swapped in, on the public page
// surface (light theme, real container width or a 390 px phone frame).
function BlockExactPreview({ section, blocks, editingBlock }) {
  const [device, setDevice] = useState("desktop")
  const merged = blocks
    .map((b) => (b.id === editingBlock.id ? editingBlock : b))
    .filter((b) => b.is_visible !== false)
  const previewSection = { ...(section || {}), blocks: merged }
  return (
    <div className="space-y-2 rounded-xl border border-slate-700 p-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-black uppercase text-amber-400">Exact preview (unsaved changes, as travellers will see it)</span>
        <span className="flex gap-1" role="group" aria-label="Preview width">
          {["desktop", "mobile"].map((d) => (
            <button key={d} type="button" aria-pressed={device === d} onClick={() => setDevice(d)}
              className={`rounded px-2 py-0.5 text-[11px] font-bold ${device === d ? "bg-amber-400 text-slate-950" : "bg-slate-800 text-slate-300"}`}>{d}</button>
          ))}
        </span>
      </div>
      {editingBlock.is_visible === false && <p className="text-[11px] text-amber-300">This block is hidden, so it is not shown in the preview.</p>}
      <div className="overflow-x-auto rounded-lg bg-[var(--ny-bg,#f8fafc)] p-3 text-slate-900">
        <div className="mx-auto" style={{ maxWidth: device === "mobile" ? 390 : 1152 }}>
          <CMSBlock section={previewSection} preview />
        </div>
      </div>
    </div>
  )
}
=======
// ----------------------------------------------------------------------------
// Re-usable ContentBlocksBuilder (preserved for HomepageManagerPanel compatibility)
// ----------------------------------------------------------------------------
>>>>>>> origin/arena/01a0ed99-tourism

export function ContentBlocksBuilder({ sectionId, section = null, onToast }) {
  const [blocks, setBlocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingBlock, setEditingBlock] = useState(null)
  const [showTypePicker, setShowTypePicker] = useState(false)

  const BLOCK_TYPES = [
    { type: "heading", label: "Heading", icon: "📌", desc: "H1, H2, H3 title heading" },
    { type: "subheading", label: "Subheading", icon: "✍️", desc: "Section subheading / tagline" },
    { type: "rich_text", label: "Rich Text", icon: "📝", desc: "Formatted rich HTML text" },
    { type: "image", label: "Image", icon: "🖼️", desc: "Single photo with caption & link" },
    { type: "gallery", label: "Image Gallery", icon: "🎨", desc: "Grid of multiple photography cards" },
    { type: "button", label: "Action Button", icon: "🔘", desc: "Call to action link button" },
    { type: "table", label: "Data Table", icon: "📊", desc: "Custom table with rows & columns" },
    { type: "video", label: "Video / Embed", icon: "🎥", desc: "YouTube / Vimeo embed" },
    { type: "map", label: "Interactive Map", icon: "🗺️", desc: "Coordinates & map pin" },
    { type: "destination_grid", label: "Destination Grid", icon: "🏔️", desc: "Live tourism destination cards" },
    { type: "hotel_grid", label: "Hotel Grid", icon: "🏨", desc: "Recommended hotels & lodges" },
    { type: "restaurant_grid", label: "Restaurant Grid", icon: "🍽️", desc: "Culinary & food spots" },
    { type: "statistics", label: "Statistics", icon: "📈", desc: "Key facts & metric numbers" },
    { type: "list", label: "List", icon: "📑", desc: "Bullet or numbered list items" },
    { type: "quote", label: "Quote", icon: "💬", desc: "Blockquote & citation" },
    { type: "alert", label: "Alert / Callout", icon: "⚠️", desc: "Notice, info or warning box" },
    { type: "divider", label: "Divider", icon: "➖", desc: "Horizontal section divider" },
    { type: "html", label: "Custom Safe HTML", icon: "💻", desc: "Sanitized HTML content" },
    { type: "card_grid", label: "Card Grid", icon: "🗂️", desc: "Tool/feature cards with emoji, text & internal link" },
    { type: "packages", label: "Travel Packages Grid", icon: "🎒", desc: "Live marketplace package cards" },
  ]

  const loadBlocks = async () => {
    if (!sectionId) return
    setLoading(true)
    try {
      const res = await adminApi.getSectionBlocks(sectionId)
      setBlocks(res.data?.results || [])
    } catch {
      setBlocks([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBlocks()
  }, [sectionId])

  const addBlock = async (type) => {
    setShowTypePicker(false)
    const defaults = {
      heading: { text: "Heading Title", level: "h2", align: "left" },
      subheading: { text: "Section Subheading", align: "left" },
      rich_text: { content: "<p>Write your formatted paragraph here...</p>" },
      image: { url: "", alt: "", caption: "", aspect_ratio: "16:9", rounded: true },
      gallery: { images: [], columns: 3 },
      button: { label: "Explore More", url: "/destinations", variant: "primary", size: "md" },
      destination_grid: { limit: 4, category: null, filter: "featured" },
      hotel_grid: { limit: 3, filter: "verified" },
      restaurant_grid: { limit: 3, filter: "verified" },
      statistics: { items: [{ number: "100+", label: "Verified Places" }] },
      list: { items: ["Item 1", "Item 2"], style: "bullet" },
      quote: { quote: "Nepal is not just a destination, it is an emotion.", author: "Anonymous", role: "Traveller" },
      alert: { type: "info", message: "Travel notice message goes here." },
      divider: { style: "solid" },
      table: { headers: ["Column 1", "Column 2"], rows: [["A1", "B1"]] },
      video: { url: "", caption: "", autoplay: false },
      map: { latitude: 27.7172, longitude: 85.3240, zoom: 12 },
      html: { html: "<p>Custom safe markup</p>" },
      card_grid: { items: [{ emoji: "🏔️", title: "Annapurna", body: "Explore high trails", url: "/destinations" }] },
      packages: { filter: "featured", limit: 3 },
    }

    try {
      const res = await adminApi.createContentBlock(sectionId, {
        block_type: type,
        title: "",
        data: defaults[type] || {},
        position: blocks.length * 10,
        is_visible: true,
      })
      if (onToast) onToast("Block added", "success")
      loadBlocks()
      if (res.data?.id) setEditingBlock(res.data)
    } catch {
      if (onToast) onToast("Could not add block", "error")
    }
  }

  const deleteBlock = async (id) => {
    if (!window.confirm("Delete this block?")) return
    try {
      await adminApi.deleteContentBlock(id)
      if (onToast) onToast("Block deleted", "success")
      loadBlocks()
    } catch {
      if (onToast) onToast("Delete failed", "error")
    }
  }

  const saveEditingBlock = async () => {
    if (!editingBlock) return
    try {
      await adminApi.updateContentBlock(editingBlock.id, {
        data: editingBlock.data,
        is_visible: editingBlock.is_visible,
        title: editingBlock.title,
      })
      if (onToast) onToast("Block updated", "success")
      setEditingBlock(null)
      loadBlocks()
    } catch {
      if (onToast) onToast("Save failed", "error")
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
          Visual Content Blocks ({blocks.length})
        </span>
        <button
          type="button"
          onClick={() => setShowTypePicker(!showTypePicker)}
          className="rounded-lg bg-amber-400 text-slate-950 px-3 py-1 text-xs font-black shadow hover:bg-amber-300"
        >
          + Add Visual Block
        </button>
      </div>

      {showTypePicker && (
<<<<<<< HEAD
        <div className="p-3 rounded-2xl bg-slate-900 border border-slate-700 space-y-2">
          <p className="text-xs font-bold text-amber-300">Choose a Content Block Type to insert:</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {BLOCK_TYPES.map((bt) => (
              <button
                key={bt.type}
                type="button"
                onClick={() => addBlock(bt.type)}
                className="p-2.5 rounded-xl bg-slate-800 hover:bg-emerald-900 border border-slate-700 text-left transition space-y-1 group"
              >
                <div className="flex items-center gap-1.5">
                  <span>{bt.icon}</span>
                  <span className="font-extrabold text-xs text-white group-hover:text-amber-300">{bt.label}</span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2">{bt.desc}</p>
              </button>
            ))}
          </div>
=======
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 rounded-xl bg-slate-800 border border-slate-700">
          {BLOCK_TYPES.map(bt => (
            <button
              key={bt.type}
              type="button"
              onClick={() => addBlock(bt.type)}
              className="p-2 rounded-lg bg-slate-900 hover:bg-slate-700 text-left text-xs transition"
            >
              <span className="mr-1.5">{bt.icon}</span>
              <span className="font-bold text-white">{bt.label}</span>
            </button>
          ))}
>>>>>>> origin/arena/01a0ed99-tourism
        </div>
      )}

      {loading ? (
        <p className="text-xs text-slate-400">Loading blocks…</p>
      ) : blocks.length === 0 ? (
        <p className="text-xs text-slate-500 italic p-3 text-center border border-dashed border-slate-700 rounded-lg">
          No blocks inside this section yet. Add cards, galleries, or text blocks above.
        </p>
      ) : (
        <div className="space-y-2">
<<<<<<< HEAD
          {blocks.map((b, idx) => (
            <div key={b.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-300 text-xs font-black uppercase">
                    {b.block_type}
                  </span>
                  <span className="font-bold text-white truncate max-w-xs">{b.title || b.data?.text || b.data?.label || `Block #${b.id}`}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button type="button" onClick={() => moveBlock(idx, -1)} disabled={idx === 0} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30">↑</button>
                  <button type="button" onClick={() => moveBlock(idx, 1)} disabled={idx === blocks.length - 1} className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30">↓</button>
                  <button type="button" onClick={() => setEditingBlock(editingBlock?.id === b.id ? null : { ...b })} className="px-2.5 py-1 rounded bg-amber-400 text-slate-950 font-bold hover:bg-amber-300">
                    {editingBlock?.id === b.id ? "Close" : "Edit"}
                  </button>
                  <button type="button" onClick={() => removeBlock(b.id)} className="px-2 py-1 rounded bg-rose-950 text-rose-300 hover:bg-rose-900 font-bold">Delete</button>
                </div>
=======
          {blocks.map((b, i) => (
            <div key={b.id} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800 border border-slate-700 text-xs">
              <span className="font-bold text-slate-200">
                #{i + 1} {b.block_type.replace('_', ' ').toUpperCase()}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setEditingBlock(b)}
                  className="rounded bg-slate-700 hover:bg-slate-600 px-2.5 py-1 text-[11px] font-bold text-white"
                >
                  Edit Block
                </button>
                <button
                  type="button"
                  onClick={() => deleteBlock(b.id)}
                  className="text-rose-400 hover:text-rose-200 p-1"
                >
                  <FiTrash2 size={13} />
                </button>
>>>>>>> origin/arena/01a0ed99-tourism
              </div>
            </div>
          ))}
        </div>
      )}

      {editingBlock && (
        <div className="p-4 rounded-xl bg-slate-800 border border-amber-400/40 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-amber-300">
              Edit Block #{editingBlock.id} ({editingBlock.block_type})
            </span>
            <button type="button" onClick={() => setEditingBlock(null)} className="text-slate-400">
              <FiX size={15} />
            </button>
          </div>

          <BlockFieldsEditor
            block={editingBlock}
            onChange={(nextData) => setEditingBlock({ ...editingBlock, data: nextData })}
          />

<<<<<<< HEAD
  useEffect(() => {
    // Deferred one tick so the loader's synchronous setLoading(true) runs
    // outside the effect flush (react-hooks/set-state-in-effect).
    const t = setTimeout(() => loadSections(), 0)
    return () => clearTimeout(t)
  }, [pageId, refreshKey])

  const persist = async (next) => {
    setSections(next)
    try {
      await adminApi.runCMSAction({ resource: "pages", id: pageId, action: "reorder", section_ids: next.map(section => section.id) })
    } catch (error) {
      onToast(error.response?.data?.detail || "Could not save section order", "error")
      loadSections()
    }
  }

  const move = (index, direction) => {
    const target = index + direction
    if (target < 0 || target >= sections.length) return
    const next = sections.slice()
    const [item] = next.splice(index, 1)
    next.splice(target, 0, item)
    persist(next)
  }

  const onDrop = (index) => {
    const from = dragFrom.current
    dragFrom.current = null
    if (from == null || from === index) return
    const next = sections.slice()
    const [item] = next.splice(from, 1)
    next.splice(index, 0, item)
    persist(next)
  }

  const saveSection = async () => {
    if (!draft?.id) return
    try {
      await adminApi.updateCMS({
        resource: "sections",
        id: draft.id,
        ...draft,
        status: "published",
        is_visible: Boolean(draft.is_visible),
      })
      notifyCmsUpdated()
      onToast("Section saved & published live!", "success")
      setOpenId(null)
      setDraft(null)
      loadSections()
    } catch (error) {
      onToast(error.response?.data?.detail || "Could not save section", "error")
    }
  }

  const addSection = async () => {
    try {
      await adminApi.createCMS({
        resource: "sections", page_id: pageId, key: `block-${Date.now()}`,
        title: "New section", body: "Edit this block.", section_type: "text",
        display_order: (sections[sections.length - 1]?.display_order || 0) + 10,
        is_visible: true, status: "published",
      })
      onToast("Section added", "success")
      loadSections()
    } catch (error) {
      onToast(error.response?.data?.detail || "Could not add section", "error")
    }
  }

  return (
    <div className="rounded-xl border border-emerald-200 bg-white p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-black text-emerald-800">All sections on this page ({sections.length})</p>
        <div className="flex gap-2">
          <button type="button" onClick={addSection} className="rounded-lg bg-emerald-700 px-3 py-1 text-xs font-bold text-white">Add section</button>
          <p className="self-center text-xs text-slate-500">Edit, preview, drag or use arrows.</p>
        </div>
      </div>
      {!sections.length && (
        <div className="rounded-xl border border-dashed border-emerald-200 bg-emerald-50/40 p-8 text-center">
          <p className="text-sm font-bold text-slate-800">No content sections yet</p>
          <p className="text-xs text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
            Start from a template for a full page layout, drop in a reusable block, or add a single section.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            <button type="button" onClick={addSection} className="rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-bold text-white">Add section</button>
          </div>
        </div>
      )}
      <div className="space-y-2">
        {sections.map((section, index) => (
          <div key={section.id} className="rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-xs">
            <div
              draggable
              onDragStart={() => { dragFrom.current = index }}
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => onDrop(index)}
              className="flex cursor-grab items-center gap-3"
            >
              <span className="font-black text-emerald-800">{index + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-bold">{section.title || section.key}</p>
                <p className="text-xs uppercase tracking-widest text-slate-500">{section.key} · {section.section_type || "text"} · {section.status}{section.is_visible === false ? " · hidden" : ""}</p>
              </div>
              <button type="button" onClick={() => setPreviewId(previewId === section.id ? null : section.id)} className="rounded bg-white px-2 py-1 font-bold">Preview</button>
              <button type="button" onClick={() => { setOpenId(openId === section.id ? null : section.id); setDraft({ ...section }) }} className="rounded bg-white px-2 py-1 font-bold">Edit</button>
              <button type="button" onClick={() => move(index, -1)} className="rounded bg-white px-2 py-1 font-bold" aria-label="Move up">↑</button>
              <button type="button" onClick={() => move(index, 1)} className="rounded bg-white px-2 py-1 font-bold" aria-label="Move down">↓</button>
            </div>
            {previewId === section.id && (
              <article className="mt-3 rounded-lg bg-white p-3">
                <h4 className="text-base font-black">{section.title}</h4>
                <p className="text-slate-500">{section.subtitle}</p>
                {section.image_url && <img src={section.image_url} alt="" className="mt-2 max-h-40 w-full rounded-lg object-cover" />}
                <SafeHtml html={section.body || ""} className="prose prose-sm mt-2" />
              </article>
            )}
            {openId === section.id && draft && (
              <div className="mt-3 grid gap-2 rounded-lg bg-slate-900 text-white p-3 sm:grid-cols-2">
                <label className="font-semibold text-slate-300">Title<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.title || ""} onChange={(e) => setDraft({ ...draft, title: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Key<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.key || ""} onChange={(e) => setDraft({ ...draft, key: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Subtitle<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.subtitle || ""} onChange={(e) => setDraft({ ...draft, subtitle: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Image / media URL<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.image_url || ""} onChange={(e) => setDraft({ ...draft, image_url: e.target.value })} /></label>
                <label className="font-semibold text-slate-300">Button Text (CTA)<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.cta_text || ""} onChange={(e) => setDraft({ ...draft, cta_text: e.target.value })} placeholder="e.g. Explore Now" /></label>
                <label className="font-semibold text-slate-300">Button Link Route<input className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.cta_url || ""} onChange={(e) => setDraft({ ...draft, cta_url: e.target.value })} placeholder="/destinations" /></label>
                <label className="font-semibold text-slate-300">Background Theme / Style
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.background_style || "clean-white"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), background_style: e.target.value } })}>
                    <option value="clean-white">Clean White (Standard Card)</option>
                    <option value="gradient-emerald">Gradient Emerald (Himalayan Forest)</option>
                    <option value="dark-slate">Dark Slate (Modern Dark Theme)</option>
                    <option value="saffron-warm">Saffron Gold (Warm Cultural Accent)</option>
                    <option value="hero-dark">Hero Dark (Cinematic Hero Banner)</option>
                    <option value="border-accent">Border Accent (Gold Border Highlighting)</option>
                  </select>
                </label>
                <label className="font-semibold text-slate-300">Padding & Spacing
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.padding_style || "medium"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), padding_style: e.target.value } })}>
                    <option value="compact">Compact (p-4)</option>
                    <option value="medium">Medium (p-6)</option>
                    <option value="spacious">Spacious (p-10)</option>
                  </select>
                </label>
                <label className="font-semibold text-slate-300">Section type
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.section_type || "text"} onChange={(e) => setDraft({ ...draft, section_type: e.target.value })}>
                    {sectionTypes.map((type) => <option key={type}>{type}</option>)}
                  </select>
                </label>
                <label className="font-semibold text-slate-300">Layout Variant
                  <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.layout_variant || "default"} onChange={(e) => setDraft({ ...draft, layout_variant: e.target.value })}>
                    {["default", "compact", "wide", "cards", "hero", "split"].map((item) => <option key={item}>{item}</option>)}
                  </select>
                </label>
                <div className="sm:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                  <label className="font-semibold text-slate-300">Content width
                    <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.max_width || "container"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), max_width: e.target.value } })}>
                      <option value="narrow">Narrow</option><option value="container">Container</option><option value="wide">Wide</option><option value="full">Full width</option>
                    </select>
                  </label>
                  <label className="font-semibold text-slate-300">Horizontal alignment
                    <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.align || "left"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), align: e.target.value } })}>
                      <option value="left">Left</option><option value="center">Center</option><option value="right">Right</option>
                    </select>
                  </label>
                  <label className="font-semibold text-slate-300">Row gap
                    <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.row_gap || "normal"} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), row_gap: e.target.value } })}>
                      <option value="compact">Compact</option><option value="normal">Normal</option><option value="large">Large</option>
                    </select>
                  </label>
                  <label className="font-semibold text-slate-300">Mobile columns
                    <select className="input-field mt-1 text-slate-100 bg-slate-800 border-slate-700" value={draft.config?.mobile_columns || 1} onChange={(e) => setDraft({ ...draft, config: { ...(draft.config || {}), mobile_columns: Number(e.target.value) } })}>
                      <option value={1}>1</option><option value={2}>2</option>
                    </select>
                  </label>
                </div>
                <label className="sm:col-span-2 font-semibold text-slate-300">Body Content
                  <RichTextEditor value={draft.body || ""} onChange={(html) => setDraft({ ...draft, body: html })} />
                </label>
                <div className="sm:col-span-2 mt-2">
                  <ContentBlocksBuilder sectionId={draft.id} section={draft} onToast={onToast} />
                </div>
                <label className="flex items-center gap-2 font-semibold text-slate-300"><input type="checkbox" checked={Boolean(draft.is_visible)} onChange={(e) => setDraft({ ...draft, is_visible: e.target.checked })} /> Visible on traveller page</label>
                <div className="flex gap-2 self-end">
                  <button type="button" onClick={saveSection} className="rounded-lg bg-amber-400 text-slate-950 font-black px-4 py-2 text-xs shadow">Save & Publish Section</button>
                  <button type="button" onClick={() => { setOpenId(null); setDraft(null) }} className="rounded-lg bg-slate-800 text-slate-300 px-3 py-2 text-xs font-bold">Cancel</button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
=======
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={saveEditingBlock}
              className="rounded-lg bg-amber-400 text-slate-950 font-black px-4 py-1.5 text-xs shadow"
            >
              Save Block
            </button>
          </div>
        </div>
      )}
>>>>>>> origin/arena/01a0ed99-tourism
    </div>
  )
}
