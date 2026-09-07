import React from "react"
import { useNavigate } from "react-router-dom"
import {
  FiMapPin,
  FiNavigation,
  FiHeart,
  FiClock,
  FiSun,
  FiCompass,
  FiShare2,
  FiShield
} from "react-icons/fi"
import { placeLocationLabel } from "../../utils/placeUtils"

export default function DestinationHero({
  destination,
  isFavorite = false,
  onToggleFavorite,
  onOpenReportModal,
  onOpenOfflineKit,
}) {
  const navigate = useNavigate()

  if (!destination) return null

  // Ensure high-contrast gradient overlay over the image
  const coverUrl = destination.cover_image_url || destination.cover_image || destination.external_image_url || "/images/destinations/kathmandu/durbar-square.jpg"

  return (
    <div className="relative w-full min-h-[500px] sm:min-h-[580px] rounded-3xl overflow-hidden shadow-2xl bg-[#102A2E] text-white flex flex-col justify-end p-6 sm:p-10 lg:p-12 mb-8 group">
      {/* Background Hero Image */}
      <img
        src={coverUrl}
        alt={destination.name}
        className="absolute inset-0 w-full h-full object-cover object-center transform group-hover:scale-105 transition-transform duration-700 ease-out"
      />

      {/* Accessible Dark Gradient Protection Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-[#102A2E]/60 to-transparent opacity-95" />
      <div className="absolute inset-0 bg-gradient-to-r from-[#102A2E]/80 via-transparent to-transparent opacity-80" />

      {/* Hero Content Layer */}
      <div className="relative z-10 space-y-4 max-w-4xl">
        {/* Category & Region Pill Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="px-3.5 py-1 rounded-full bg-[#D9C7A3] text-[#102A2E] text-xs font-black uppercase tracking-wider shadow">
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
        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight drop-shadow-md leading-tight">
          {destination.name}
        </h1>

        {/* Location Subtitle */}
        <div className="flex flex-wrap items-center gap-3 text-sm text-stone-200 font-medium">
          <span className="flex items-center gap-1.5 font-bold text-[#D9C7A3]">
            <FiMapPin className="text-[#D99048]" />
            {placeLocationLabel(destination)}
          </span>
          {destination.district && (
            <>
              <span>•</span>
              <span>District: <b className="text-white">{destination.district}</b></span>
            </>
          )}
          {destination.aliases && (
            <>
              <span>•</span>
              <span className="italic text-stone-300">"{destination.aliases}"</span>
            </>
          )}
        </div>

        {/* Short Editorial Abstract */}
        <p className="text-sm sm:text-base text-stone-200/90 leading-relaxed line-clamp-3 max-w-3xl">
          {destination.short_description || destination.description || "Discover mountains, ancient heritage, and vibrant local culture in this landmark Nepal destination."}
        </p>

        {/* Quick Travel Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3 rounded-2xl bg-white/10 backdrop-blur border border-white/15 text-xs">
            <span className="text-[10px] uppercase font-bold text-stone-300 block">Recommended Stay</span>
            <span className="text-sm font-black text-white flex items-center gap-1 mt-0.5">
              <FiClock className="text-[#D99048]" />
              {destination.recommended_days ? `${destination.recommended_days} Days` : "Not recorded"}
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-white/10 backdrop-blur border border-white/15 text-xs">
            <span className="text-[10px] uppercase font-bold text-stone-300 block">Best Season</span>
            <span className="text-sm font-black text-white flex items-center gap-1 mt-0.5">
              <FiSun className="text-amber-300" />
              {destination.best_time_to_visit || "Not recorded"}
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-white/10 backdrop-blur border border-white/15 text-xs">
            <span className="text-[10px] uppercase font-bold text-stone-300 block">Distance from Kathmandu</span>
            <span className="text-sm font-black text-white flex items-center gap-1 mt-0.5">
              <FiCompass className="text-emerald-300" />
              {destination.distance_from_kathmandu_km != null ? `${destination.distance_from_kathmandu_km} km` : "Not recorded"}
            </span>
          </div>

          <div className="p-3 rounded-2xl bg-white/10 backdrop-blur border border-white/15 text-xs">
            <span className="text-[10px] uppercase font-bold text-stone-300 block">Safety & Risk Level</span>
            <span className="text-sm font-black text-emerald-300 flex items-center gap-1 mt-0.5">
              <FiShield className="text-emerald-400" />
              {destination.risk_analysis?.risk_category || "Moderate"}
            </span>
          </div>
        </div>

        {/* Action Buttons Row */}
        <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-white/15">
          <button
            onClick={() => navigate(`/trip-planner?dest=${encodeURIComponent(destination.slug)}`)}
            className="px-6 py-3.5 rounded-2xl bg-[#D99048] hover:bg-amber-600 text-slate-950 font-black text-sm flex items-center gap-2 shadow-xl shadow-amber-500/20 transition-all hover:scale-105"
          >
            <FiCompass size={18} /> Plan This Journey
          </button>

          <button
            onClick={() => navigate(`/navigation?dest=${encodeURIComponent(destination.name)}`)}
            className="px-6 py-3.5 rounded-2xl bg-white hover:bg-stone-100 text-slate-950 font-black text-sm flex items-center gap-2 shadow-xl transition-all hover:scale-105"
          >
            <FiNavigation size={18} className="text-[#102A2E]" /> Get Road Route
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
            >
              <FiHeart size={20} className={isFavorite ? "fill-white" : ""} />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
