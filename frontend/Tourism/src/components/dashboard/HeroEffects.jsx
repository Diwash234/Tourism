/**
 * HeroEffects — sits absolutely behind the hero's text content (parent
 * must be `relative`, this is `absolute inset-0 z-0`, content above it
 * needs `relative z-10`, which Landing.jsx's hero content already has).
 * Everything here is CSS keyframe animation, not a scroll-linked JS
 * parallax or a canvas particle system — deliberately, to keep the
 * landing page fast per the brief's own "maintaining fast performance"
 * requirement.
 */
const HeroEffects = () => {
  const snowflakes = Array.from({ length: 24 }).map((_, i) => ({
    left: `${(i * 41) % 100}%`,
    delay: `${(i % 8) * 1.7}s`,
    duration: `${8 + (i % 5)}s`,
    size: 2 + (i % 3),
  }))

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
      {/* Floating clouds */}
      <div className="hero-cloud absolute top-10 left-[10%] w-40 h-14 bg-white/10 rounded-full blur-xl" />
      <div className="hero-cloud absolute top-20 right-[15%] w-56 h-16 bg-white/10 rounded-full blur-xl" style={{ animationDelay: "6s" }} />
      <div className="hero-cloud absolute top-6 left-[45%] w-32 h-10 bg-white/10 rounded-full blur-lg" style={{ animationDelay: "12s" }} />

      {/* Prayer flag string, gently waving */}
      <svg className="absolute top-4 left-0 w-full h-16" viewBox="0 0 400 60" preserveAspectRatio="none">
        <path d="M0 10 Q 200 0 400 10" stroke="#ffffff" strokeOpacity="0.3" strokeWidth="1" fill="none" />
        {[20, 80, 140, 200, 260, 320, 380].map((x, i) => {
          const colors = ["#DC143C", "#F59E0B", "#FFFFFF", "#1B8A5A", "#0B3D91"]
          return (
            <path
              key={x}
              className="hero-flag"
              style={{ animationDelay: `${i * 0.15}s` }}
              d={`M${x} 10 L${x - 8} 26 L${x + 8} 26 Z`}
              fill={colors[i % colors.length]}
              opacity="0.55"
            />
          )
        })}
      </svg>

      {/* Layered mountain silhouettes, distant drift */}
      <svg className="hero-mountain-layer absolute bottom-0 left-0 w-[110%] h-40" viewBox="0 0 1200 200" preserveAspectRatio="none">
        <path d="M0 160 L150 60 L300 140 L450 40 L600 150 L750 70 L900 160 L1050 50 L1200 140 L1200 200 L0 200 Z" fill="#ffffff" opacity="0.08" />
      </svg>
      <svg className="hero-mountain-layer absolute bottom-0 left-0 w-[110%] h-28" viewBox="0 0 1200 140" preserveAspectRatio="none" style={{ animationDelay: "-20s" }}>
        <path d="M0 120 L200 40 L380 110 L560 20 L740 120 L920 50 L1100 120 L1200 90 L1200 140 L0 140 Z" fill="#072454" opacity="0.25" />
      </svg>

      {/* Subtle snowfall */}
      {snowflakes.map((s, i) => (
        <span
          key={i}
          className="hero-snowflake absolute top-0 rounded-full bg-white"
          style={{
            left: s.left,
            width: s.size,
            height: s.size,
            animationDelay: s.delay,
            animationDuration: s.duration,
          }}
        />
      ))}
    </div>
  )
}

export default HeroEffects