import { useState } from "react"
import { Link, NavLink } from "react-router-dom"
import {
  FiHome, FiUser, FiMapPin, FiHeart, FiClock, FiBell, FiSettings,
  FiDollarSign, FiCalendar, FiAlertTriangle, FiNavigation, FiSearch,
  FiGlobe, FiMessageCircle, FiBookOpen, FiShield, FiKey, FiBriefcase,
  FiPlusCircle, FiCheckSquare, FiCompass, FiX, FiLogIn, FiUserPlus,
} from "react-icons/fi"
import { AnimatePresence, motion } from "framer-motion"
import useAuth from "../../hooks/useAuth"
import useSidebarState from "../../hooks/useSidebarState"

const GROUPS = [
  {
    label: "Explore & Discover",
    links: [
      { to: "/destinations", label: "Destinations", icon: FiMapPin, color: "forest" },
      { to: "/destinations/submit", label: "Submit Place", icon: FiPlusCircle, color: "himalaya" },
      { to: "/explore-map", label: "Explore by Province", icon: FiCompass, color: "forest" },
      { to: "/recommendation", label: "AI Recommendations", icon: FiHeart, color: "violet" },
      { to: "/navigation", label: "GTA Navigation HUD", icon: FiNavigation, color: "sky" },
      { to: "/hotels/search", label: "Hotels & Lodges", icon: FiKey, color: "saffron" },
    ],
  },
  {
    label: "Planning & Safety",
    links: [
      { to: "/budget-estimator", label: "Budget Estimator", icon: FiDollarSign, color: "orange" },
      { to: "/expenditure", label: "Expenditure History", icon: FiDollarSign, color: "emerald" },
      { to: "/itinerary", label: "Itinerary Planner", icon: FiCalendar, color: "himalaya" },
      { to: "/risk-alerts", label: "Risk Sentinel", icon: FiAlertTriangle, color: "nepalred" },
      { to: "/emergency", label: "Emergency Hub", icon: FiAlertTriangle, color: "red" },
      { to: "/language", label: "Nepal Phrasebook", icon: FiGlobe, color: "purple" },
      { to: "/translation", label: "Live Translation", icon: FiGlobe, color: "cyan" },
      { to: "/chatbot", label: "Himal AI Assistant", icon: FiMessageCircle, color: "violet" },
    ],
  },
  {
    label: "My Account",
    links: [
      { to: "/dashboard", label: "My Dashboard", icon: FiHome, color: "himalaya" },
      { to: "/profile", label: "Profile", icon: FiUser, color: "himalaya" },
      { to: "/favorites", label: "Saved Favorites", icon: FiHeart, color: "pink" },
      { to: "/my-bookings", label: "My Bookings", icon: FiBookOpen, color: "emerald" },
      { to: "/my-submissions", label: "My Submissions", icon: FiCheckSquare, color: "saffron" },
      { to: "/history", label: "Visit History", icon: FiClock, color: "stone" },
    ],
  },
  {
    label: "Portals & Control",
    links: [
      { to: "/admin", label: "Admin Central", icon: FiShield, color: "nepalred", roleCheck: "admin" },
      { to: "/staff", label: "Staff Operations", icon: FiBriefcase, color: "saffron", roleCheck: "staff" },
      { to: "/settings", label: "Settings", icon: FiSettings, color: "stone" },
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
  cyan: "text-cyan-600 bg-cyan-50 group-hover:bg-cyan-100",
  stone: "text-gray-600 bg-gray-50 group-hover:bg-gray-100",
}

export default function Sidebar() {
  const [collapsed, setCollapsed] = useSidebarState()
  const { isAuthenticated, user, isAdmin } = useAuth()

  return (
    <aside
      className={`fixed top-16 bottom-0 left-0 z-40 bg-white border-r border-gray-100 transition-all duration-300 overflow-y-auto ${
        collapsed ? "-translate-x-full lg:translate-x-0 lg:w-0 lg:border-r-0" : "translate-x-0 w-64 shadow-xl lg:shadow-none"
      }`}
    >
      <div className="p-4 space-y-6">
        {/* User Card */}
        {isAuthenticated && (
          <div className="p-3.5 rounded-2xl bg-gradient-to-br from-purple-50 to-rose-50/40 border border-purple-100 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-700 text-white font-black flex items-center justify-center text-sm shadow">
              {user?.first_name?.[0] || user?.email[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="font-bold text-xs text-gray-900 truncate">{user?.full_name || user?.email}</p>
              <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-purple-200/60 text-purple-900">
                {user?.role || "Tourist"}
              </span>
            </div>
          </div>
        )}

        {/* Link Groups */}
        {GROUPS.map((grp, i) => (
          <div key={i} className="space-y-1.5">
            <p className="text-[11px] font-extrabold text-gray-400 uppercase tracking-wider px-3">
              {grp.label}
            </p>
            <div className="space-y-0.5">
              {grp.links.map((link, j) => {
                const Icon = link.icon
                const colorClass = COLOR_MAP[link.color] || COLOR_MAP.stone
                return (
                  <NavLink
                    key={j}
                    to={link.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all group ${
                        isActive
                          ? "bg-purple-700 text-white shadow-md shadow-purple-900/20"
                          : "text-gray-700 hover:bg-purple-50 hover:text-purple-900"
                      }`
                    }
                  >
                    <div className={`p-1.5 rounded-lg ${colorClass} group-hover:scale-105 transition-transform`}>
                      <Icon size={14} />
                    </div>
                    <span>{link.label}</span>
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
