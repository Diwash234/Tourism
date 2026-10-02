import { useState } from "react"
import { FiVolume2, FiX } from "react-icons/fi"
import usePublicConfig from "../../hooks/usePublicConfig"

export default function ContinuousTicker() {
  const { settings } = usePublicConfig()
  const tickersConfig = settings?.tickers
  const [dismissed, setDismissed] = useState(false)

  const isPublished = tickersConfig?.status ? tickersConfig.status === "published" : true
  const isEnabled = tickersConfig?.enabled !== false

  if (dismissed || !isEnabled || !isPublished) {
    return null
  }

  const items = Array.isArray(tickersConfig?.items) && tickersConfig.items.length > 0
    ? tickersConfig.items
    : [
        "Kathmandu Valley Heritage Festival: Sep 25 – Oct 15, 2026",
        "Annapurna Circuit Route Status: Clear & Open for Autumn Treks",
        "Everest Base Camp Weather: Favorable high visibility conditions",
        "24/7 Tourist Police Helpline: Dial 1144 for nationwide tourist assistance",
      ]

  return (
    <div
      role="region"
      aria-label="Live travel updates and route ticker"
      className="ny-ticker-bar relative z-10 flex w-full items-center overflow-hidden border-b border-emerald-950/40 bg-[#041d18] text-white text-xs font-medium py-1.5 px-3"
    >
      {/* Ticker Label / Icon Badge */}
      <div className="flex items-center gap-1.5 shrink-0 bg-emerald-800/90 text-emerald-100 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mr-3 z-10 shadow-sm">
        <FiVolume2 size={12} className="animate-pulse text-amber-300" />
        <span>Live Updates</span>
      </div>

      {/* Ticker Track */}
      <div className="relative flex-1 overflow-hidden">
        <div className="ticker-track flex whitespace-nowrap gap-8 text-[#d1e7dd] text-[12px]">
          {items.map((item, index) => (
            <span key={`t1-${index}`} className="inline-flex items-center gap-2">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
              <span>{item}</span>
            </span>
          ))}
          {/* Duplicate track for seamless infinite marquee loop */}
          {items.map((item, index) => (
            <span key={`t2-${index}`} className="inline-flex items-center gap-2" aria-hidden="true">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" />
              <span>{item}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Dismiss Button */}
      <button
        type="button"
        onClick={() => setDismissed(true)}
        aria-label="Dismiss live ticker"
        className="p-1 rounded text-[#99bba5] hover:text-white hover:bg-white/10 transition-colors shrink-0 ml-2 z-10"
      >
        <FiX size={13} />
      </button>
    </div>
  )
}
