import { NavLink } from "react-router-dom"
import { BsHouseDoor, BsGeoAlt, BsCalendar3, BsHeart, BsPerson } from "react-icons/bs"
import useAuth from "../../hooks/useAuth"

export default function MobileBottomNav() {
  const { isAuthenticated } = useAuth()

  const navItems = [
    { to: isAuthenticated ? "/dashboard" : "/", label: "Home", icon: BsHouseDoor },
    { to: "/destinations", label: "Explore", icon: BsGeoAlt },
    { to: "/trip-planner", label: "My Trip", icon: BsCalendar3 },
    { to: "/favorites", label: "Saved", icon: BsHeart },
    { to: isAuthenticated ? "/profile" : "/login", label: "Profile", icon: BsPerson },
  ]

  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-slate-950/95 backdrop-blur border-t border-emerald-500/30 text-slate-300 px-2 py-1.5 shadow-2xl flex items-center justify-around">
      {navItems.map((item) => {
        const Icon = item.icon
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center py-1 px-3 rounded-xl transition-all ${
                isActive
                  ? "text-emerald-400 font-extrabold scale-105"
                  : "text-slate-400 hover:text-slate-200"
              }`
            }
          >
            <Icon size={18} />
            <span className="text-[10px] mt-0.5 tracking-tight">{item.label}</span>
          </NavLink>
        )
      })}
    </nav>
  )
}
