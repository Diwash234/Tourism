import { useEffect, useState, Suspense } from "react"
import { Link, Outlet, useLocation } from "react-router-dom"
import { FiActivity, FiChevronDown, FiChevronRight, FiMenu, FiShield, FiUsers, FiX } from "react-icons/fi"
import TourismLogo from "../branding/TourismLogo"
import AdminGlobalSearch from "./AdminGlobalSearch"
import ProfileMenu from "../layout/ProfileMenu"
import useMediaQuery from "../../hooks/useMediaQuery"
import { ADMIN_NAV_GROUPS, ADMIN_PRIMARY_NAV, adminSectionHref, canAccessAdminSection, findAdminSection } from "./adminNavigation"
import useAuth from "../../hooks/useAuth"
import useRouteSeo from "../../hooks/useRouteSeo"

export default function AdminLayout() {
  const { isAdmin, can } = useAuth()
  const visibleGroups = ADMIN_NAV_GROUPS.map(group => ({
    ...group,
    items: group.items.filter(([section]) => isAdmin || canAccessAdminSection(section, can)),
  })).filter(group => group.items.length > 0)
  const isDesktop = useMediaQuery("(min-width: 1024px)")
  const [open, setOpen] = useState(false) // mobile drawer
  const [collapsed, setCollapsed] = useState(() => {
    try { return window.localStorage?.getItem("ny_admin_sidebar_collapsed") === "1" } catch { return false }
  })
  const toggleCollapsed = () =>
    setCollapsed((v) => {
      try { window.localStorage?.setItem("ny_admin_sidebar_collapsed", v ? "0" : "1") } catch { /* ignore */ }
      return !v
    })
  // Three-state model (brief §3/§42): on desktop the hamburger toggles the
  // rail between expanded and icon-only; on mobile it toggles the drawer.
  const toggleSidebar = () => {
    if (isDesktop) toggleCollapsed()
    else setOpen((v) => !v)
  }
  // Groups are click-controlled and start closed; only the group owning the
  // active section opens itself (brief §16/§17).
  const [expanded, setExpanded] = useState({})
  const location = useLocation()
  useRouteSeo()
  const activeSection = new URLSearchParams(location.search).get("section") || "overview"
  const drawerHidden = !open && !isDesktop
  const closeMobile = () => {
    if (typeof window !== "undefined" && !window.matchMedia("(min-width: 1024px)").matches) setOpen(false)
  }

  // Crossing into desktop always clears any stale mobile drawer (brief §43).
  // setState happens inside the media-query event callback, not the effect
  // flush, so this is render-safe.
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return undefined
    const mql = window.matchMedia("(min-width: 1024px)")
    const onChange = (event) => { if (event.matches) setOpen(false) }
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  // Open only the group that owns the active section.
  useEffect(() => {
    const t = setTimeout(() => {
      const owner = visibleGroups.find((group) =>
        group.items.some(([section, , , children]) =>
          section === activeSection ||
          children?.some((child) => (child.query?.section || section) === activeSection)
        )
      )
      if (owner) setExpanded((prev) => (prev[owner.label] ? prev : { ...prev, [owner.label]: true }))
    }, 0)
    return () => clearTimeout(t)
  }, [activeSection])

  return (
    <div className="admin-green-theme min-h-screen bg-slate-50 text-slate-900">
      <a href="#admin-main" className="admin-skip-link">Skip to admin content</a>
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center gap-3 overflow-visible border-b border-slate-200 bg-white px-3 text-slate-900 shadow-sm sm:px-5">
        <button
          onClick={toggleSidebar}
          className="admin-icon-button !min-h-11 !min-w-11 !bg-emerald-50 !text-emerald-800"
          aria-label={isDesktop ? (collapsed ? "Expand admin sidebar" : "Collapse admin sidebar to icons") : (open ? "Close admin navigation" : "Open admin navigation")}
          aria-expanded={isDesktop ? !collapsed : open}
          aria-controls="admin-navigation"
        >
          <FiMenu />
        </button>
        <TourismLogo size="sm" to="/admin" showTagline={false} responsiveText />
        <nav aria-label="Priority admin navigation" className="hidden items-center gap-1 xl:flex">
          {ADMIN_PRIMARY_NAV.filter(section => isAdmin || canAccessAdminSection(section, can)).map((section) => {
            const item = findAdminSection(section)
            if (!item) return null
            const Icon = item[2]
            return (
              <Link
                key={section}
                to={adminSectionHref(section)}
                className={`flex items-center gap-1 whitespace-nowrap rounded-lg px-2.5 py-2 text-xs font-bold ${
                  activeSection === section ? "bg-white text-emerald-900" : "text-slate-600 hover:bg-emerald-50"
                }`}
              >
                <Icon />
                {item[1]}
              </Link>
            )
          })}
        </nav>
        <div className="mx-2 hidden min-w-0 max-w-md flex-1 lg:max-w-lg md:block"><AdminGlobalSearch /></div>
        <div className="ml-auto flex items-center gap-1.5 text-xs sm:gap-2">
          <span className="hidden rounded-full bg-emerald-50 px-2 py-1 font-black uppercase tracking-wide text-slate-500 sm:inline">Admin</span>
          <Link to="/" className="hidden min-h-11 items-center whitespace-nowrap rounded-lg bg-white px-3 py-2 font-bold text-emerald-900 sm:inline-flex">Traveller site</Link>
          <ProfileMenu variant="admin" />
        </div>
      </header>

      <aside
        id="admin-navigation"
        aria-label="Admin navigation"
        aria-hidden={drawerHidden || undefined}
        className={`fixed bottom-0 top-16 z-40 w-72 max-w-[90vw] overflow-y-auto overflow-x-hidden overscroll-contain border-r border-slate-200 bg-white text-slate-700 shadow-lg transition-[transform,width] ${drawerHidden ? "invisible" : "visible"} ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:visible lg:translate-x-0 ${collapsed ? "lg:w-16" : "lg:w-72"}`}
        style={{ paddingBottom: "max(0.5rem, env(safe-area-inset-bottom))" }}
      >
        <nav className={`p-4 ${collapsed ? "lg:p-1.5" : ""}`}>
          {/* Rail width toggle — icon only, no visible word (brief §4/§18) */}
          <button
            type="button"
            onClick={toggleCollapsed}
            className="mb-2 hidden w-full items-center justify-center rounded-lg py-1.5 text-slate-400 hover:bg-slate-100 lg:flex"
            aria-label={collapsed ? "Expand admin sidebar" : "Collapse admin sidebar to icons"}
            title={collapsed ? "Expand admin sidebar" : "Collapse admin sidebar"}
          >
            <FiChevronRight className={`transition-transform ${collapsed ? "" : "rotate-180"}`} />
          </button>
          <div className={`mb-4 rounded-xl bg-slate-50 p-3 text-white ${collapsed ? "lg:hidden" : ""}`}>
            <FiShield className="inline text-slate-400" /> <b>Administrator workspace</b>
            <p className="mt-1 text-xs text-slate-500">CMS, media, users, analytics and safety</p>
          </div>
          {visibleGroups.map((group) => (
            <section key={group.label} className="mb-2">
              <button
                onClick={() => setExpanded((value) => ({ ...value, [group.label]: !value[group.label] }))}
                className={`flex min-h-10 w-full items-center justify-between py-2 text-xs font-black uppercase tracking-widest text-slate-400 ${collapsed ? "lg:hidden" : ""}`}
                aria-expanded={expanded[group.label]}
              >
                {group.label}
                {expanded[group.label] ? <FiChevronDown /> : <FiChevronRight />}
              </button>
              {/* In icon-rail mode every link stays reachable regardless of
                  group expansion state (brief §5/§6) */}
              {(expanded[group.label] || collapsed) && (
                <div className={`space-y-1 border-l-2 border-slate-200 pl-2 ${collapsed ? "lg:border-l-0 lg:pl-0" : ""}`}>
                  {group.items.map(([section, label, Icon, children]) => (
                    <div key={section}>
                      <Link
                        to={adminSectionHref(section)}
                        onClick={closeMobile}
                        aria-current={activeSection === section ? "page" : undefined}
                        title={label}
                        aria-label={label}
                        className={`flex min-h-10 items-center gap-3 whitespace-nowrap rounded-xl px-3 py-2 text-sm ${
                          collapsed ? "lg:justify-center lg:px-1" : ""
                        } ${
                          activeSection === section
                            ? "bg-white font-black text-emerald-900 shadow-sm"
                            : "text-slate-600 hover:bg-slate-100 hover:text-white"
                        }`}
                      >
                        <Icon aria-hidden="true" className="text-base shrink-0" />
                        <span className={`truncate ${collapsed ? "lg:hidden" : ""}`}>{label}</span>
                      </Link>
                      {children?.length > 0 && !collapsed && (activeSection === section || children.some((child) => (child.query?.section || section) === activeSection)) && (
                        <div className="ml-8 mt-1 mb-2 space-y-1 text-xs text-slate-600">
                          {children.map((child) => {
                            const href = adminSectionHref(section, child.query)
                            const targetSection = child.query?.section || section
                            const current = targetSection === activeSection && Object.entries(child.query || {}).filter(([key]) => key !== "section").every(([key, value]) => new URLSearchParams(location.search).get(key) === String(value))
                            return (
                              <Link key={child.label} to={href} onClick={closeMobile} className={`flex items-center gap-2 rounded-lg px-2 py-1.5 ${current ? "bg-emerald-50 text-white" : "hover:bg-slate-100"}`}>
                                <span className={`inline-block h-3 w-3 rounded border ${current ? "border-white bg-amber-400" : "border-slate-300"}`} />
                                {child.label}
                              </Link>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          ))}
          <section className="mt-4 border-t border-slate-200 pt-4">
            <p className={`mb-2 text-xs font-black uppercase text-slate-400 ${collapsed ? "lg:hidden" : ""}`}>Dedicated tools</p>
            <Link to="/admin/diagnostics" onClick={closeMobile} title="Audit & Diagnostics" aria-label="Audit & Diagnostics" className={`flex min-h-10 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 ${collapsed ? "lg:justify-center lg:px-1" : ""}`}>
              <FiActivity className="shrink-0" /> <span className={collapsed ? "lg:hidden" : ""}>Audit & Diagnostics</span>
            </Link>
            <Link to="/admin/hotel-assignments" onClick={closeMobile} title="Hotel Assignments" aria-label="Hotel Assignments" className={`flex min-h-10 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 ${collapsed ? "lg:justify-center lg:px-1" : ""}`}>
              <FiShield className="shrink-0" /> <span className={collapsed ? "lg:hidden" : ""}>Hotel Assignments</span>
            </Link>
            <Link to="/admin/tasks" onClick={closeMobile} title="Staff Tasks" aria-label="Staff Tasks" className={`flex min-h-10 items-center gap-2 whitespace-nowrap rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 ${collapsed ? "lg:justify-center lg:px-1" : ""}`}>
              <FiUsers className="shrink-0" /> <span className={collapsed ? "lg:hidden" : ""}>Staff Tasks</span>
            </Link>
          </section>
        </nav>
      </aside>
      {open && (
        <button type="button" onClick={() => setOpen(false)} className="fixed inset-0 top-16 z-30 bg-black/45 lg:hidden" aria-label="Close admin navigation overlay">
          <FiX className="sr-only" />
        </button>
      )}
      <main id="admin-main" tabIndex="-1" className={`min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 pt-16 transition-[padding] duration-300 ${collapsed ? "lg:pl-16" : "lg:pl-72"}`}>
        <div className="mx-auto w-full max-w-[1600px] p-3 pb-24 sm:p-6 lg:pb-6">
          <Suspense fallback={<div className="container-app flex min-h-[320px] items-center justify-center py-12" role="status" aria-live="polite"><span className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--ny-border)] border-t-[var(--ny-green)]" aria-hidden="true" /><span className="sr-only">Loading page</span></div>}><Outlet /></Suspense>
        </div>
      </main>
    </div>
  )
}
