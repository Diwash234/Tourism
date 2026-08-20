import { useState } from "react"
import { Link, Outlet, useLocation } from "react-router-dom"
import { FiActivity, FiChevronDown, FiChevronRight, FiLogOut, FiMenu, FiShield, FiUsers, FiX } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import AdminGlobalSearch from "./AdminGlobalSearch"
import { ADMIN_NAV_GROUPS, ADMIN_PRIMARY_NAV, adminSectionHref, findAdminSection } from "./adminNavigation"

export default function AdminLayout() {
  const [open, setOpen] = useState(false)
  const [expanded, setExpanded] = useState(
    Object.fromEntries(ADMIN_NAV_GROUPS.map((group, index) => [group.label, index < 3]))
  )
  const { user, logout } = useAuth()
  const location = useLocation()
  const activeSection = new URLSearchParams(location.search).get("section") || "overview"
  const closeMobile = () => {
    if (typeof window !== "undefined" && window.innerWidth < 1024) setOpen(false)
  }

  return (
    <div className="admin-green-theme min-h-screen bg-emerald-50 text-slate-900">
      <a href="#admin-main" className="admin-skip-link">Skip to admin content</a>
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center gap-3 border-b border-emerald-800 bg-emerald-950 px-3 text-white shadow-sm sm:px-5">
        <button
          onClick={() => setOpen((value) => !value)}
          className="admin-icon-button !bg-emerald-800 !text-white"
          aria-label={open ? "Close admin navigation" : "Open admin navigation"}
          aria-expanded={open}
          aria-controls="admin-navigation"
        >
          <FiMenu />
        </button>
        <div className="hidden whitespace-nowrap font-black md:block">
          <span className="text-emerald-300">Digital Nepal</span> Administrator
        </div>
        <nav aria-label="Priority admin navigation" className="hidden items-center gap-1 xl:flex">
          {ADMIN_PRIMARY_NAV.map((section) => {
            const item = findAdminSection(section)
            if (!item) return null
            const Icon = item[2]
            return (
              <Link
                key={section}
                to={adminSectionHref(section)}
                className={`flex items-center gap-1 rounded-lg px-2.5 py-2 text-xs font-bold ${
                  activeSection === section ? "bg-white text-emerald-950" : "text-emerald-100 hover:bg-emerald-800"
                }`}
              >
                <Icon />
                {item[1]}
              </Link>
            )
          })}
        </nav>
        <AdminGlobalSearch />
        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className="hidden rounded-full bg-emerald-800 px-2 py-1 font-black uppercase tracking-wide text-emerald-200 sm:inline">Admin</span>
          <span className="hidden text-emerald-100 sm:inline">{user?.email}</span>
          <Link to="/" className="min-h-10 rounded-lg bg-white px-3 py-2 font-bold text-emerald-950">Traveller site</Link>
          <button onClick={logout} className="admin-icon-button !bg-rose-700 !text-white" aria-label="Log out">
            <FiLogOut />
          </button>
        </div>
      </header>

      <aside
        id="admin-navigation"
        aria-label="Admin navigation"
        className={`fixed bottom-0 top-16 z-40 w-80 max-w-[90vw] overflow-y-auto overscroll-contain border-r border-emerald-900 bg-emerald-950 text-emerald-50 shadow-lg transition-transform ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <nav className="p-4">
          <div className="mb-4 rounded-xl bg-emerald-900 p-3 text-white">
            <FiShield className="inline text-emerald-300" /> <b>Administrator workspace</b>
            <p className="mt-1 text-xs text-emerald-200">CMS, media, users, analytics and safety</p>
          </div>
          {ADMIN_NAV_GROUPS.map((group) => (
            <section key={group.label} className="mb-2">
              <button
                onClick={() => setExpanded((value) => ({ ...value, [group.label]: !value[group.label] }))}
                className="flex min-h-10 w-full items-center justify-between py-2 text-xs font-black uppercase tracking-widest text-emerald-300"
                aria-expanded={expanded[group.label]}
              >
                {group.label}
                {expanded[group.label] ? <FiChevronDown /> : <FiChevronRight />}
              </button>
              {expanded[group.label] && (
                <div className="space-y-1 border-l-2 border-emerald-800 pl-2">
                  {group.items.map(([section, label, Icon]) => (
                    <Link
                      key={section}
                      to={adminSectionHref(section)}
                      onClick={closeMobile}
                      aria-current={activeSection === section ? "page" : undefined}
                      className={`flex min-h-10 items-center gap-3 rounded-xl px-3 py-2 text-sm ${
                        activeSection === section
                          ? "bg-white font-black text-emerald-950 shadow-sm"
                          : "text-emerald-100 hover:bg-emerald-900 hover:text-white"
                      }`}
                    >
                      <Icon aria-hidden="true" />
                      {label}
                    </Link>
                  ))}
                </div>
              )}
            </section>
          ))}
          <section className="mt-4 border-t border-emerald-800 pt-4">
            <p className="mb-2 text-xs font-black uppercase text-emerald-300">Dedicated tools</p>
            <Link to="/admin/diagnostics" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-900">
              <FiActivity /> Audit & Diagnostics
            </Link>
            <Link to="/admin/hotel-assignments" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-900">
              <FiShield /> Hotel Assignments
            </Link>
            <Link to="/admin/tasks" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-900">
              <FiUsers /> Staff Tasks
            </Link>
          </section>
        </nav>
      </aside>
      {open && (
        <button onClick={() => setOpen(false)} className="fixed inset-0 top-16 z-30 bg-black/45 lg:hidden" aria-label="Close admin navigation overlay">
          <FiX className="sr-only" />
        </button>
      )}
      <main id="admin-main" tabIndex="-1" className="min-h-screen bg-gradient-to-br from-white via-emerald-50 to-green-100 pt-16 lg:pl-80">
        <div className="p-3 sm:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
