import { useEffect, useState } from "react"
import { Link, NavLink } from "react-router-dom"
import {
  BsHouseDoor, BsPerson, BsGeoAlt, BsHeart, BsClockHistory, BsBell, BsGear,
  BsWallet2, BsCalculator, BsCalendar3, BsExclamationTriangle, BsCompass,
  BsTranslate, BsChatDots, BsJournalBookmark, BsShieldLock, BsBuilding, BsBriefcase,
  BsPlusCircle, BsCheck2Square, BsX, BsBoxArrowInRight, BsPersonPlus, BsBarChart, BsImage,
  BsActivity, BsChevronDown, BsChevronRight, BsSignpost, BsStar, BsMap, BsBook,
  BsListOl, BsTicketPerforated, BsPeople, BsChatQuote, BsRobot, BsCardText, BsInbox,
  BsHospital, BsHouses,
} from "react-icons/bs"

import useAuth from "../../hooks/useAuth"
import { closeSidebar } from "../../hooks/useSidebarState"
import { useI18n } from "../../i18n"
import configApi from "../../api/configApi"

const GROUPS = [
  {
    label: "Explore", tk: "sidebar.explore",
    links: [
      { to: "/destinations", label: "Destinations", tk: "sidebar.destinations", icon: BsGeoAlt, color: "forest" },
      { to: "/recommendation", label: "Recommended", tk: "sidebar.recommendations", icon: BsStar, color: "emerald" },
      { to: "/gallery", label: "Gallery", tk: "sidebar.gallery", icon: BsImage, color: "pink" },
      { to: "/compare", label: "Compare Places", tk: "sidebar.compare", icon: BsBarChart, color: "orange" },
      { to: "/nearby-places", label: "Nearby", icon: BsCompass, color: "forest" },
      { to: "/explore-map", label: "Explore by Province", tk: "sidebar.explore_map", icon: BsMap, color: "forest" },
      { to: "/discover-nepal", label: "Discover Nepal", tk: "sidebar.discover", icon: BsBook, color: "himalaya" },
      { to: "/packages", label: "Travel Packages", tk: "sidebar.packages", icon: BsBriefcase, color: "orange" },
      { to: "/collaborate", label: "Partner with us", icon: BsBriefcase, color: "emerald" },
    ],
  },
  {
    label: "My Trips", tk: "sidebar.planning",
    links: [
      { to: "/trip-planner", label: "Trip Planner", tk: "sidebar.trip_planner", icon: BsCalendar3, color: "emerald" },
      { to: "/itinerary", label: "Itineraries", tk: "sidebar.itinerary", icon: BsListOl, color: "himalaya" },
      { to: "/expenditure", label: "Expense Tracker", tk: "sidebar.expenditure", icon: BsWallet2, color: "emerald" },
      { to: "/budget-estimator", label: "Budget Estimator", tk: "sidebar.budget", icon: BsCalculator, color: "orange" },
      { to: "/favorites", label: "Saved Trips", tk: "sidebar.favorites", icon: BsHeart, color: "pink" },
      { to: "/my-bookings", label: "Bookings", tk: "sidebar.bookings", icon: BsTicketPerforated, color: "emerald" },
      { to: "/trip", label: "Trip requests", icon: BsTicketPerforated, color: "orange" },
      { to: "/partner", label: "Partner desk", icon: BsBriefcase, color: "saffron" },
    ],
  },
  {
    label: "Hotels", tk: "sidebar.hotels",
    links: [
      { to: "/hotels/search", label: "Find Hotels", icon: BsBuilding, color: "saffron" },
      { to: "/hotels", label: "Saved Hotels", icon: BsHouses, color: "saffron" },
    ],
  },
  {
    label: "Safety", tk: "sidebar.safety",
    links: [
      { to: "/emergency", label: "Emergency / SOS", tk: "sidebar.emergency", icon: BsExclamationTriangle, color: "red" },
      { to: "/risk-alerts", label: "Travel Alerts", tk: "sidebar.risk", icon: BsBell, color: "nepalred" },
      { to: "/family-safety", label: "Family Safety", icon: BsPeople, color: "emerald" },
      { to: "/navigation", label: "Location", tk: "sidebar.navigation", icon: BsSignpost, color: "sky" },
      { to: "/language", label: "Phrasebook", tk: "sidebar.phrasebook", icon: BsChatQuote, color: "emerald" },
      { to: "/translation", label: "Live Translation", tk: "sidebar.translation", icon: BsTranslate, color: "cyan" },
      { to: "/chatbot", label: "Himal AI Assistant", tk: "sidebar.chatbot", icon: BsRobot, color: "terracotta" },
    ],
  },
  {
    label: "Account", tk: "sidebar.account",
    links: [
      { to: "/dashboard", label: "My Dashboard", tk: "sidebar.dashboard", icon: BsHouseDoor, color: "himalaya" },
      { to: "/profile", label: "Profile", tk: "sidebar.profile", icon: BsPerson, color: "himalaya" },
      { to: "/personal-details", label: "Personal Details", tk: "sidebar.personal_details", icon: BsCardText, color: "himalaya" },
      { to: "/notifications", label: "Notifications", icon: BsInbox, color: "saffron" },
      { to: "/my-submissions", label: "My Submissions", tk: "sidebar.submissions", icon: BsCheck2Square, color: "saffron" },
      { to: "/history", label: "Visit History", tk: "sidebar.history", icon: BsClockHistory, color: "stone" },
      { to: "/destinations/submit", label: "Submit Place", tk: "sidebar.submit", icon: BsPlusCircle, color: "saffron" },
      { to: "/submit-service", label: "Submit a Service", icon: BsHospital, color: "emerald" },
      { to: "/settings", label: "Settings", tk: "sidebar.settings", icon: BsGear, color: "stone" },
    ],
  },
  {
    label: "Workspace portals", tk: "sidebar.portals",
    links: [
      { to: "/admin", label: "Admin Central", tk: "sidebar.admin", icon: BsShieldLock, color: "nepalred", roleCheck: "admin" },
      { to: "/admin/diagnostics", label: "Diagnostics Center", tk: "sidebar.diagnostics", icon: BsActivity, color: "terracotta", roleCheck: "admin" },
      { to: "/staff", label: "Staff Operations", tk: "sidebar.staff", icon: BsBriefcase, color: "saffron", roleCheck: "staff" },
      { to: "/local/dashboard", label: "Local Guide Portal", tk: "sidebar.local", icon: BsHouseDoor, color: "emerald", roleCheck: "local" },
    ],
  },
]

