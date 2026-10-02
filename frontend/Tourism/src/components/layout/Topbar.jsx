import { FiPhone, FiAlertCircle, FiArrowRight, FiCheckCircle } from "react-icons/fi"
import { Link } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"
import LanguageSwitcher from "../common/LanguageSwitcher"

export default function Topbar() {
  const { settings } = usePublicConfig()
  const topbar = settings?.topbar

  if (!topbar) {
    return null
  }

  // Check if enabled and published (or fallback published)
  const isPublished = topbar.status ? topbar.status === "published" : true
  const isEnabled = topbar.enabled !== false

  if (!isEnabled || !isPublished) {
    return null
  }

  const helpline = topbar.helpline || "1144 / +977-1-4247041"
  const notice = topbar.notice || "Autumn 2026 Trekking Season Open · Favorable weather across Annapurna & Everest"
  const weather = topbar.weather_summary || "Kathmandu 21°C · Pokhara 23°C · Namche 9°C"
  const emergencyUrl = topbar.emergency_url || "/emergency"
  const emergencyLabel = topbar.emergency_label || "24/7 Tourist Police"

  const handleApplyClick = () => {
    window.dispatchEvent(new CustomEvent("ny-open-admission-modal"))
  }

  return (
    <aside
      aria-label="Official announcements and emergency hotline"
      className="ny-topbar relative z-20 flex min-h-[36px] w-full items-center justify-between border-b border-emerald-900/40 bg-[#06241e] px-2 py-1 text-[11px] sm:text-xs text-[#c7d9d2] transition-colors"
    >
      {/* Left: 24/7 Helpline & Emergency */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <a
          href="tel:1144"
          className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950/80 px-2 py-0.5 text-emerald-300 font-semibold hover:bg-emerald-800/80 hover:text-white transition-colors"
          title="Direct call to Tourist Police 24/7 hotline"
        >
          <FiPhone size={11} className="animate-pulse text-emerald-400" />
          <span>{emergencyLabel}:</span>
          <span className="font-mono text-white">{helpline}</span>
        </a>

        <Link
          to={emergencyUrl}
          className="hidden md:inline-flex items-center gap-1 text-[11px] text-[#A3E635] hover:underline"
        >
          <FiAlertCircle size={11} />
          <span>Safety Hub</span>
        </Link>
      </div>

      {/* Center: Live Seasonal / Weather Notice */}
      <div className="hidden lg:flex items-center gap-2 overflow-hidden px-2 text-center text-emerald-100/90 truncate max-w-xl">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
        <span className="font-medium truncate">{notice}</span>
        <span className="text-white/40">|</span>
        <span className="text-[#a4c7bb] font-mono text-[11px] shrink-0">{weather}</span>
      </div>

      {/* Right: Quick Apply Button & Language Switcher */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={handleApplyClick}
          className="inline-flex items-center gap-1 rounded bg-emerald-600 hover:bg-emerald-500 px-2 py-0.5 text-[11px] font-semibold text-white shadow-sm transition-all"
        >
          <span>{topbar.apply_button_label || "Apply / Inquire"}</span>
          <FiArrowRight size={10} />
        </button>

        {topbar.show_language !== false && (
          <div className="hidden sm:block scale-90 origin-right">
            <LanguageSwitcher />
          </div>
        )}
      </div>
    </aside>
  )
}
