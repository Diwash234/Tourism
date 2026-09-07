import React, { useState, useEffect, useMemo, useRef } from "react"
import { useNavigate } from "react-router-dom"
import {
  FiMapPin,
  FiNavigation,
  FiHeart,
  FiClock,
  FiSun,
  FiCompass,
  FiShield,
} from "react-icons/fi"
import { placeLocationLabel } from "../../utils/placeUtils"

const FOCAL_CENTER = "center center"

// Legibility scrim: bottom + left navy gradients so text/buttons never sit on
// busy pixels, regardless of the photograph behind them.
const scrim = {
  background: [
    "linear-gradient(to top, rgba(7,12,32,0.96) 0%, rgba(7,12,32,0.72) 45%, rgba(7,12,32,0.28) 78%, rgba(7,12,32,0.10) 100%)",
    "linear-gradient(to right, rgba(7,12,32,0.88) 0%, rgba(7,12,32,0.40) 55%, rgba(7,12,32,0.10) 100%)",
    "radial-gradient(120% 90% at 50% 8%, rgba(7,12,32,0) 55%, rgba(7,12,32,0.45) 100%)",
  ].join(", "),
}

const isHttp = (u) => typeof u === "string" && /^https?:\/\//i.test(u)

export default function DestinationHero({
  destination,
  isFavorite = false,
  onToggleFavorite,
  onOpenReportModal,
  onOpenOfflineKit,
}) {
  const navigate = useNavigate()
  const reduced = useRef(false)

  // Rotate through the destination's own photographs (cover first).
  const bgImages = useMemo(() => {
    if (!destination) return []
    const list = []
    const push = (u) => { if (u && !list.includes(u)) list.push(u) }
    push(destination.cover_image_url || destination.cover_image)
    ;(destination.images || []).forEach((u) => {
      // Only rotate remote, loadable URLs or media paths; skip broken hosts.
      if (isHttp(u) || u.startsWith("/media/")) push(u)
    })
    if (!list.length) push("/images/destinations/kathmandu/durbar-square.jpg")
    return list
  }, [destination])

  const [bgIdx, setBgIdx] = useState(0)
  useEffect(() => {
    reduced.current = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false
  }, [])
  useEffect(() => {
    if (reduced.current || bgImages.length < 2) return
    const t = setInterval(() => setBgIdx((p) => (p + 1) % bgImages.length), 8000)
    return () => clearInterval(t)
  }, [bgImages.length])

  if (!destination) return null

  return (
    <div className="relative w-full min-h-[520px] sm:min-h-[600px] rounded-3xl overflow-hidden shadow-2xl bg-[#070c20] text-white flex flex-col justify-end p-6 sm:p-10 lg:p-12 mb-8">
      {/* Rotating photographic backdrop of this very destination */}
      {bgImages.map((u, i) => (
        <img
          key={u}
          src={u}
          alt={destination.name}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-[1200ms] ease-out ${i === bgIdx ? "opacity-100 kenburns" : "opacity-0"}`}
          style={{ objectPosition: FOCAL_CENTER }}
          loading={i === 0 ? "eager" : "lazy"}
          onError={(e) => { e.currentTarget.style.visibility = "hidden" }}
        />
      ))}

      {/* High-contrast scrim guarantees readable text over any photo */}
      <div className="absolute inset-0" style={scrim} aria-hidden="true" />

      {/* Hero Content Layer */}
      <div className="relative z-10 space-y-4 max-w-4xl">
        {/* Category & Region Pill Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="px-3.5 py-1 rounded-full bg-[#D9C7A3] text-[#0d1330] text-xs font-black uppercase tracking-wider shadow">
            {destination.category_name || destination.category?.name || "Himalayan Destination"}
          </span>
          {destination.province && (
            <span className="px-3 py-1 rounded-full bg-white/15 backdrop-blur text-stone-100 text-xs font-bold border border-white/20">
              📍 {destination.province} Province
            </span>
          )}
          {destination.altitude && (
            <span className="px-3 py-1 rounded-full bg-white/15 backdrop-blur text-amber-300 text-xs font-bold border border-white/20">
              🏔️ {destination.altitude}
            </span>
          )}
        </div>

        {/* Destination Main Title */}
        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-tight break-words" style={{ textShadow: "0 2px 22px rgba(7,12,32,0.7)" }}>
          {destination.name}
        </h1>

        {/* Location Subtitle */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-stone-100 font-medium" style={{ textShadow: "0 1px 10px rgba(7,12,32,0.8)" }}>
          <span className="flex items-center gap-1.5 font-bold text-[#D9C7A3]">
            <FiMapPin className="text-[#D99048]" />
            {placeLocationLabel(destination)}
          </span>
          {destination.district && (
            <>
              <span aria-hidden="true">•</span>
              <span>District: <b className="text-white">{destination.district}</b></span>
            </>
          )}
        </div>

        {/* Short Editorial Abstract */}
        <p className="text-sm sm:text-base text-stone-100/90 leading-relaxed line-clamp-3 max-w-3xl" style={{ textShadow: "0 1px 8px rgba(7,12,32,0.8)" }}>
          {destination.short_description || destination.description || "Discover mountains, ancient heritage, and vibrant local culture in this landmark Nepal destination."}
        </p>

        {/* Quick Travel Metrics Bar */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
          {[
            { label: "Recommended Stay", value: destination.recommended_days ? `${destination.recommended_days} Days` : "Not recorded", icon: FiClock, tint: "text-[#D99048]" },
            { label: "Best Season", value: destination.best_time_to_visit || "Not recorded", icon: FiSun, tint: "text-amber-300" },
            { label: "Distance from Kathmandu", value: destination.distance_from_kathmandu_km != null ? `${destination.distance_from_kathmandu_km} km` : "Not recorded", icon: FiCompass, tint: "text-[#70B1AB]" },
            { label: "Safety & Risk Level", value: destination.risk_analysis?.risk_category || "Moderate", icon: FiShield, tint: "text-emerald-300" },
          ].map(({ label, value, icon: Icon, tint }) => (
            <div key={label} className="p-3 rounded-2xl bg-[#0d1330]/55 backdrop-blur border border-white/15 text-xs">
              <span className="text-[10px] uppercase font-bold text-stone-300 block">{label}</span>
              <span className="text-sm font-black text-white flex items-center gap-1 mt-0.5">
                <Icon className={tint} /> {value}
              </span>
            </div>
          ))}
        </div>

        {/* Action Buttons Row */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-white/15">
          <button
            onClick={() => navigate(`/trip-planner?dest=${encodeURIComponent(destination.slug)}`)}
            className="px-6 py-3.5 rounded-2xl bg-[#D99048] hover:bg-amber-500 text-slate-950 font-black text-sm flex items-center gap-2 shadow-xl shadow-amber-500/25 transition-all hover:scale-[1.03]"
          >
            <FiCompass size={18} /> Plan This Journey
          </button>

          <button
            onClick={() => navigate(`/navigation?dest=${encodeURIComponent(destination.name)}`)}
            className="px-6 py-3.5 rounded-2xl bg-white hover:bg-stone-100 text-slate-950 font-black text-sm flex items-center gap-2 shadow-xl transition-all hover:scale-[1.03]"
          >
            <FiNavigation size={18} className="text-[#0d1330]" /> Get Road Route
          </button>

          {onOpenOfflineKit && (
            <button
              onClick={onOpenOfflineKit}
              className="px-4 py-3.5 rounded-2xl bg-white/15 hover:bg-white/25 text-white font-bold text-xs sm:text-sm border border-white/20 transition-all backdrop-blur"
            >
              🎒 Offline Kit
            </button>
          )}

          {onToggleFavorite && (
            <button
              onClick={onToggleFavorite}
              className={`p-3.5 rounded-2xl border transition-all ${
                isFavorite
                  ? "bg-rose-500 border-rose-400 text-white shadow-lg"
                  : "bg-white/15 hover:bg-white/25 border-white/20 text-white backdrop-blur"
              }`}
              title={isFavorite ? "Remove from Favorites" : "Add to Favorites"}
              aria-pressed={isFavorite}
            >
              <FiHeart size={20} className={isFavorite ? "fill-white" : ""} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
