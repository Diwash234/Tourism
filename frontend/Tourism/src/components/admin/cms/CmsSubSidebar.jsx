import { useState, useMemo } from "react"
import {
  BsSpeedometer2, BsHouseDoor, BsInfoCircle, BsDoorOpen, BsGrid1X2,
  BsNewspaper, BsExclamationCircle, BsBarChart, BsCalendarEvent,
  BsImage, BsDownload, BsPen, BsLayoutTextWindow, BsBorderTop,
  BsLayoutThreeColumns, BsMegaphone, BsShieldCheck, BsActivity,
  BsChatDots, BsWindow, BsAward, BsQuestionCircle, BsFileText,
  BsEnvelope, BsHeart, BsChatQuote, BsCardChecklist, BsListCheck,
  BsTrash, BsFileEarmarkText, BsJournalBookmark, BsSearch,
  BsChevronDown, BsChevronRight, BsFolder2Open, BsLayers
} from "react-icons/bs"

export const CMS_CORE_FEATURED_PAGES = [
  { key: "home", route: "/", title: "Home", icon: BsHouseDoor, hasChildren: true },
  { key: "about", route: "/about", title: "About", icon: BsInfoCircle, hasChildren: true },
  { key: "packages", route: "/packages", title: "Admission", icon: BsDoorOpen, hasChildren: false },
  { key: "how-it-works", route: "/how-it-works", title: "Programs", icon: BsGrid1X2, hasChildren: true },
  { key: "discover-nepal", route: "/discover-nepal", title: "News", icon: BsNewspaper, hasChildren: true },
  { key: "risk-alerts", route: "/risk-alerts", title: "Notices", icon: BsExclamationCircle, hasChildren: false },
  { key: "recommendation", route: "/recommendation", title: "Results", icon: BsBarChart, hasChildren: false },
  { key: "districts", route: "/districts", title: "Events", icon: BsCalendarEvent, hasChildren: false },
  { key: "gallery", route: "/gallery", title: "Gallery", icon: BsImage, hasChildren: false },
  { key: "before-you-travel", route: "/before-you-travel", title: "Downloads", icon: BsDownload, hasChildren: false },
  { key: "travel", route: "/travel", title: "Blogs", icon: BsPen, hasChildren: true },
]

export const CMS_GLOBAL_SECTIONS = [
  { id: "navbar", label: "Navbar", icon: BsLayoutTextWindow },
  { id: "topbar", label: "Topbar", icon: BsBorderTop },
  { id: "footer", label: "Footer", icon: BsLayoutThreeColumns },
  { id: "cta_banners", label: "CTA Banners", icon: BsMegaphone },
  { id: "action_buttons", label: "Apply Now Buttons", icon: BsShieldCheck },
  { id: "tickers", label: "Tickers", icon: BsActivity },
  { id: "chat_widget", label: "Chat Widget", icon: BsChatDots },
  { id: "admission_modal", label: "Admission Modal", icon: BsWindow },
]

export const CMS_CONTENT_TYPES = [
  { id: "news", label: "News", icon: BsNewspaper, defaultCount: 12 },
  { id: "blogs", label: "Student Blog", icon: BsPen, defaultCount: 2 },
  { id: "notices", label: "Notices", icon: BsExclamationCircle, defaultCount: 19 },
  { id: "results", label: "Results", icon: BsBarChart, defaultCount: 5 },
  { id: "events", label: "Events & Workshops", icon: BsCalendarEvent, defaultCount: 4 },
  { id: "programs", label: "Programs", icon: BsGrid1X2, defaultCount: 3 },
  { id: "scholarships", label: "Scholarships", icon: BsAward, defaultCount: 1 },
  { id: "faqs", label: "FAQs", icon: BsQuestionCircle, defaultCount: 4 },
  { id: "applications", label: "Applications", icon: BsFileText, defaultCount: 1 },
  { id: "enquiries", label: "Enquiries", icon: BsEnvelope, defaultCount: 0 },
  { id: "feedback", label: "Feedback", icon: BsHeart, defaultCount: 1 },
  { id: "testimonials", label: "Testimonials", icon: BsChatQuote, defaultCount: 1 },
  { id: "surveys", label: "Surveys", icon: BsCardChecklist, defaultCount: 1 },
  { id: "survey_responses", label: "Survey Responses", icon: BsListCheck, defaultCount: 3 },
  { id: "trash", label: "Content Trash", icon: BsTrash, defaultCount: 0 },
]

export const CMS_JOURNALS = [
  { id: "abstracts", label: "Abstract", icon: BsFileEarmarkText, defaultCount: 5 },
  { id: "journals", label: "Journal Section", icon: BsJournalBookmark, defaultCount: 2 },
]

