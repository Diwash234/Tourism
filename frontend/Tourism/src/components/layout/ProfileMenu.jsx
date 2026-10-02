import { useEffect, useRef, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { FiChevronDown, FiHeart, FiLogOut, FiSettings, FiUser } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import { useI18n } from "../../i18n"

/**
 * Shared profile dropdown for every role's navbar (brief §15/§36).
 * Click-only (never hover), closes on outside click and Escape, right-aligned
 * so it stays inside the viewport, identity + email live inside the menu
 * instead of permanently in the navbar (brief §14).
 */
export default function ProfileMenu({ variant = "light" }) {
  const { user, logout } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const box = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onDown = (event) => {
      if (!box.current?.contains(event.target)) setOpen(false)
    }
    const onKey = (event) => { if (event.key === "Escape") setOpen(false) }
    document.addEventListener("mousedown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  const handleLogout = async () => {
    setOpen(false)
    await logout()
    navigate("/login")
  }

  const admin = variant === "admin"
  const initial = (user?.first_name?.[0] || user?.email?.[0] || "?").toUpperCase()
  const displayName = user?.full_name || user?.first_name || user?.name || t("nav.profile")

  const itemClass = admin
    ? "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-semibold text-emerald-100 hover:bg-emerald-100 hover:text-emerald-950"
    : "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-slate-700"

  return (
    <div ref={box} className="relative shrink-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Profile menu"
        className={`flex items-center gap-2 rounded-full py-1 pl-1 pr-2 transition-colors ${
          admin
            ? "bg-emerald-800 text-white hover:bg-emerald-700"
            : "border border-gray-200 dark:border-slate-600 hover:shadow-card"
        }`}
      >
        <span className={`grid h-8 w-8 place-items-center rounded-full text-xs font-black text-white ${admin ? "bg-emerald-600" : "bg-nav-active"}`}>
          {initial}
        </span>
        <span className={`hidden max-w-[110px] truncate text-sm font-medium sm:block ${admin ? "text-emerald-50" : "text-gray-700 dark:text-gray-200"}`}>
          {displayName}
        </span>
        <FiChevronDown size={14} className={`transition-transform ${admin ? "text-emerald-200" : "text-gray-400"} ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div
          role="menu"
          className={`absolute right-0 top-full z-[80] mt-2 w-64 rounded-2xl border p-2 shadow-2xl ${
            admin
              ? "border-emerald-200 bg-emerald-950"
              : "border-gray-100 bg-white dark:border-slate-700 dark:bg-slate-800"
          }`}
        >
          <div className="flex items-center gap-3 px-3 py-2">
            <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-black text-white ${admin ? "bg-emerald-600" : "bg-nav-active"}`}>
              {initial}
            </span>
            <div className="min-w-0">
              <p className={`truncate text-sm font-bold ${admin ? "text-white" : "text-gray-900 dark:text-white"}`}>{displayName}</p>
              <p className={`truncate text-xs ${admin ? "text-emerald-200" : "text-gray-500 dark:text-gray-400"}`}>{user?.email}</p>
            </div>
          </div>
          {user?.role && (
            <p className={`mx-3 mb-1 text-[10px] font-black uppercase tracking-wide ${admin ? "text-emerald-300" : "text-gray-400 dark:text-gray-500"}`}>
              {user.role}
            </p>
          )}
          <div className={`my-1 border-t ${admin ? "border-emerald-800" : "border-gray-100 dark:border-slate-700"}`} />
          <Link to="/profile" onClick={() => setOpen(false)} className={itemClass} role="menuitem">
            <FiUser size={15} /> Profile
          </Link>
          <Link to="/favorites" onClick={() => setOpen(false)} className={itemClass} role="menuitem">
            <FiHeart size={15} /> Saved trips
          </Link>
          <Link to="/settings" onClick={() => setOpen(false)} className={itemClass} role="menuitem">
            <FiSettings size={15} /> Account settings
          </Link>
          <div className={`my-1 border-t ${admin ? "border-emerald-800" : "border-gray-100 dark:border-slate-700"}`} />
          <button type="button" onClick={handleLogout} role="menuitem" className={`${itemClass} !text-rose-600 hover:!bg-rose-50 dark:hover:!bg-rose-950/40`}>
            <FiLogOut size={15} /> {t("nav.logout")}
          </button>
        </div>
      )}
    </div>
  )
}
