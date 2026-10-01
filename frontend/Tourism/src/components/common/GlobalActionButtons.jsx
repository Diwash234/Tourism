import { FiEdit3, FiPhoneCall } from "react-icons/fi"
import { useNavigate, useLocation } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"

export default function GlobalActionButtons() {
  const { settings } = usePublicConfig()
  const actionsConfig = settings?.action_buttons
  const navigate = useNavigate()
  const location = useLocation()

  // Hide on auth, admin, and chat pages to prevent clashing with primary tools
  if (
    location.pathname.startsWith("/admin") ||
    location.pathname.startsWith("/staff") ||
    location.pathname.startsWith("/login") ||
    location.pathname.startsWith("/register")
  ) {
    return null
  }

  const isPublished = actionsConfig?.status ? actionsConfig.status === "published" : true
  const isEnabled = actionsConfig?.enabled !== false

  if (!isEnabled || !isPublished) {
    return null
  }

  const primaryLabel = actionsConfig.primary_label || "Apply / Inquire Now"
  const primaryAction = actionsConfig.primary_action || "open_modal"
  const primaryUrl = actionsConfig.primary_url || "/trip"

  const handlePrimaryClick = () => {
    if (primaryAction === "open_modal") {
      window.dispatchEvent(new CustomEvent("ny-open-admission-modal"))
    } else {
      navigate(primaryUrl)
    }
  }

  return (
    <div className="ny-global-action-buttons fixed bottom-6 left-6 z-40 hidden sm:flex items-center gap-2">
      <button
        type="button"
        onClick={handlePrimaryClick}
        className="group flex items-center gap-2 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 text-xs font-bold shadow-lg shadow-emerald-950/30 transition-all hover:scale-105"
        title="Open travel inquiry and admission request"
      >
        <FiEdit3 size={15} className="group-hover:rotate-12 transition-transform" />
        <span>{primaryLabel}</span>
      </button>

      {actionsConfig.floating_sos && (
        <a
          href="tel:1144"
          className="flex items-center gap-1.5 rounded-full bg-rose-700 hover:bg-rose-600 text-white px-3 py-2.5 text-xs font-bold shadow-lg shadow-rose-950/30 transition-all hover:scale-105"
          title="Tourist Police 24/7 Hotline: 1144"
        >
          <FiPhoneCall size={14} className="animate-bounce" />
          <span className="hidden md:inline">1144 SOS</span>
        </a>
      )}
    </div>
  )
}