export default function CmsSubSidebar({
  activeView = "overview",
  activeSubId = null,
  onSelectView,
  pages = [],
  sections = [],
  contentCounts = {},
  onSelectPage,
  activePageId = null,
  activeSectionId = null,
  onSelectSection,
}) {
  const [pagesExpanded, setPagesExpanded] = useState(true)
  const [allPagesOpen, setAllPagesOpen] = useState(false)
  const [pageSearch, setPageSearch] = useState("")
  const [expandedPages, setExpandedPages] = useState({})

  const togglePageAccordion = (pageKey, e) => {
    e.stopPropagation()
    setExpandedPages(prev => ({ ...prev, [pageKey]: !prev[pageKey] }))
  }

  // Group sections by page for accordion view
  const sectionsByPage = useMemo(() => {
    const map = {}
    sections.forEach(s => {
      const pId = s.page_id || s.page
      if (!map[pId]) map[pId] = []
      map[pId].push(s)
    })
    return map
  }, [sections])

  // Filter all 65 pages
  const filteredPages = useMemo(() => {
    if (!pageSearch.trim()) return pages
    const q = pageSearch.toLowerCase()
    return pages.filter(p => (p.title || "").toLowerCase().includes(q) || (p.route || "").toLowerCase().includes(q) || (p.key || "").toLowerCase().includes(q))
  }, [pages, pageSearch])

  return (
    <aside
      aria-label="CMS Navigation sub-sidebar"
      className="w-64 sm:w-72 shrink-0 bg-[#0B132B] text-slate-200 border-r border-slate-800/80 flex flex-col h-[calc(100vh-6rem)] sticky top-20 rounded-2xl overflow-hidden shadow-2xl select-none"
    >
      {/* Sidebar Header */}
      <div className="p-3.5 border-b border-slate-800/80 bg-[#080E21] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-blue-600/30 border border-blue-500/40 grid place-items-center text-blue-400">
            <BsLayers size={15} />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-white">CMS Studio</span>
            <span className="block text-[10px] text-emerald-400 font-medium">● 65 Pages Live</span>
          </div>
        </div>
      </div>

      {/* Scrollable Navigation Body */}
      <div className="flex-1 overflow-y-auto px-2.5 py-3 space-y-4 text-xs font-medium scrollbar-thin scrollbar-thumb-slate-700">

        {/* OVERVIEW SECTION */}
        <div>
          <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Overview
          </div>
          <button
            type="button"
            onClick={() => onSelectView("overview")}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all ${
              activeView === "overview"
                ? "bg-[#1D4ED8] text-white font-semibold shadow-sm"
                : "text-slate-300 hover:text-white hover:bg-slate-800/60"
            }`}
          >
            <BsSpeedometer2 size={15} className={activeView === "overview" ? "text-white" : "text-slate-400"} />
            <span className="flex-1">Dashboard</span>
          </button>
        </div>

        {/* PAGES & SECTIONS */}
        <div>
          <div className="flex items-center justify-between px-2 pb-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Pages
            </span>
            <button
              type="button"
              onClick={() => setPagesExpanded(!pagesExpanded)}
              className="text-slate-400 hover:text-white p-0.5 rounded"
              title={pagesExpanded ? "Collapse Pages" : "Expand Pages"}
            >
              <BsChevronDown size={11} className={`transition-transform duration-200 ${pagesExpanded ? "" : "-rotate-90"}`} />
            </button>
          </div>

          {pagesExpanded && (
            <div className="space-y-0.5">
              {CMS_CORE_FEATURED_PAGES.map(item => {
                const Icon = item.icon
                const matchedDbPage = pages.find(p => p.key === item.key || p.route === item.route)
                const pageId = matchedDbPage?.id
                const isPageSelected = activeView === "page" && (activePageId === pageId || (!activePageId && item.key === "home"))
                const isPublished = matchedDbPage ? matchedDbPage.status === "published" : true
                const pageSections = pageId ? (sectionsByPage[pageId] || []) : []
                const isAccordionOpen = Boolean(expandedPages[item.key])

                return (
                  <div key={item.key}>
                    <button
                      type="button"
                      onClick={() => {
                        onSelectPage(matchedDbPage || { id: null, key: item.key, title: item.title, route: item.route })
                      }}
                      className={`w-full group flex items-center justify-between px-3 py-1.5 rounded-lg text-left transition-all ${
                        isPageSelected
                          ? "bg-[#1D4ED8] text-white font-semibold shadow-sm"
                          : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <Icon size={14} className={isPageSelected ? "text-white" : "text-slate-400 group-hover:text-slate-200"} />
                        <span className="truncate">{item.title}</span>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        {/* Active indicator dot */}
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            isPublished
                              ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]"
                              : "bg-amber-400"
                          }`}
                          title={isPublished ? "Published live" : "Draft state"}
                        />

                        {/* Chevron for sub-sections drill-down */}
                        {item.hasChildren && (
                          <span
                            role="button"
                            tabIndex={0}
                            onClick={(e) => togglePageAccordion(item.key, e)}
                            className="p-0.5 rounded text-slate-400 hover:text-white hover:bg-slate-700/50"
                          >
                            <BsChevronDown size={10} className={`transition-transform duration-200 ${isAccordionOpen ? "rotate-180" : ""}`} />
                          </span>
                        )}
                      </div>
                    </button>

                    {/* Sub-sections tree */}
                    {item.hasChildren && isAccordionOpen && (
                      <div className="pl-6 pr-1 py-1 space-y-0.5 border-l border-slate-700/40 ml-4 my-0.5">
                        {pageSections.length > 0 ? (
                          pageSections.map(sec => (
                            <button
                              key={sec.id}
                              type="button"
                              onClick={() => {
                                onSelectPage(matchedDbPage)
                                onSelectSection(sec)
                              }}
                              className={`w-full flex items-center justify-between px-2 py-1 rounded text-[11px] truncate text-left transition-all ${
                                activeSectionId === sec.id
                                  ? "bg-blue-600/60 text-white font-medium"
                                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                              }`}
                            >
                              <span className="truncate">{sec.title || sec.key}</span>
                              <span className={`w-1 h-1 rounded-full ${sec.status === "published" ? "bg-emerald-400" : "bg-amber-400"}`} />
                            </button>
                          ))
                        ) : (
                          <div className="px-2 py-1 text-[10px] text-slate-500 italic">
                            Default sections loaded
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}

              {/* All 65 Pages Drawer */}
              <div className="pt-1.5">
                <button
                  type="button"
                  onClick={() => setAllPagesOpen(!allPagesOpen)}
                  className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/40 text-[11px] font-semibold border border-dashed border-slate-700/60"
                >
                  <span className="flex items-center gap-1.5">
                    <BsFolder2Open size={12} />
                    <span>All {pages.length || 65} Pages Directory</span>
                  </span>
                  <BsChevronRight size={10} className={`transition-transform duration-200 ${allPagesOpen ? "rotate-90" : ""}`} />
                </button>

                {allPagesOpen && (
                  <div className="mt-1.5 p-1.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5 max-h-56 overflow-y-auto">
                    <div className="relative">
                      <BsSearch className="absolute left-2 top-2 text-slate-500" size={10} />
                      <input
                        value={pageSearch}
                        onChange={(e) => setPageSearch(e.target.value)}
                        placeholder="Filter 65 pages..."
                        className="w-full rounded bg-slate-800/90 pl-6 pr-2 py-1 text-[11px] text-white placeholder-slate-500 border border-slate-700 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div className="space-y-0.5">
                      {filteredPages.map(page => (
                        <button
                          key={page.id || page.key}
                          type="button"
                          onClick={() => onSelectPage(page)}
                          className={`w-full flex items-center justify-between px-2 py-1 rounded text-[11px] truncate text-left ${
                            activeView === "page" && activePageId === page.id
                              ? "bg-blue-600 text-white font-medium"
                              : "text-slate-300 hover:bg-slate-800 hover:text-white"
                          }`}
                        >
                          <span className="truncate">{page.title || page.key}</span>
                          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${page.status === "published" ? "bg-emerald-400" : "bg-amber-400"}`} />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* SECTIONS (GLOBAL) */}
        <div>
          <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Sections
          </div>
          <div className="space-y-0.5">
            {CMS_GLOBAL_SECTIONS.map(item => {
              const Icon = item.icon
              const isSelected = activeView === "global_section" && activeSubId === item.id

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectView("global_section", item.id)}
                  className={`w-full group flex items-center justify-between px-3 py-1.5 rounded-lg text-left transition-all ${
                    isSelected
                      ? "bg-[#1D4ED8] text-white font-semibold shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon size={14} className={isSelected ? "text-white" : "text-slate-400 group-hover:text-slate-200"} />
                    <span className="truncate">{item.label}</span>
                  </div>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] shrink-0" />
                </button>
              )
            })}
          </div>
        </div>

        {/* CONTENT */}
        <div>
          <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Content
          </div>
          <div className="space-y-0.5">
            {CMS_CONTENT_TYPES.map(item => {
              const Icon = item.icon
              const isSelected = activeView === "content" && activeSubId === item.id
              const count = contentCounts[item.id] !== undefined ? contentCounts[item.id] : item.defaultCount

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectView("content", item.id)}
                  className={`w-full group flex items-center justify-between px-3 py-1.5 rounded-lg text-left transition-all ${
                    isSelected
                      ? "bg-[#1D4ED8] text-white font-semibold shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon size={14} className={isSelected ? "text-white" : "text-slate-400 group-hover:text-slate-200"} />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {count !== null && count > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700/60 shrink-0">
                      {count}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* JOURNALS */}
        <div>
          <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Journals
          </div>
          <div className="space-y-0.5">
            {CMS_JOURNALS.map(item => {
              const Icon = item.icon
              const isSelected = activeView === "journals" && activeSubId === item.id
              const count = contentCounts[item.id] !== undefined ? contentCounts[item.id] : item.defaultCount

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectView("journals", item.id)}
                  className={`w-full group flex items-center justify-between px-3 py-1.5 rounded-lg text-left transition-all ${
                    isSelected
                      ? "bg-[#1D4ED8] text-white font-semibold shadow-sm"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon size={14} className={isSelected ? "text-white" : "text-slate-400 group-hover:text-slate-200"} />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {count !== null && count > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700/60 shrink-0">
                      {count}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        </div>

      </div>
    </aside>
  )
}
