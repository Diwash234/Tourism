import { useEffect, useState } from "react"
import { Link, NavLink, useLocation } from "react-router-dom"
import {
  BsX, BsBoxArrowInRight, BsPersonPlus, BsChevronDown, BsChevronRight,
} from "react-icons/bs"
import { UI_ICON } from "../../utils/uiIcons"

import useAuth from "../../hooks/useAuth"
import useSidebarState, { closeSidebar } from "../../hooks/useSidebarState"
import { useI18n } from "../../i18n"
import usePublicConfig from "../../hooks/usePublicConfig"
import { userDisplayName, userRoleLabel } from "../../utils/placeUtils"
import LanguageSwitcher from "../common/LanguageSwitcher"

// link.icon is a name from the real UI icon set (public/icons/ui/) —
// original duotone pictograms (node scripts/generate-ui-icons.mjs).
const GROUPS = [
  {
    label: "Discover", tk: "sidebar.explore",
    links: [
      { to: "/destinations", label: "Destinations", tk: "sidebar.destinations", icon: "pin", color: "forest" },
      { to: "/recommendation", label: "Recommended", tk: "sidebar.recommendations", icon: "star", color: "emerald" },
      { to: "/gallery", label: "Gallery", tk: "sidebar.gallery", icon: "image", color: "pink" },
      { to: "/compare", label: "Compare Places", tk: "sidebar.compare", icon: "bar-chart", color: "orange" },
      { to: "/nearby-places", label: "Nearby", icon: "compass", color: "forest" },
      { to: "/distances", label: "Distances & Directions", tk: "sidebar.distances", icon: "distance", color: "amber" },
      { to: "/travel", label: "Travel Planner", tk: "sidebar.travel_planner", icon: "route", color: "emerald" },
      { to: "/explore-map", label: "Explore by Province", tk: "sidebar.explore_map", icon: "map", color: "forest" },
      { to: "/discover-nepal", label: "Discover Nepal", tk: "sidebar.discover", icon: "book", color: "himalaya" },
      { to: "/packages", label: "Travel Packages", tk: "sidebar.packages", icon: "briefcase", color: "orange" },
      { to: "/collaborate", label: "Partner with us", icon: "briefcase", color: "emerald" },
    ],
  },
  {
    label: "Plan", tk: "sidebar.planning",
    links: [
      { to: "/itinerary", label: "Trip Planner & Itineraries", tk: "sidebar.trip_planner", icon: "calendar", color: "emerald" },
      { to: "/expenditure", label: "Expense Tracker", tk: "sidebar.expenditure", icon: "wallet", color: "emerald" },
      { to: "/budget-estimator", label: "Budget Estimator", tk: "sidebar.budget", icon: "calculator", color: "orange" },
      { to: "/favorites", label: "Saved Trips", tk: "sidebar.favorites", icon: "heart", color: "pink" },
      { to: "/my-bookings", label: "Bookings", tk: "sidebar.bookings", icon: "ticket", color: "emerald" },
      { to: "/trip", label: "Trip requests", icon: "ticket", color: "orange" },
      { to: "/partner", label: "Partner desk", icon: "briefcase", color: "saffron" },
    ],
  },
  {
    label: "Stay", tk: "sidebar.hotels",
    links: [
      { to: "/hotels/search", label: "Find Hotels", icon: "building", color: "saffron" },
      { to: "/hotels", label: "Saved Hotels", icon: "houses", color: "saffron", end: true },
    ],
  },
  {
    label: "Safety", tk: "sidebar.safety",
    links: [
      { to: "/emergency", label: "Emergency / SOS", tk: "sidebar.emergency", icon: "warning", color: "red" },
      { to: "/risk-alerts", label: "Travel Alerts", tk: "sidebar.risk", icon: "bell", color: "nepalred" },
      { to: "/family-safety", label: "Family Safety", icon: "people", color: "emerald" },
      { to: "/navigation", label: "Location", tk: "sidebar.navigation", icon: "navigate", color: "sky" },
      { to: "/language", label: "Phrasebook", tk: "sidebar.phrasebook", icon: "quote", color: "emerald" },
      { to: "/translation", label: "Live Translation", tk: "sidebar.translation", icon: "translate", color: "cyan" },
      { to: "/chatbot", label: "Himal AI Assistant", tk: "sidebar.chatbot", icon: "robot", color: "terracotta" },
    ],
  },
  {
    label: "Account", tk: "sidebar.account",
    links: [
      { to: "/dashboard", label: "My Dashboard", tk: "sidebar.dashboard", icon: "house", color: "himalaya" },
      { to: "/personal-details", label: "Personal Details", tk: "sidebar.personal_details", icon: "card", color: "himalaya" },
      { to: "/notifications", label: "Notifications", icon: "inbox", color: "saffron" },
      { to: "/my-submissions", label: "My Submissions", tk: "sidebar.submissions", icon: "check-square", color: "saffron" },
      { to: "/history", label: "Visit History", tk: "sidebar.history", icon: "clock", color: "stone" },
      { to: "/destinations/submit", label: "Submit Place", tk: "sidebar.submit", icon: "plus", color: "saffron" },
      { to: "/submit-service", label: "Submit a Service", icon: "hospital", color: "emerald" },
      { to: "/settings", label: "Settings", tk: "sidebar.settings", icon: "gear", color: "stone" },
    ],
  },
  {
    label: "Workspace portals", tk: "sidebar.portals",
    links: [
      { to: "/admin", label: "Admin Central", tk: "sidebar.admin", icon: "shield", color: "nepalred", roleCheck: "admin" },
      { to: "/admin/diagnostics", label: "Diagnostics Center", tk: "sidebar.diagnostics", icon: "activity", color: "terracotta", roleCheck: "admin" },
      { to: "/staff", label: "Staff Operations", tk: "sidebar.staff", icon: "briefcase", color: "saffron", roleCheck: "staff" },
      { to: "/local/dashboard", label: "Local Guide Portal", tk: "sidebar.local", icon: "house", color: "emerald", roleCheck: "local" },
    ],
  },
]

