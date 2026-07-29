import { Link } from "react-router-dom"

/**
 * TourismLogo
 * Placeholder mark built from CSS/SVG primitives so it renders instantly
 * with no image asset. Swap the <svg> block below for a designed logo
 * file later (see the comment at the bottom) without touching callers.
 *
 * Concept: a bold "T" — the left stroke carries a mountain-peak notch and
 * Nepal-flag colors, the right stroke carries a small compass pin. Two
 * small national-identity accents sit above: a stylized Lali Gurans
 * (rhododendron, Nepal's national flower) and a simplified Danphe
 * (Himalayan monal, national bird) silhouette. The core T/mountain shape
 * stays legible even at favicon size (24px); the two accents are most
 * visible at "lg".
 */
const TourismLogo = ({ to = "/", showTagline = true, size = "md" }) => {
  const dims = {
    sm: { box: 32, text: "text-lg", tagline: "hidden" },
    md: { box: 40, text: "text-xl", tagline: "text-[11px]" },
    lg: { box: 56, text: "text-2xl", tagline: "text-xs" },
  }[size]

  return (
    <Link to={to} className="flex items-center gap-2.5 select-none">
      <svg
        width={dims.box}
        height={dims.box}
        viewBox="0 0 64 64"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Tourism logo"
      >
        {/* Left stroke of the T: Himalayan peaks in Nepal blue/red */}
        <path d="M6 14 L26 14 L26 24 L18 24 L18 54 L10 54 L10 24 L6 24 Z" fill="#0B3D91" />
        <path d="M8 24 L14 12 L18 20 L22 10 L26 24 Z" fill="#DC143C" />

        {/* Right stroke of the T: compass pin in green/gold */}
        <path d="M38 14 L58 14 L58 24 L54 24 L54 54 L46 54 L46 24 L38 24 Z" fill="#1B8A5A" />
        <circle cx="50" cy="10" r="5" fill="#F59E0B" />
        <circle cx="50" cy="10" r="1.8" fill="#FFFFFF" />

        {/* Lali Gurans (rhododendron) — Nepal's national flower — a
            simple 5-petal accent above the left peak */}
        <g transform="translate(15, 4)">
          <circle cx="0" cy="-3" r="2.4" fill="#DC143C" />
          <circle cx="-2.6" cy="-1" r="2.4" fill="#DC143C" />
          <circle cx="2.6" cy="-1" r="2.4" fill="#DC143C" />
          <circle cx="-1.6" cy="2" r="2.4" fill="#DC143C" />
          <circle cx="1.6" cy="2" r="2.4" fill="#DC143C" />
          <circle cx="0" cy="0" r="1.4" fill="#F59E0B" />
        </g>

        {/* Danphe (Himalayan monal) — Nepal's national bird — a
            simplified crested silhouette, small accent right of the flag */}
        <g transform="translate(30, 6)" fill="#1B8A5A">
          <path d="M0 6 C0 2 3 0 6 0 C7 -1 8 -2 8 -3 C8 -2 7.5 -0.5 7 0.3 C9 1.5 10 3.5 9 6 C8 8.5 4 9 2 8 C0.5 7.3 0 6.6 0 6 Z" />
          <circle cx="7.5" cy="1.3" r="0.9" fill="#F59E0B" />
        </g>

        {/* Center bar of the T uniting both halves */}
        <rect x="10" y="14" width="44" height="8" rx="2" fill="#0B3D91" />
      </svg>

      <div className="leading-tight">
        <h1 className={`${dims.text} font-extrabold text-himalaya-500`}>
          Tour<span className="text-forest-500">ism</span>
        </h1>
        {showTagline && (
          <p className={`${dims.tagline} font-medium text-gray-400 tracking-wide`}>
            Explore Nepal Together
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
       <img src={logoUrl} alt="Tourism logo" style={{ width: dims.box, height: dims.box }} />
  3. Keep the exported prop API (to, showTagline, size) the same so
     Navbar.jsx, Footer.jsx, and the login/register pages don't need edits.
*/