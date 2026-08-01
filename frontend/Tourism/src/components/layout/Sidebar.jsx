import { useState } from "react"
import { NavLink } from "react-router-dom"
import {
  FiHome, FiUser, FiMapPin, FiHeart, FiClock, FiBell, FiSettings,
  FiDollarSign, FiAlertTriangle, FiNavigation, FiSearch, FiGlobe,
  FiMessageCircle, FiBookOpen, FiShield, FiKey, FiChevronDown, FiCompass,
} from "react-icons/fi"
import useAuth from "../../hooks/useAuth"

// FIXED as part of this restructure: every link that existed in the
// previous flat Sidebar is still here, unchanged — this only regroups
// them and adds the new Discover Nepal module (anchor links into
// DiscoverNepal.jsx, see the reasoning there for why it's one hub page
// instead of ~15 separate ones with no backend data behind them).
const GROUPS = [
  {
    label: "Main",
    links: [
      { to: "/dashboard", label: "Dashboard", icon: FiHome },
      { to: "/profile", label: "Profile", icon: FiUser },
      { to: "/destinations", label: "Destinations", icon: FiMapPin },
      { to: "/explore-map", label: "Explore by Province", icon: FiCompass },
      { to: "/recommendation", label: "Recommendations", icon: FiHeart },
      { to: "/nearby-places", label: "Nearby Places", icon: FiMapPin },
      { to: "/hotels/search", label: "Hotels", icon: FiKey },
      { to: "/favorites", label: "Favorites", icon: FiHeart },
      { to: "/my-bookings", label: "My Bookings", icon: FiBookOpen },
      { to: "/history", label: "History", icon: FiClock },
    ],
  },
  {
    label: "Plan & Stay Safe",
    links: [
      { to: "/budget-estimator", label: "Budget Estimator", icon: FiDollarSign },
      { to: "/risk-alerts", label: "Risk Alerts", icon: FiAlertTriangle },
      { to: "/navigation", label: "Navigation", icon: FiNavigation },
      { to: "/language", label: "District Search", icon: FiSearch },
      { to: "/emergency", label: "Emergency", icon: FiAlertTriangle },
      { to: "/translation", label: "Translation", icon: FiGlobe },
      { to: "/chatbot", label: "Himal AI", icon: FiMessageCircle },
    ],
  },
  {
    label: "Discover Nepal",
    links: [
      { to: "/discover-nepal#history", label: "History" },
      { to: "/discover-nepal#culture", label: "Culture" },
      { to: "/discover-nepal#festivals", label: "Festivals" },
      { to: "/discover-nepal#wildlife", label: "Wildlife" },
      { to: "/dashboard#top", label: "National Symbols" },
      { to: "/discover-nepal#unesco", label: "UNESCO Sites" },
      { to: "/discover-nepal#national-parks", label: "National Parks" },
      { to: "/discover-nepal#dress-music-architecture", label: "Traditional Dress" },
      { to: "/discover-nepal#dress-music-architecture", label: "Music & Dance" },
      { to: "/discover-nepal#dress-music-architecture", label: "Architecture" },
      { to: "/discover-nepal#religion-languages", label: "Religion & Languages" },
      { to: "/discover-nepal#ethnic-groups", label: "Ethnic Groups" },
      { to: "/discover-nepal#local-food", label: "Local Food" },
      { to: "/discover-nepal#crafts", label: "Traditional Crafts" },
      { to: "/discover-nepal#mountains", label: "Mountains" },
      { to: "/discover-nepal#provinces", label: "Province Information" },
    ],
  },
  {
    label: "Account",
    links: [
      { to: "/notifications", label: "Notifications", icon: FiBell },
      { to: "/settings", label: "Settings", icon: FiSettings },
    ],
  },
]

const SidebarLink = ({ to, label, icon: Icon }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
        isActive
          ? "bg-himalaya-50 text-himalaya-600"
          : "text-gray-600 hover:bg-gray-50"
      }`
    }
  >
    {Icon ? <Icon size={18} /> : <span className="w-[18px]" />}
    {label}
  </NavLink>
)

const SidebarGroup = ({ label, links, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-600"
      >
        {label}
        <FiChevronDown size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="flex flex-col gap-1">
          {links.map((link) => <SidebarLink key={link.to + link.label} {...link} />)}
        </div>
      )}
    </div>
  )
}

const Sidebar = () => {
  const { isAdmin } = useAuth()

  return (
    <aside className="hidden lg:block w-64 shrink-0 bg-white rounded-xl2 shadow-card p-3 h-fit sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto">
      {/* Small Nepal-themed header touch inside the sidebar itself */}
      <div className="flex items-center gap-2 px-3 py-2 mb-1 text-himalaya-500">
        <FiCompass size={16} />
        <span className="text-xs font-semibold">Explore Nepal</span>
      </div>

      <nav>
        {GROUPS.map((group) => (
          <SidebarGroup key={group.label} label={group.label} links={group.links} />
        ))}

        {/* Admin link — unchanged from before, still conditional on role */}
        {isAdmin && (
          <div className="mt-2 border-t border-gray-100 pt-4 space-y-1">
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  isActive ? "text-nepalred-600" : "text-nepalred-500 hover:bg-nepalred-50"
                }`
              }
            >
              <FiShield size={18} />
              Admin Dashboard
            </NavLink>
            {/* NEW: these two pages existed, fully built, with zero
                routes anywhere — now reachable */}
            <NavLink
              to="/admin/hotel-assignments"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive ? "text-nepalred-600" : "text-gray-500 hover:bg-nepalred-50"
                }`
              }
            >
              <span className="w-[18px]" /> Hotel Assignments
            </NavLink>
            <NavLink
              to="/admin/tasks"
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive ? "text-nepalred-600" : "text-gray-500 hover:bg-nepalred-50"
                }`
              }
            >
              <span className="w-[18px]" /> Admin Tasks
            </NavLink>
          </div>
        )}
      </nav>
    </aside>
  )
}

export default Sidebar