const COLOR_MAP = {
  himalaya: "text-blue-600 bg-blue-50 group-hover:bg-blue-100",
  forest: "text-emerald-600 bg-emerald-50 group-hover:bg-emerald-100",
  saffron: "text-amber-600 bg-amber-50 group-hover:bg-amber-100",
  nepalred: "text-rose-600 bg-rose-50 group-hover:bg-rose-100",
  red: "text-red-600 bg-red-50 group-hover:bg-red-100",
  orange: "text-orange-600 bg-orange-50 group-hover:bg-orange-100",
  pink: "text-pink-600 bg-pink-50 group-hover:bg-pink-100",
  emerald: "text-emerald-600 bg-emerald-50 group-hover:bg-emerald-100",
  sky: "text-sky-600 bg-sky-50 group-hover:bg-sky-100",
  violet: "text-emerald-700 bg-[#F7F8F5] group-hover:bg-emerald-100",
  purple: "text-emerald-700 bg-[#F7F8F5] group-hover:bg-emerald-100",
  terracotta: "text-orange-700 bg-orange-50 group-hover:bg-orange-100",
  cyan: "text-cyan-600 bg-cyan-50 group-hover:bg-cyan-100",
  stone: "text-gray-600 bg-gray-50 group-hover:bg-gray-100",
}