const COLOR_MAP = {
  // Unified deep-green chips on the emerald-950 rail (matches the admin
  // dashboard green theme — one consistent green sidebar across the app).
  himalaya: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  forest: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  saffron: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  nepalred: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  red: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  orange: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  pink: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  emerald: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  sky: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  violet: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  purple: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  terracotta: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  cyan: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
  stone: "text-[#BDEBD9] bg-white/10 group-hover:bg-white/15",
}

const isDesktop = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(min-width: 1024px)").matches

export default function Sidebar() {
  const { isAuthenticated, user, isAdmin, isStaff, isLocal } = useAuth()
  const { t } = useI18n()
  const { navigation } = usePublicConfig()
  const location = useLocation()
  const [managedItems, setManagedItems] = useState([])
  // Groups are click-controlled (brief §17): nothing auto-expands except the
  // group that contains the active route, so the current page stays visible.
  const [expanded, setExpanded] = useState({})
  const [open] = useSidebarState()
  // Icon-rail mode: desktop with the rail closed. On mobile !open simply
  // means the drawer is off-screen, so the same flat icon rendering is inert.
  const iconMode = !open
  const drawerHidden = !open && !isDesktop()

  useEffect(() => {
    const timer = setTimeout(() => setManagedItems((navigation || []).filter(item => item.location === "sidebar")), 0)
    return () => clearTimeout(timer)
  }, [navigation])

  const handleNav = () => {
    if (!isDesktop()) closeSidebar()
  }

  const PUBLIC_ROUTES = new Set([
    "/", "/destinations", "/recommendation", "/gallery", "/compare", "/nearby-places",
    "/distances", "/itinerary", "/explore-map", "/discover-nepal", "/packages", "/guides", "/guide-portal", "/tourism-jobs", "/guide-bookings", "/collaborate", "/hotels/search",
    "/emergency", "/risk-alerts", "/budget-estimator", "/navigation", "/language", "/translation", "/chatbot", "/travel",
    "/about", "/contact", "/support", "/how-it-works", "/privacy", "/terms", "/login", "/register"
  ])

  const managedByRoute = new Map(managedItems.filter(item => String(item.route).startsWith("/")).map(item => [item.route, item]))
  const visibleGroups = GROUPS.map((grp) => ({
    ...grp,
    links: grp.links
      .filter(link => managedItems.length === 0 || managedByRoute.has(link.to) || link.roleCheck)
      .map(link => managedByRoute.has(link.to) ? { ...link, label: managedByRoute.get(link.to).label } : link)
      .filter((link) => {
        if (!isAuthenticated && !PUBLIC_ROUTES.has(link.to)) return false
        if (link.roleCheck === "admin" && !isAdmin) return false
        if (link.roleCheck === "staff" && !isStaff) return false
        if (link.roleCheck === "local" && !isLocal && !isAdmin) return false
        return true
      }),
  })).filter((g) => g.links.length > 0)
  const dynamicLinks = managedItems
    .filter(item => /^\/page\/[^/]+$/.test(String(item.route || "")))
    .map(item => ({ to: item.route, label: item.label, icon: "file", end: true }))
  if (dynamicLinks.length) visibleGroups.push({ label: "More pages", links: dynamicLinks })

  // Expand the group that owns the active route (brief §17/§20); other groups
  // keep whatever the user last chose. Deferred one tick: keeps synchronous
  // setState out of the effect flush (react-hooks/set-state-in-effect).
  useEffect(() => {
    const t = setTimeout(() => {
      const owner = visibleGroups.find((grp) =>
        grp.links.some((link) => location.pathname === link.to || (!link.end && location.pathname.startsWith(`${link.to}/`)))
      )
      if (owner) setExpanded((prev) => (prev[owner.label] ? prev : { ...prev, [owner.label]: true }))
    }, 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

  const linkClass = ({ isActive }) =>
    `flex min-h-11 items-center gap-3 rounded-[var(--ny-radius-sm)] px-3 text-xs font-semibold transition-all group whitespace-nowrap ${
      iconMode ? "lg:justify-center lg:px-1" : ""
    } ${
      isActive
        ? "bg-[var(--ny-green)] text-white shadow-[0_4px_12px_rgba(7,91,72,0.24)]"
        : "text-[#C7D9D2] hover:bg-white/10 hover:text-white"
    }`

  const renderLink = (link) => {
    const colorClass = COLOR_MAP[link.color] || COLOR_MAP.stone
    return (
      <NavLink
        key={link.to}
        to={link.to}
        end={!!link.end}
        onClick={handleNav}
        className={linkClass}
        title={link.tk ? t(link.tk) : link.label}
        aria-label={link.tk ? t(link.tk) : link.label}
      >
        <div className={`p-1 rounded-lg shrink-0 ${colorClass}`}>
          {typeof link.icon === "string" ? (
            <img src={UI_ICON(link.icon)} alt="" aria-hidden="true" className="w-5 h-5" draggable={false} />
          ) : (
            <link.icon size={14} />
          )}
        </div>
        {/* Label: never wraps vertically — hidden entirely in icon-rail mode */}
        <span className={`truncate ${iconMode ? "lg:hidden" : ""}`}>{link.tk ? t(link.tk) : link.label}</span>
      </NavLink>
    )
  }

  return (
    <>
      <div
        onClick={closeSidebar}
        className={`fixed inset-0 top-16 bg-black/40 z-30 lg:hidden sidebar-backdrop transition-opacity duration-300 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
        data-sidebar-backdrop="true"
        aria-hidden="true"
      />

      <aside
        id="sidebar-drawer"
        aria-label="Secondary navigation"
        aria-hidden={drawerHidden || undefined}
        className={`sidebar-drawer fixed bottom-0 left-0 top-16 z-50 w-60 max-w-[88vw] overflow-x-hidden overflow-y-auto overscroll-contain border-r border-white/10 bg-[var(--ny-green-deepest)] shadow-[var(--ny-shadow-elevated)] transition-[transform,width,visibility] duration-200 will-change-transform lg:max-w-none lg:translate-x-0 lg:shadow-none ${open ? "visible translate-x-0 lg:w-64" : "-translate-x-full lg:w-16"} ${drawerHidden ? "invisible" : "visible"}`}
        style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
      >
        <div className={`space-y-5 ${iconMode ? "p-2 lg:p-1.5" : "p-4"}`}>
          {/* Rail expand/collapse control — icon only, no visible word (brief §4/§18) */}
          <RailToggle />
          <div className="flex items-center justify-between lg:hidden">
            <span className="text-sm font-bold text-white">Traveller menu</span>
            <button type="button" onClick={closeSidebar} className="p-2 rounded-lg hover:bg-emerald-800 text-[#BDEBD9]" aria-label="Close menu">
              <BsX size={18} />
            </button>
          </div>

          {isAuthenticated ? (
            <div className={`p-3.5 rounded-2xl bg-[#063B32] border border-white/10 flex items-center gap-3 ${iconMode ? "lg:justify-center lg:p-2" : ""}`}>
              <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white font-black flex items-center justify-center text-sm shadow shrink-0">
                {userDisplayName(user)?.[0]?.toUpperCase() || "T"}
              </div>
              <div className={`min-w-0 ${iconMode ? "lg:hidden" : ""}`}>
                <p className="font-bold text-xs text-white truncate">{userDisplayName(user)}</p>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-emerald-800 text-[#BDEBD9]">
                  {userRoleLabel(user)}
                </span>
              </div>
            </div>
          ) : (
            <div className={`p-3 rounded-2xl bg-[#063B32] border border-white/10 flex gap-2 ${iconMode ? "lg:hidden" : ""}`}>
              <Link to="/login" onClick={handleNav} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-500">
                <BsBoxArrowInRight size={13} /> Login
              </Link>
              <Link to="/register" onClick={handleNav} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border border-emerald-600 text-[#C7D9D2] text-xs font-bold hover:bg-emerald-800">
                <BsPersonPlus size={13} /> Sign up
              </Link>
            </div>
          )}

          {/* Language — lives here (expanded view) so it stays reachable on
              phones, where the navbar's switcher is hidden. The navbar shows
              it too on md+ screens. Hidden in the collapsed icon-rail. */}
          {!iconMode && (
            <div className="px-1">
              <p className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-400 mb-1.5 px-1">
                {t("sidebar.language")}
              </p>
              <div className="flex items-center gap-2 px-1">
                <LanguageSwitcher compact />
              </div>
            </div>
          )}

          {iconMode ? (
            /* Icon-rail mode: flat list of every visible link, icons only,
               grouped with subtle dividers (brief §5/§6/§34) */
            <div className="space-y-2">
              {visibleGroups.map((grp, gi) => (
                <div key={grp.label} className="space-y-0.5">
                  {gi > 0 && <div className="mx-2 my-1.5 border-t border-white/10" aria-hidden="true" />}
                  {grp.links.map(renderLink)}
                </div>
              ))}
            </div>
          ) : (
            /* Expanded mode: click-controlled collapsible groups (brief §17) */
            visibleGroups.map((grp) => (
              <div key={grp.label} className="space-y-1">
                <button
                  type="button"
                  onClick={() => setExpanded((value) => ({ ...value, [grp.label]: !value[grp.label] }))}
                  className="flex min-h-11 w-full items-center justify-between px-3 py-2 text-xs font-extrabold text-[#BDEBD9] uppercase tracking-wider whitespace-nowrap"
                  aria-expanded={expanded[grp.label] === true}
                >
                  {grp.tk ? t(grp.tk) : grp.label}
                  {expanded[grp.label] === true ? <BsChevronDown size={14} /> : <BsChevronRight size={14} />}
                </button>
                {expanded[grp.label] === true && (
                  <div className="space-y-0.5 border-l-2 border-white/15 ml-3 pl-1">
                    {grp.links.map(renderLink)}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  )
}

/** Desktop-only rail width toggle. Icon + accessible label, no visible word. */
function RailToggle() {
  const [open, , , , , , toggleCollapsed] = useSidebarState()
  return (
    <button
      type="button"
      onClick={toggleCollapsed}
      className="hidden lg:flex w-full items-center justify-center py-1.5 rounded-lg text-[#BDEBD9] hover:bg-emerald-800 hover:text-white transition-colors"
      aria-label={open ? "Collapse sidebar to icons" : "Expand sidebar"}
      title={open ? "Collapse sidebar" : "Expand sidebar"}
    >
      <BsChevronRight size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
    </button>
  )
}
