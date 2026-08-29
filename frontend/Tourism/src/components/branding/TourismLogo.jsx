import React from "react"
import { Link } from "react-router-dom"
import usePublicConfig from "../../hooks/usePublicConfig"

/**
 * NepalYatraSymbol — Standalone Emblem Icon
 * Feature: Geometric Himalayan mountain peak + winding travel path + subtle crimson flag pennant.
 * Palette: Deep Nepal Crimson Red (#C8102E), Himalayan Dark Blue (#0B3D91), Warm Golden Yellow (#F59E0B), Pure White.
 */
export const NepalYatraSymbol = ({ size = 40, className = "" }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 select-none ${className}`}
      aria-label="Nepal Yatra emblem"
    >
      {/* Background Frame / Circular Shield with subtle border */}
      <circle cx="50" cy="50" r="46" fill="#00205B" />

      {/* Background Sky / Altitude Gradient Ring */}
      <circle cx="50" cy="50" r="44" fill="#0B3D91" />

      {/* Sun / Golden Hour Arc */}
      <circle cx="50" cy="48" r="22" fill="#F59E0B" opacity="0.9" />

      {/* Secondary Flanking Himalayan Range */}
      <path d="M12 75 L32 46 L50 75 Z" fill="#4B6B94" />
      <path d="M50 75 L68 44 L88 75 Z" fill="#3B5982" />

      {/* Primary Geometric Main Himalayan Peak */}
      <path d="M22 76 L50 26 L78 76 Z" fill="#FFFFFF" />

      {/* Peak Shading / Angular Facet (Modern Flat Vector Geometry) */}
      <path d="M50 26 L78 76 L50 76 Z" fill="#E2E8F0" opacity="0.9" />
      <path d="M50 26 L60 44 L50 50 Z" fill="#CBD5E1" />

      {/* Winding Travel Path (Golden Path Leading to Summit) */}
      <path
        d="M 28 88 C 38 78, 36 72, 44 64 C 50 58, 46 50, 50 36"
        stroke="#F59E0B"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M 28 88 C 38 78, 36 72, 44 64 C 50 58, 46 50, 50 36"
        stroke="#FFD166"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
        strokeDasharray="4 3"
      />

      {/* Subtle Simplified Nepal Crimson Flag Pennant Accent near Summit */}
      <g transform="translate(52, 20)">
        <line x1="0" y1="0" x2="0" y2="16" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M 0 0 L 12 5 L 0 10 Z" fill="#C8102E" />
        <path d="M 0 6 L 10 10 L 0 14 Z" fill="#C8102E" />
        <circle cx="3" cy="3" r="1" fill="#FFFFFF" />
        <circle cx="3" cy="8" r="0.9" fill="#FFFFFF" />
      </g>

      {/* Base Foundation Arc */}
      <path d="M 10 76 C 30 84, 70 84, 90 76 L 90 88 C 70 96, 30 96, 10 88 Z" fill="#C8102E" />

      {/* Outer Golden Accent Ring */}
      <circle cx="50" cy="50" r="46" stroke="#F59E0B" strokeWidth="2" opacity="0.8" />
    </svg>
  )
}

/**
 * TourismLogo — Primary Nepal Yatra Brand Component
 * Used across Navbar, Auth pages, Footer, and Admin Dashboard.
 */
const TourismLogo = ({ to = "/", showTagline = true, size = "md", darkText = false }) => {
  const { branding } = usePublicConfig()
  const siteTitle = branding.site_title || "Nepal Yatra"
  const tagline = branding.tagline || "Himalayan Journeys & Travel Planning"

  const dims = {
    sm: { box: 34, text: "text-lg", tagline: "hidden" },
    md: { box: 42, text: "text-xl", tagline: "text-[11px]" },
    lg: { box: 56, text: "text-2xl sm:text-3xl", tagline: "text-xs" },
  }[size] || { box: 42, text: "text-xl", tagline: "text-[11px]" }

  return (
    <Link to={to} className="flex items-center gap-2.5 select-none shrink-0 min-w-0 group">
      {branding.logo_url ? (
        <img
          src={branding.logo_url}
          alt={branding.logo_alt || `${siteTitle} logo`}
          width={dims.box}
          height={dims.box}
          className="object-contain shrink-0 rounded-xl"
        />
      ) : (
        <NepalYatraSymbol size={dims.box} className="group-hover:scale-105 transition-transform" />
      )}

      <div className="leading-tight flex flex-col justify-center min-w-0">
        <div className="flex items-center gap-1 font-heading font-black tracking-tight">
          <span className={darkText ? "text-slate-900" : "text-white drop-shadow-sm"}>
            {siteTitle.includes("Nepal") ? "Nepal" : siteTitle}
          </span>
          {siteTitle.includes("Nepal") && (
            <span className="text-amber-400 font-extrabold">
              {siteTitle.replace("Nepal", "").trim() || "Yatra"}
            </span>
          )}
        </div>
        {showTagline && (
          <p className={`${dims.tagline} font-medium text-slate-300/90 tracking-wide truncate max-w-xs`}>
            {tagline}
          </p>
        )}
      </div>
    </Link>
  )
}

export default TourismLogo