export default function Sidebar() {
  const { isAuthenticated, user, isAdmin, isStaff, isLocal } = useAuth()
  const { t } = useI18n()
  const [managedItems, setManagedItems] = useState([])
  const [expanded, setExpanded] = useState({ Explore: true, "My Trips": true, Hotels: false, Safety: false, Account: true, "Workspace portals": true })
  useEffect(() => { configApi.getPublicConfig().then(({ data }) => setManagedItems((data.navigation || []).filter(item => item.location === "sidebar"))).catch(() => {}) }, [])

  const handleNav = () => {
    if (window.innerWidth < 1024) closeSidebar()
  }

  const PUBLIC_ROUTES = new Set([
    "/", "/destinations", "/recommendation", "/gallery", "/compare", "/nearby-places",
    "/explore-map", "/discover-nepal", "/packages", "/collaborate", "/hotels/search",
    "/emergency", "/risk-alerts", "/navigation", "/language", "/translation", "/chatbot",
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

  return (
    <>
      <div
        onClick={closeSidebar}
        className="fixed inset-0 top-16 bg-black/40 z-30 lg:hidden sidebar-backdrop opacity-0 pointer-events-none transition-opacity duration-300"
        data-sidebar-backdrop="true"
        aria-hidden="true"
      />

      <aside
        className="sidebar-drawer fixed top-16 bottom-0 left-0 z-40 w-64 max-w-[88vw] bg-white border-r border-emerald-100 overflow-y-auto overscroll-contain
                   transform -translate-x-full transition-transform duration-300 will-change-transform
                   shadow-xl lg:translate-x-0 lg:shadow-none lg:max-w-none"
        style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
      >
        <div className="p-4 space-y-5">
          <div className="flex items-center justify-between lg:hidden">
            <span className="text-sm font-bold text-gray-900">Traveller menu</span>
            <button onClick={closeSidebar} className="p-2 rounded-lg hover:bg-gray-100 text-gray-600" aria-label="Close menu">
              <BsX size={18} />
            </button>
          </div>

          {isAuthenticated ? (
            <div className="p-3.5 rounded-2xl bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-100 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-700 text-white font-black flex items-center justify-center text-sm shadow">
                {user?.first_name?.[0] || user?.email[0].toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="font-bold text-xs text-gray-900 truncate">{user?.full_name || user?.email}</p>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
                  {user?.role || "Tourist"}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-2xl bg-gray-50 border border-gray-100 flex gap-2">
              <Link to="/login" onClick={handleNav} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800">
                <BsBoxArrowInRight size={13} /> Login
              </Link>
              <Link to="/register" onClick={handleNav} className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border border-emerald-200 text-emerald-800 text-xs font-bold hover:bg-emerald-50">
                <BsPersonPlus size={13} /> Sign up
              </Link>
            </div>
          )}

          {visibleGroups.map((grp) => (
            <div key={grp.label} className="space-y-1">
              <button
                type="button"
                onClick={() => setExpanded((value) => ({ ...value, [grp.label]: !value[grp.label] }))}
                className="flex w-full items-center justify-between px-3 py-2 text-[11px] font-extrabold text-emerald-800 uppercase tracking-wider"
                aria-expanded={expanded[grp.label] !== false}
              >
                {grp.tk ? t(grp.tk) : grp.label}
                {expanded[grp.label] !== false ? <BsChevronDown size={14} /> : <BsChevronRight size={14} />}
              </button>
              {expanded[grp.label] !== false && (
                <div className="space-y-0.5 border-l-2 border-emerald-100 ml-3 pl-1">
                  {grp.links.map((link) => {
                    const Icon = link.icon
                    const colorClass = COLOR_MAP[link.color] || COLOR_MAP.stone
                    return (
                      <NavLink
                        key={link.to}
                        to={link.to}
                        onClick={handleNav}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all group ${
                            isActive
                              ? "bg-emerald-700 text-white shadow-md"
                              : "text-gray-700 hover:bg-emerald-50 hover:text-emerald-900"
                          }`
                        }
                      >
                        <div className={`p-1.5 rounded-lg ${colorClass}`}>
                          <Icon size={14} />
                        </div>
                        <span>{link.tk ? t(link.tk) : link.label}</span>
                      </NavLink>
                    )
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </aside>
    </>
  )
}
