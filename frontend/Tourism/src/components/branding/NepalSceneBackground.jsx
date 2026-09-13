/**
 * NepalSceneBackground
 * Original SVG artwork (no external photo) — layered Himalayan
 * silhouette, a string of prayer flags, and a corner Dhoka (traditional
 * Newari carved wooden window/door) motif. Used as a full-bleed
 * background behind the auth pages instead of a hotlinked stock photo.
 *
 * Swapping in real photography later: replace the whole component with
 * an <img>/background-image using your own licensed photo — everything
 * that renders on top of it (the logo, the auth card) doesn't need to
 * change, since this only fills the background layer.
 */
const NepalSceneBackground = () => (
  <svg
    className="absolute inset-0 w-full h-full"
    viewBox="0 0 1200 700"
    preserveAspectRatio="xMidYMax slice"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#0B3D91" />
        <stop offset="100%" stopColor="#1B8A5A" />
      </linearGradient>
    </defs>

    <rect width="1200" height="700" fill="url(#sky)" />

    {/* Distant mountain layer */}
    <path
      d="M0 420 L120 300 L220 380 L340 250 L460 360 L600 220 L760 370 L900 260 L1050 380 L1200 300 L1200 700 L0 700 Z"
      fill="#ffffff"
      opacity="0.08"
    />
    {/* Mid mountain layer with a snow-cap highlight */}
    <path
      d="M0 480 L150 340 L280 440 L420 300 L560 430 L720 320 L880 450 L1050 340 L1200 440 L1200 700 L0 700 Z"
      fill="#ffffff"
      opacity="0.14"
    />
    <path d="M420 300 L460 340 L400 340 Z" fill="#ffffff" opacity="0.35" />
    <path d="M720 320 L760 360 L700 360 Z" fill="#ffffff" opacity="0.35" />

    {/* Foreground mountain layer, darkest */}
    <path
      d="M0 560 L100 460 L230 540 L380 420 L520 550 L680 440 L840 560 L1000 460 L1200 540 L1200 700 L0 700 Z"
      fill="#072454"
      opacity="0.55"
    />

    {/* Prayer flag string across the top */}
    <path d="M0 60 Q 600 130 1200 50" stroke="#ffffff" strokeOpacity="0.4" strokeWidth="2" fill="none" />
    {[80, 260, 440, 620, 800, 980, 1150].map((x, i) => {
      const colors = ["#DC143C", "#F59E0B", "#FFFFFF", "#1B8A5A", "#0B3D91"]
      const y = 60 + Math.sin(i) * 20 + (i % 2 === 0 ? 20 : 35)
      return (
        <path
          key={x}
          d={`M${x} ${y} L${x - 10} ${y + 16} L${x + 10} ${y + 16} Z`}
          fill={colors[i % colors.length]}
          opacity="0.55"
        />
      )
    })}

    {/* Corner Dhoka motif — simplified traditional Newari carved window
        lattice, bottom-left corner, very low opacity so it reads as
        texture rather than competing with the auth card */}
    <g transform="translate(20, 520)" opacity="0.18" fill="none" stroke="#ffffff" strokeWidth="2">
      <rect x="0" y="0" width="160" height="160" rx="4" />
      <rect x="14" y="14" width="132" height="132" rx="3" />
      {[0, 1, 2, 3].map((row) =>
        [0, 1, 2, 3].map((col) => (
          <rect key={`${row}-${col}`} x={22 + col * 30} y={22 + row * 30} width="22" height="22" />
        ))
      )}
    </g>
  </svg>
)

export default NepalSceneBackground