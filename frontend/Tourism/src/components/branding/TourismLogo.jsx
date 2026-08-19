import { Link } from "react-router-dom"

/**
 * TourismLogo — v2, circular mark.
 * Replaces the earlier "T" wordmark-style logo. Same prop API
 * (to, showTagline, size) so every existing caller (Navbar, Login,
 * Register, ForgotPassword) keeps working with zero changes elsewhere.
 *
 * Design note: cramming every requested motif (Everest, rising sun,
 * prayer flags, Stupa, Rhododendron, flag hint, trekking trail, mandala
 * border) into a 24px navbar icon would just read as noise — real logos
 * simplify at small sizes. So: size="sm"/"md" render a simplified core
 * mark (mountain + sun + mandala ring) that stays legible down to
 * favicon size, and size="lg" unlocks the full detailed version with
 * every motif, meant for splash/about-page contexts.
 */
const TourismLogo = ({ to = "/", showTagline = true, size = "md" }) => {
  const dims = {
    sm: { box: 32, text: "text-lg", tagline: "hidden", detailed: false },
    md: { box: 40, text: "text-xl", tagline: "text-[11px]", detailed: false },
    lg: { box: 64, text: "text-2xl", tagline: "text-xs", detailed: true },
  }[size]

  return (
    <Link to={to} className="flex items-center gap-2 sm:gap-2.5 select-none shrink-0 min-w-0">
      <svg
        width={dims.box}
        height={dims.box}
        viewBox="0 0 100 100"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Digital Nepal tourism logo"
      >
        <defs>
          <linearGradient id="logoSky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0B3D91" />
            <stop offset="65%" stopColor="#3f66b8" />
            <stop offset="100%" stopColor="#F59E0B" />
          </linearGradient>
          <clipPath id="logoCircleClip">
            <circle cx="50" cy="50" r="42" />
          </clipPath>
        </defs>

        {/* Mandala-inspired outer border: dashed ring + petal notches */}
        <circle cx="50" cy="50" r="47" fill="none" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="2 3" />
        {dims.detailed &&
          Array.from({ length: 12 }).map((_, i) => {
            const angle = (i * 30 * Math.PI) / 180
            const x = 50 + 47 * Math.cos(angle)
            const y = 50 + 47 * Math.sin(angle)
            return <circle key={i} cx={x} cy={y} r="1.6" fill="#DC143C" />
          })}

        {/* Sky + circular frame */}
        <circle cx="50" cy="50" r="42" fill="url(#logoSky)" />

        <g clipPath="url(#logoCircleClip)">
          {/* Prayer flag string across the top, only at detailed size */}
          {dims.detailed && (
            <>
              <path d="M10 22 Q 50 14 90 22" stroke="#ffffff" strokeOpacity="0.6" strokeWidth="1" fill="none" />
              {[18, 34, 50, 66, 82].map((x, i) => {
                const colors = ["#DC143C", "#F59E0B", "#FFFFFF", "#1B8A5A", "#0B3D91"]
                return <path key={x} d={`M${x} 21 L${x - 4} 28 L${x + 4} 28 Z`} fill={colors[i]} />
              })}
            </>
          )}

          {/* Rising sun, partly behind the mountain */}
          <circle cx="50" cy="60" r="13" fill="#F59E0B" />
          {dims.detailed &&
            Array.from({ length: 8 }).map((_, i) => {
              const angle = (i * 45 * Math.PI) / 180
              const x1 = 50 + 15 * Math.cos(angle)
              const y1 = 60 + 15 * Math.sin(angle)
              const x2 = 50 + 19 * Math.cos(angle)
              const y2 = 60 + 19 * Math.sin(angle)
              return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#F59E0B" strokeWidth="1.5" />
            })}

          {/* Secondary flanking peaks for a range effect (detailed only) */}
          {dims.detailed && (
            <>
              <path d="M8 68 L22 46 L34 68 Z" fill="#c9d8f3" />
              <path d="M66 68 L80 44 L94 68 Z" fill="#c9d8f3" />
            </>
          )}

          {/* Everest silhouette, main peak */}
          <path d="M22 68 L42 32 L50 44 L58 30 L78 68 Z" fill="#FFFFFF" />
          <path d="M50 44 L58 30 L63 38 L58 40 Z" fill="#eaf0fb" />
          <path d="M42 32 L46 38 L38 40 Z" fill="#eaf0fb" />

          {/* Trekking trail winding toward the base of the mountain */}
          {dims.detailed && (
            <path
              d="M6 82 Q 20 74 18 66 Q 16 58 28 56 Q 40 54 42 46"
              stroke="#F59E0B"
              strokeWidth="1.4"
              strokeDasharray="2 2.5"
              fill="none"
              strokeLinecap="round"
            />
          )}

          {/* Foreground band (grass/foothill) */}
          <rect x="0" y="80" width="100" height="20" fill="#146c46" />

          {/* Stupa silhouette, small, near the trail */}
          {dims.detailed && (
            <g transform="translate(70, 70)">
              <rect x="-6" y="8" width="12" height="4" fill="#FFFFFF" />
              <path d="M-7 8 A7 6 0 0 1 7 8 Z" fill="#FFFFFF" />
              <rect x="-1.2" y="-6" width="2.4" height="8" fill="#F59E0B" />
              <path d="M-3 -6 L0 -12 L3 -6 Z" fill="#F59E0B" />
            </g>
          )}

          {/* Rhododendron (national flower) accent, small, opposite the stupa */}
          {dims.detailed && (
            <g transform="translate(24, 76)">
              <circle cx="0" cy="-3" r="2.6" fill="#DC143C" />
              <circle cx="-2.8" cy="-1" r="2.6" fill="#DC143C" />
              <circle cx="2.8" cy="-1" r="2.6" fill="#DC143C" />
              <circle cx="-1.7" cy="2.2" r="2.6" fill="#DC143C" />
              <circle cx="1.7" cy="2.2" r="2.6" fill="#DC143C" />
              <circle cx="0" cy="0" r="1.5" fill="#F59E0B" />
            </g>
          )}

          {/* Subtle Nepal-flag pennant hint on a small pole by the trail */}
          {dims.detailed && (
            <g transform="translate(10, 80)">
              <line x1="0" y1="0" x2="0" y2="-10" stroke="#eee" strokeWidth="0.8" />
              <path d="M0 -10 L6 -8 L0 -5 Z" fill="#DC143C" stroke="#0B3D91" strokeWidth="0.5" />
            </g>
          )}
        </g>

        {/* Circle outline on top for a crisp edge */}
        <circle cx="50" cy="50" r="42" fill="none" stroke="#0B3D91" strokeWidth="1" opacity="0.4" />
      </svg>

      <div className="leading-tight hidden sm:block min-w-0">
        <h1 className={`${dims.text} font-heading font-extrabold text-himalaya-500 whitespace-nowrap`}>
          Digital<span className="text-forest-500">Nepal</span>
        </h1>
        {showTagline && (
          <p className={`${dims.tagline} font-medium text-gray-400 tracking-wide`}>
            Explore the Heart of the Himalayas
          </p>
        )}
      </div>
    </Link>
  )
}

export default TourismLogo

/*
  To switch to a designed asset later:
  1. Drop the final logo at src/assets/logo.svg (or .png)
  2. Replace the <svg>...</svg> block above with:
       <img src={logoUrl} alt="Digital Nepal logo" style={{ width: dims.box, height: dims.box }} />
  3. Keep the exported prop API (to, showTagline, size) the same so
     Navbar.jsx, Login.jsx, Register.jsx, ForgotPassword.jsx don't need edits.
*/