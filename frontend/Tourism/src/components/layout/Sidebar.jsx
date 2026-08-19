import { Link, NavLink, useLocation } from "react-router-dom"
import {
  FiHome, FiUser, FiMapPin, FiHeart, FiClock, FiBell, FiSettings,
  FiDollarSign, FiCalendar, FiAlertTriangle, FiNavigation,
  FiGlobe, FiMessageCircle, FiBookOpen, FiShield, FiKey, FiBriefcase,
  FiPlusCircle, FiCheckSquare, FiCompass, FiX, FiLogIn, FiUserPlus, FiTrendingUp, FiImage,
  FiActivity,
} from "react-icons/fi"

import useAuth from "../../hooks/useAuth"
import { closeSidebar } from "../../hooks/useSidebarState"
import { useI18n } from "../../i18n"

const GROUPS = [
  {
    label: "Explore & Discover", tk: "sidebar.explore",
    links: [
      { to: "/destinations", label: "Destinations", tk: "sidebar.destinations", icon: FiMapPin, color: "forest" },
      { to: "/gallery", label: "Visual Photo Gallery", tk: "sidebar.gallery", icon: FiImage, color: "pink" },
      { to: "/compare", label: "Compare Places", tk: "sidebar.compare", icon: FiTrendingUp, color: "orange" },
      { to: "/discover-nepal", label: "Discover Nepal", tk: "sidebar.discover", icon: FiBookOpen, color: "himalaya" },
      { to: "/packages", label: "Travel Packages", tk: "sidebar.packages", icon: FiBriefcase, color: "orange" },
      { to: "/destinations/submit", label: "Submit Place", tk: "sidebar.submit", icon: FiPlusCircle, color: "saffron" },
      { to: "/submit-service", label: "Submit Hotel / Hospital / Service", icon: FiPlusCircle, color: "emerald" },
      { to: "/explore-map", label: "Explore by Province", tk: "sidebar.explore_map", icon: FiCompass, color: "forest" },
      { to: "/recommendation", label: "AI Recommendations", tk: "sidebar.recommendations", icon: FiHeart, color: "emerald" },
      { to: "/navigation", label: "GTA Navigation HUD", tk: "sidebar.navigation", icon: FiNavigation, color: "sky" },
      { to: "/hotels/search", label: "Hotels & Lodges", tk: "sidebar.hotels", icon: FiKey, color: "saffron" },
    ],
  },
  {
    label: "Planning & Safety", tk: "sidebar.planning",
    links: [
      { to: "/budget-estimator", label: "Budget Estimator", tk: "sidebar.budget", icon: FiDollarSign, color: "orange" },
      { to: "/trip-planner", label: "Interactive Trip Planner", tk: "sidebar.trip_planner", icon: FiCalendar, color: "emerald" },
      { to: "/expenditure", label: "Expenditure History", tk: "sidebar.expenditure", icon: FiDollarSign, color: "emerald" },
      { to: "/itinerary", label: "Itinerary Planner", tk: "sidebar.itinerary", icon: FiCalendar, color: "himalaya" },
      { to: "/risk-alerts", label: "Risk Sentinel", tk: "sidebar.risk", icon: FiAlertTriangle, color: "nepalred" },
      { to: "/family-safety", label: "Family Live Safety", tk: "sidebar.safety", icon: FiShield, color: "emerald" },
      { to: "/emergency", label: "Emergency Hub", tk: "sidebar.emergency", icon: FiAlertTriangle, color: "red" },
      { to: "/language", label: "Nepal Phrasebook", tk: "sidebar.phrasebook", icon: FiGlobe, color: "emerald" },
      { to: "/translation", label: "Live Translation", tk: "sidebar.translation", icon: FiGlobe, color: "cyan" },
      { to: "/chatbot", label: "Himal AI Assistant", tk: "sidebar.chatbot", icon: FiMessageCircle, color: "terracotta" },
    ],
  },
  {
    label: "My Account", tk: "sidebar.account",
    links: [
      { to: "/dashboard", label: "My Dashboard", tk: "sidebar.dashboard", icon: FiHome, color: "himalaya" },
      { to: "/profile", label: "Profile", tk: "sidebar.profile", icon: FiUser, color: "himalaya" },
      { to: "/personal-details", label: "Personal Details", tk: "sidebar.personal_details", icon: FiUser, color: "himalaya" },
      { to: "/favorites", label: "Saved Favorites", tk: "sidebar.favorites", icon: FiHeart, color: "pink" },
      { to: "/my-bookings", label: "My Bookings", tk: "sidebar.bookings", icon: FiBookOpen, color: "emerald" },
      { to: "/my-submissions", label: "My Submissions", tk: "sidebar.submissions", icon: FiCheckSquare, color: "saffron" },
      { to: "/history", label: "Visit History", tk: "sidebar.history", icon: FiClock, color: "stone" },
    ],
  },
  {
    label: "Portals & Control", tk: "sidebar.portals",
    links: [
      { to: "/admin", label: "Admin Central", tk: "sidebar.admin", icon: FiShield, color: "nepalred", roleCheck: "admin" },
      { to: "/admin/diagnostics", label: "Diagnostics Center", tk: "sidebar.diagnostics", icon: FiActivity, color: "terracotta", roleCheck: "admin" },
      { to: "/staff", label: "Staff Operations", tk: "sidebar.staff", icon: FiBriefcase, color: "saffron", roleCheck: "staff" },
      { to: "/local/dashboard", label: "Local Guide Portal", tk: "sidebar.local", icon: FiHome, color: "emerald", roleCheck: "local" },
      { to: "/settings", label: "Settings", tk: "sidebar.settings", icon: FiSettings, color: "stone" },
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
  violet: "text-purple-600 bg-purple-50 group-hover:bg-purple-100",
  purple: "text-purple-600 bg-purple-50 group-hover:bg-purple-100",
  terracotta: "text-orange-700 bg-orange-50 group-hover:bg-orange-100",
  cyan: "text-cyan-600 bg-cyan-50 group-hover:bg-cyan-100",
  stone: "text-gray-600 bg-gray-50 group-hover:bg-gray-100",
}

export default function Sidebar() {
  const { isAuthenticated, user, isAdmin, isLocal } = useAuth()
  const { t } = useI18n()
  const location = useLocation()

  // Close the mobile drawer whenever the route changes.
  const handleNav = () => {
    if (window.innerWidth < 1024) closeSidebar()
  }

  const visibleGroups = GROUPS.map((grp) => ({
    ...grp,
    links: grp.links.filter((link) => {
      if (link.roleCheck === "admin" && !isAdmin) return false
      if (link.roleCheck === "staff" && !isAdmin && user?.role !== "staff") return false
      if (link.roleCheck === "local" && !isLocal && !isAdmin) return false
      return true
    }),
  })).filter((g) => g.links.length > 0)

  return (
    <>
      {/* Mobile backdrop */}
      <div
        onClick={closeSidebar}
        className="fixed inset-0 top-16 bg-black/40 z-30 lg:hidden sidebar-backdrop opacity-0 pointer-events-none transition-opacity duration-300"
        data-sidebar-backdrop="true"
        aria-hidden="true"
      />

      <aside
        className="sidebar-drawer fixed top-16 bottom-0 left-0 z-40 w-64 max-w-[88vw] bg-white border-r border-gray-100 overflow-y-auto overscroll-contain
                   transform -translate-x-full transition-transform duration-300 will-change-transform
                   shadow-xl lg:translate-x-0 lg:shadow-none lg:max-w-none"
        style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
      >
        <div className="p-4 space-y-6">
          <div className="flex items-center justify-between lg:hidden">
            <span className="text-sm font-bold text-gray-900">Menu</span>
            <button
              onClick={closeSidebar}
              className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
              aria-label="Close menu"
            >
              <FiX size={18} />
            </button>
          </div>

          {isAuthenticated ? (
            <div className="p-3.5 rounded-2xl bg-gradient-to-br from-primary-50 to-secondary-50 border border-primary-100 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary-600 text-white font-black flex items-center justify-center text-sm shadow">
                {user?.first_name?.[0] || user?.email[0].toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="font-bold text-xs text-gray-900 truncate">{user?.full_name || user?.email}</p>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-secondary-100 text-secondary-700">
                  {user?.role || "Tourist"}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-2xl bg-gray-50 border border-gray-100 flex gap-2">
              <Link
                to="/login"
                onClick={handleNav}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-primary-600 text-white text-xs font-bold hover:bg-primary-700"
              >
                <FiLogIn size={13} /> Login
              </Link>
              <Link
                to="/register"
                onClick={handleNav}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border border-primary-200 text-primary-700 text-xs font-bold hover:bg-primary-50"
              >
                <FiUserPlus size={13} /> Sign up
              </Link>
            </div>
          )}

          {visibleGroups.map((grp, i) => (
            <div key={i} className="space-y-1.5">
              <p className="text-[11px] font-extrabold text-gray-400 uppercase tracking-wider px-3">
                {grp.tk ? t(grp.tk) : grp.label}
              </p>
              <div className="space-y-0.5">
                {grp.links.map((link, j) => {
                  const Icon = link.icon
                  const colorClass = COLOR_MAP[link.color] || COLOR_MAP.stone
                  return (
                    <NavLink
                      key={j}
                      to={link.to}
                      onClick={handleNav}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all group ${
                          isActive
                            ? "bg-primary-600 text-white shadow-md shadow-primary-900/20"
                            : "text-gray-700 hover:bg-primary-50 hover:text-primary-900"
                        }`
                      }
                    >
                      <div className={`p-1.5 rounded-lg ${colorClass} group-hover:scale-105 transition-transform`}>
                        <Icon size={14} />
                      </div>
                      <span>{link.tk ? t(link.tk) : link.label}</span>
                    </NavLink>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </aside>
    </>
  )
}
