import { useEffect, useState } from "react"
import { Link, NavLink, Outlet } from "react-router-dom"
import { FiBriefcase, FiCalendar, FiCoffee, FiDollarSign, FiFileText, FiHome, FiImage, FiLogOut, FiMenu, FiMessageSquare, FiShield, FiStar, FiTruck, FiX } from "react-icons/fi"
import userApi from "../../api/userApi"
import useAuth from "../../hooks/useAuth"

const items = [
  { to: "/staff", label: "Operations Dashboard", icon: FiHome, module: "dashboard", end: true },
  { to: "/staff/destinations", label: "Destination Queue", icon: FiBriefcase, module: "destinations" },
  { to: "/staff/images", label: "Image Review", icon: FiImage, module: "images" },
  { to: "/staff/budget", label: "Budget Surveys", icon: FiDollarSign, module: "budget" },
  { to: "/staff/safety", label: "Safety Reports", icon: FiShield, module: "safety" },
  { to: "/staff/reviews", label: "Review Queue", icon: FiStar, module: "reviews" },
  { to: "/staff/hotels", label: "Assigned Hotels", icon: FiHome, module: "hotels" },
  { to: "/staff/restaurants", label: "Restaurant Queue", icon: FiCoffee, module: "restaurants" },
  { to: "/staff/transportation", label: "Transport Routes", icon: FiTruck, module: "transportation" },
  { to: "/staff/travel-plans", label: "Travel Plans", icon: FiCalendar, module: "travel_plans" },
  { to: "/staff/content", label: "Content Drafts", icon: FiFileText, module: "content" },
  { to: "/staff/feedback", label: "Feedback Queue", icon: FiMessageSquare, module: "feedback" },
]

export default function StaffLayout() {
  const [open, setOpen] = useState(false)
  const [caps, setCaps] = useState({ dashboard: ["view"] })
  const [districts, setDistricts] = useState([])
  const { user, logout } = useAuth()

  useEffect(() => {
    userApi.getCapabilities()
      .then(({ data }) => {
        setCaps(data.capabilities || {})
        setDistricts(data.managed_districts || [])
      })
      .catch(() => {})
  }, [])

  const allowed = (module) =>
    module === "dashboard" || caps[module]?.includes("view") || caps[module]?.includes("*")

  return (
    <div className="staff-amber-theme min-h-screen bg-amber-50">
      <a href="#staff-main" className="admin-skip-link">Skip to staff content</a>
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center gap-3 border-b border-amber-300 bg-amber-500 px-4 text-amber-950 shadow-sm">
        <button onClick={() => setOpen(!open)} className="p-2 lg:hidden" aria-label="Open staff navigation">
          <FiMenu />
        </button>
        <FiBriefcase className="hidden sm:block" />
        <b>Digital Nepal Staff Operations</b>
        <span className="ml-auto hidden rounded-full bg-amber-800 px-2 py-1 text-[10px] font-black uppercase tracking-wide text-amber-100 sm:inline">Staff</span>
        <span className="hidden text-xs text-amber-950 sm:inline">{user?.email}</span>
        <Link to="/" className="rounded-lg bg-white px-3 py-2 text-xs font-bold text-amber-900">Traveller site</Link>
        <button onClick={logout} className="rounded-lg bg-rose-700 p-2 text-white" aria-label="Log out">
          <FiLogOut />
        </button>
      </header>
      <aside
        aria-label="Staff workspace navigation"
        className={`fixed bottom-0 left-0 top-16 z-40 w-64 overflow-y-auto bg-amber-950 p-4 text-amber-50 transition-transform ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <div className="mb-3 flex justify-between text-white">
          <span className="font-black">Assigned Workspace</span>
          <button onClick={() => setOpen(false)} className="lg:hidden" aria-label="Close staff navigation">
            <FiX />
          </button>
        </div>
        {districts.length > 0 && (
          <p className="mb-3 rounded-lg bg-amber-900 p-2 text-[10px] text-amber-200">
            District scope: {districts.join(", ")}
          </p>
        )}
        {items.filter((item) => allowed(item.module)).map(({ to, label, icon: Icon, module, end }) => (
          <NavLink
            end={end}
            key={module}
            to={to}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `mb-1 flex items-center gap-3 rounded-xl px-3 py-3 text-sm ${
                isActive ? "bg-amber-400 font-black text-amber-950" : "text-amber-100 hover:bg-amber-900"
              }`
            }
          >
            <Icon />
            {label}
          </NavLink>
        ))}
        <p className="mt-6 text-[10px] text-amber-300">
          Queues come from your assigned capabilities, districts, hotels and tasks. CMS, users and analytics stay in Admin.
        </p>
      </aside>
      {open && <button className="fixed inset-0 top-16 z-30 bg-black/50 lg:hidden" onClick={() => setOpen(false)} aria-label="Close overlay" />}
      <main id="staff-main" tabIndex="-1" className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-white pt-16 lg:pl-64">
        <div className="p-3 sm:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
