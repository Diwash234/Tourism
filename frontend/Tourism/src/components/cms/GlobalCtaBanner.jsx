import { FiArrowRight, FiShield, FiCompass } from "react-icons/fi"
import { Link } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"

export default function GlobalCtaBanner({ className = "" }) {
  const { settings } = usePublicConfig()
  const cta = settings?.cta_banners

  const isPublished = cta?.status ? cta.status === "published" : true
  const isEnabled = cta?.enabled !== false

  if (!isEnabled || !isPublished) {
    return null
  }

  const badge = cta.badge || "Autumn 2026 Season"
  const title = cta.title || "Experience Nepal Beyond the Beaten Path"
  const subtitle = cta.subtitle || "Discover 6,700+ verified destinations, certified mountain guides, and real-time safety tracking across all 7 provinces."
  const buttonText = cta.button_text || "Plan Your Expedition"
  const buttonUrl = cta.button_url || "/itinerary"
  const secondaryText = cta.secondary_text || "Emergency Hub"
  const secondaryUrl = cta.secondary_url || "/emergency"

  const handlePrimaryClick = (e) => {
    if (buttonUrl.startsWith("#") || buttonUrl === "open_modal" || cta.open_modal) {
      e.preventDefault()
      window.dispatchEvent(new CustomEvent("ny-open-admission-modal"))
    }
  }

  return (
    <section className={`ny-global-cta-banner container-app py-8 ${className}`}>
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#052b24] via-[#093f35] to-[#041d18] p-6 sm:p-10 text-white shadow-xl border border-emerald-800/40">
        {/* Subtle decorative background circles */}
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-emerald-400/10 blur-3xl" />

        <div className="relative z-10 max-w-3xl">
          {badge && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300 border border-emerald-500/30 mb-3">
              <FiCompass className="animate-spin text-emerald-400" style={{ animationDuration: "12s" }} />
              {badge}
            </span>
          )}

          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-white mb-3">
            {title}
          </h2>

          <p className="text-sm sm:text-base text-emerald-100/80 leading-relaxed mb-6 max-w-2xl">
            {subtitle}
          </p>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to={buttonUrl}
              onClick={handlePrimaryClick}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 px-5 py-3 text-sm font-bold text-gray-950 shadow-lg shadow-emerald-900/30 transition-all hover:scale-[1.02]"
            >
              <span>{buttonText}</span>
              <FiArrowRight size={16} />
            </Link>

            {secondaryText && (
              <Link
                to={secondaryUrl}
                className="inline-flex items-center gap-2 rounded-xl bg-white/10 hover:bg-white/15 px-4 py-3 text-sm font-semibold text-white border border-white/15 transition-all"
              >
                <FiShield size={15} className="text-emerald-300" />
                <span>{secondaryText}</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
