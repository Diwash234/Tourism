import { useEffect, useState } from "react"
import { Link, NavLink, Outlet } from "react-router-dom"
import { FiBriefcase, FiDollarSign, FiFileText, FiHome, FiImage, FiMenu, FiMessageSquare, FiShield, FiStar, FiX } from "react-icons/fi"
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
  { to: "/staff/content", label: "Content Drafts", icon: FiFileText, module: "content" },
  { to: "/staff/feedback", label: "Feedback Queue", icon: FiMessageSquare, module: "feedback" },
]

export default function StaffLayout() {
  const [open, setOpen] = useState(false)
  const [caps, setCaps] = useState({ dashboard: ["view"] })
  const [districts, setDistricts] = useState([])
  const { user } = useAuth()
  useEffect(() => { userApi.getCapabilities().then(({ data }) => { setCaps(data.capabilities || {}); setDistricts(data.managed_districts || []) }).catch(() => {}) }, [])
  const allowed = module => module === "dashboard" || caps[module]?.includes("view") || caps[module]?.includes("*")
  return <div className="min-h-screen bg-slate-100">
    <header className="fixed top-0 inset-x-0 z-50 h-16 bg-white border-b flex items-center px-4 gap-3"><button onClick={() => setOpen(!open)} className="lg:hidden p-2"><FiMenu/></button><b className="text-purple-800">Digital Nepal Staff Operations</b><span className="ml-auto text-xs text-gray-500 hidden sm:inline">{user?.email}</span><Link to="/" className="text-xs bg-emerald-700 text-white px-3 py-2 rounded-lg">User Dashboard</Link></header>
    <aside className={`fixed top-16 bottom-0 left-0 z-40 w-64 bg-slate-950 p-4 transition-transform overflow-y-auto ${open ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}><div className="flex justify-between text-white mb-3"><span className="font-black">Assigned Workspace</span><button onClick={() => setOpen(false)} className="lg:hidden"><FiX/></button></div>{districts.length > 0 && <p className="text-[10px] text-amber-300 bg-slate-900 rounded-lg p-2 mb-3">District scope: {districts.join(", ")}</p>}{items.filter(item => allowed(item.module)).map(({ to, label, icon: Icon, module, end }) => <NavLink end={end} key={module} to={to} onClick={() => setOpen(false)} className={({ isActive }) => `flex gap-3 items-center px-3 py-3 rounded-xl text-sm mb-1 ${isActive ? "bg-purple-600 text-white" : "text-slate-300 hover:bg-slate-800"}`}><Icon/>{label}</NavLink>)}<p className="text-[10px] text-slate-500 mt-6">Queues are generated from backend capabilities, district scope, hotel assignments, and personal task assignments.</p></aside>
    {open && <button className="fixed inset-0 top-16 bg-black/50 z-30 lg:hidden" onClick={() => setOpen(false)}/>}<main className="pt-16 lg:pl-64"><div className="p-3 sm:p-6"><Outlet/></div></main>
  </div>
}
