import { useState, useEffect } from "react"
import { Link, NavLink, useLocation } from "react-router-dom"
import {
  FiHome,
  FiUser,
  FiMapPin,
  FiHeart,
  FiClock,
  FiBell,
  FiSettings,
  FiDollarSign,
  FiAlertTriangle,
  FiNavigation,
  FiSearch,
  FiGlobe,
  FiMessageCircle,
  FiBookOpen,
  FiShield,
  FiKey,
  FiChevronDown,
  FiCompass,
  FiX,
  FiLogIn,
  FiUserPlus,
} from "react-icons/fi"
import { AnimatePresence, motion } from "framer-motion"

import useAuth from "../../hooks/useAuth"
import useSidebarState from "../../hooks/useSidebarState"

const GROUPS = [
  {
    label: "Main",
    links: [
      { to: "/dashboard", label: "Dashboard", icon: FiHome, color: "himalaya" },
      { to: "/profile", label: "Profile", icon: FiUser, color: "himalaya" },
      { to: "/destinations", label: "Destinations", icon: FiMapPin, color: "forest" },
      { to: "/explore-map", label: "Explore by Province", icon: FiCompass, color: "forest" },
      { to: "/recommendation", label: "Recommendations", icon: FiHeart, color: "violet" },
      { to: "/nearby-places", label: "Nearby Places", icon: FiMapPin, color: "forest" },
      { to: "/hotels/search", label: "Hotels", icon: FiKey, color: "saffron" },
      { to: "/favorites", label: "Favorites", icon: FiHeart, color: "pink" },
      { to: "/my-bookings", label: "My Bookings", icon: FiBookOpen, color: "emerald" },
      { to: "/history", label: "History", icon: FiClock, color: "stone" },
    ],
  },
  {
    label: "Plan & Stay Safe",
    links: [
      {
        to: "/budget-estimator",
        label: "Budget Estimator",
        icon: FiDollarSign,
        color: "orange",
      },
      {
        to: "/risk-alerts",
        label: "Risk Alerts",
        icon: FiAlertTriangle,
        color: "nepalred",
      },
      {
        to: "/navigation",
        label: "Navigation",
        icon: FiNavigation,
        color: "sky",
      },
      {
        to: "/language",
        label: "District Search",
        icon: FiSearch,
        color: "purple",
      },
      {
        to: "/emergency",
        label: "Emergency",
        icon: FiAlertTriangle,
        color: "red",
      },
      {
        to: "/translation",
        label: "Translation",
        icon: FiGlobe,
        color: "cyan",
      },
      {
        to: "/chatbot",
        label: "Himal AI",
        icon: FiMessageCircle,
        color: "violet",
      },
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
      {
        to: "/discover-nepal#dress-music-architecture",
        label: "Traditional Dress",
      },
      {
        to: "/discover-nepal#dress-music-architecture",
        label: "Music & Dance",
      },
      {
        to: "/discover-nepal#dress-music-architecture",
        label: "Architecture",
      },
      {
        to: "/discover-nepal#religion-languages",
        label: "Religion & Languages",
      },
      {
        to: "/discover-nepal#ethnic-groups",
        label: "Ethnic Groups",
      },
      {
        to: "/discover-nepal#local-food",
        label: "Local Food",
      },
      {
        to: "/discover-nepal#crafts",
        label: "Traditional Crafts",
      },
      {
        to: "/discover-nepal#mountains",
        label: "Mountains",
      },
      {
        to: "/discover-nepal#provinces",
        label: "Province Information",
      },
    ],
  },
  {
    label: "Account",
    links: [
      {
        to: "/notifications",
        label: "Notifications",
        icon: FiBell,
        color: "amber",
      },
      {
        to: "/settings",
        label: "Settings",
        icon: FiSettings,
        color: "slate",
      },
    ],
  },
]

const COLOR_CLASSES = {
  himalaya: {
    active: "bg-himalaya-50 text-himalaya-600",
    icon: "text-himalaya-500",
  },
  forest: {
    active: "bg-forest-50 text-forest-600",
    icon: "text-forest-500",
  },
  saffron: {
    active: "bg-saffron-50 text-saffron-600",
    icon: "text-saffron-500",
  },
  nepalred: {
    active: "bg-nepalred-50 text-nepalred-600",
    icon: "text-nepalred-500",
  },
  violet: {
    active: "bg-violet-50 text-violet-600",
    icon: "text-violet-500",
  },
  pink: {
    active: "bg-pink-50 text-pink-600",
    icon: "text-pink-500",
  },
  emerald: {
    active: "bg-emerald-50 text-emerald-600",
    icon: "text-emerald-500",
  },
  stone: {
    active: "bg-stone-100 text-stone-600",
    icon: "text-stone-500",
  },
  orange: {
    active: "bg-orange-50 text-orange-600",
    icon: "text-orange-500",
  },
  sky: {
    active: "bg-sky-50 text-sky-600",
    icon: "text-sky-500",
  },
  purple: {
    active: "bg-purple-50 text-purple-600",
    icon: "text-purple-500",
  },
  red: {
    active: "bg-red-50 text-red-600",
    icon: "text-red-500",
  },
  cyan: {
    active: "bg-cyan-50 text-cyan-600",
    icon: "text-cyan-500",
  },
  amber: {
    active: "bg-amber-50 text-amber-600",
    icon: "text-amber-500",
  },
  slate: {
    active: "bg-slate-100 text-slate-600",
    icon: "text-slate-500",
  },
}

