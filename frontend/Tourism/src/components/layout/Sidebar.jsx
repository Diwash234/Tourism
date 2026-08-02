import { useState } from "react"
import { NavLink } from "react-router-dom"
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
} from "react-icons/fi"

import useAuth from "../../hooks/useAuth"

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


const SidebarLink = ({
  to,
  label,
  icon: Icon,
  color = "himalaya",
}) => {

  const classes =
    COLOR_CLASSES[color] || COLOR_CLASSES.himalaya

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? classes.active
            : "text-gray-600 hover:bg-gray-50"
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


const SidebarGroup = ({
  label,
  links,
  defaultOpen = true,
}) => {

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
          className={`transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>


      {open && (
        <div className="flex flex-col gap-1">
          {links.map((link) => (
            <SidebarLink
              key={link.to + link.label}
              {...link}
            />
          ))}
        </div>
      )}

    </div>
  )
}


const Sidebar = () => {

  const { isAdmin } = useAuth()


  return (
    <aside className="hidden lg:block w-64 shrink-0 bg-white rounded-xl2 shadow-card p-3 h-fit sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto">

      <div className="flex items-center gap-2 px-3 py-2 mb-1 text-himalaya-500">
        <FiCompass size={16} />
        <span className="text-xs font-semibold">
          Explore Nepal
        </span>
      </div>


      <nav>

        {GROUPS.map((group) => (
          <SidebarGroup
            key={group.label}
            label={group.label}
            links={group.links}
          />
        ))}


        {isAdmin && (

          <div className="mt-2 border-t border-gray-100 pt-4 space-y-1">

            <NavLink
              to="/admin"
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
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-nepalred-50"
            >
              <span className="w-[18px]" />
              Hotel Assignments
            </NavLink>


            <NavLink
              to="/admin/tasks"
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-nepalred-50"
            >
              <span className="w-[18px]" />
              Admin Tasks
            </NavLink>

          </div>

        )}

      </nav>

    </aside>
  )
}


export default Sidebar