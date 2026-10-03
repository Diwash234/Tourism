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

      {/* Main CMS Workspace Container */}
      <main className="flex-1 min-w-0 w-full space-y-5">

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

              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setSeoPreview(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition"
                >
                  <FiEye size={13} />
                  <span>SEO Preview</span>
                </button>

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

// ----------------------------------------------------------------------------
// Re-usable ContentBlocksBuilder (preserved for HomepageManagerPanel compatibility)
// ----------------------------------------------------------------------------

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
    </div>
  )
}