const SidebarLink = ({ to, label, icon: Icon, color = "himalaya", onClick }) => {
  const classes = COLOR_CLASSES[color] || COLOR_CLASSES.himalaya
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
          isActive ? classes.active : "text-gray-600 hover:bg-gray-50"
        }`
      }
    >
      {({ isActive }) => (
        <>
          {Icon ? (
            <Icon
              size={18}
              className={
                isActive
                  ? classes.active.split(" ")[1]
                  : classes.icon
              }
            />
          ) : (
            <span className="w-[18px]" />
          )}
          {label}
        </>
      )}
    </NavLink>
  )
}

const SidebarGroup = ({ label, links, defaultOpen = true, onLinkClick }) => {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-600"
      >
        {label}
        <FiChevronDown
          size={14}
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="flex flex-col gap-1">
          {links.map((link) => (
            <SidebarLink
              key={link.to + link.label}
              {...link}
              onClick={onLinkClick}
            />
          ))}
        </div>
      )}
    </div>
  )
}

const SidebarBody = ({ onLinkClick }) => {
  const { isAdmin, isAuthenticated } = useAuth()
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 mb-1 text-himalaya-500 shrink-0">
        <FiCompass size={16} />
        <span className="text-xs font-semibold">
          Explore Nepal
        </span>
      </div>

      <nav className="flex-1 overflow-y-auto pr-1 -mr-1 pb-3">
        {GROUPS.map((group) => (
          <SidebarGroup
            key={group.label}
            label={group.label}
            links={group.links}
            onLinkClick={onLinkClick}
          />
        ))}

        {isAdmin && (
          <div className="mt-2 border-t border-gray-100 pt-4 space-y-1">
            <NavLink
              to="/admin"
              onClick={onLinkClick}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold ${
                  isActive
                    ? "text-nepalred-600"
                    : "text-nepalred-500 hover:bg-nepalred-50"
                }`
              }
            >
              <FiShield size={18}/>
              Admin Dashboard
            </NavLink>

            <NavLink
              to="/admin/hotel-assignments"
              onClick={onLinkClick}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-nepalred-50"
            >
              <span className="w-[18px]" />
              Hotel Assignments
            </NavLink>

            <NavLink
              to="/admin/tasks"
              onClick={onLinkClick}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-nepalred-50"
            >
              <span className="w-[18px]" />
              Admin Tasks
            </NavLink>
          </div>
        )}

        {!isAuthenticated && (
          <div className="mt-2 border-t border-gray-100 pt-4 space-y-2">
            <p className="px-3 text-xs font-semibold uppercase tracking-wide text-gray-400">
              Guest
            </p>
            <Link
              to="/login"
              onClick={onLinkClick}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-himalaya-50 hover:text-himalaya-600"
            >
              <FiLogIn size={18} className="text-himalaya-500" />
              Log In
            </Link>
            <Link
              to="/register"
              onClick={onLinkClick}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-forest-50 hover:text-forest-600"
            >
              <FiUserPlus size={18} className="text-forest-500" />
              Create Account
            </Link>
          </div>
        )}
      </nav>
    </div>
  )
}

const Sidebar = () => {
  const location = useLocation()
  const [drawerOpen, setDrawerOpen] = useSidebarState()

  useEffect(() => {
    if (drawerOpen) setDrawerOpen(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

  const closeDrawer = () => setDrawerOpen(false)

  return (
    <>
      {/* Desktop: fixed left sidebar (never scrolls away, always at corner) */}
      <aside
        className="
          hidden lg:flex
          fixed left-0 top-16 z-40
          w-60 xl:w-64
          h-[calc(100vh-4rem)]
          bg-white border-r border-gray-100 shadow-sm
          p-2 sm:p-3
          overflow-hidden
        "
      >
        <div className="w-full h-full">
          <SidebarBody />
        </div>
      </aside>

      {/* Mobile / minimized: slide-in drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              key="sidebar-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/40 lg:hidden"
              onClick={closeDrawer}
              aria-hidden="true"
            />
            <motion.aside
              key="sidebar-drawer"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "tween", duration: 0.25, ease: "easeOut" }}
              className="
                fixed left-0 top-16 z-50
                w-72 sm:w-80 max-w-[86vw]
                h-[calc(100vh-4rem)]
                bg-white border-r border-gray-200 shadow-xl
                p-3
                overflow-hidden
                lg:hidden
              "
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                  Menu
                </span>
                <button
                  onClick={closeDrawer}
                  className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-800"
                  aria-label="Close sidebar"
                >
                  <FiX size={18} />
                </button>
              </div>
              <div className="w-full h-[calc(100%-2rem)]">
                <SidebarBody onLinkClick={closeDrawer} />
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

export default Sidebar
