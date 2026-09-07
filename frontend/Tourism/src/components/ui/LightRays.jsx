/**
 * LightRays — animated conic/radial light rays bursting from a point.
 * ReactBits-style decorative background for hero sections, empty states,
 * and premium call-to-action areas. Fully CSS-animated (no GPU-heavy JS
 * per-frame loop), respects prefers-reduced-motion.
 */
import { cn } from "../../utils/cn"

export default function LightRays({
  className = "",
  color = "#1f6b4d",
  accent = "#c2603a",
  count = 12,
  intensity = 0.35,
  speed = 18, // seconds per full rotation
  children,
}) {
  const rays = Array.from({ length: count })
  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)} aria-hidden="true">
      {/* Slow rotating ray bundle */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        style={{
          width: "max(220vmax, 1200px)",
          height: "max(220vmax, 1200px)",
          animation: `rays-spin ${speed}s linear infinite`,
          backgroundImage: `conic-gradient(
            from 0deg,
            transparent 0deg,
            ${color}33 4deg,
            transparent 8deg,
            transparent 20deg,
            ${accent}22 24deg,
            transparent 28deg,
            transparent 45deg,
            ${color}22 49deg,
            transparent 53deg,
            transparent 70deg,
            ${accent}33 74deg,
            transparent 78deg,
            transparent 100%
          )`,
          opacity: intensity,
          mixBlendMode: "screen",
          filter: "blur(30px)",
        }}
      />
      {/* Opposite direction for parallax depth */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        style={{
          width: "max(160vmax, 900px)",
          height: "max(160vmax, 900px)",
          animation: `rays-spin ${speed * 1.6}s linear infinite reverse`,
          backgroundImage: `repeating-conic-gradient(
            from 0deg,
            transparent 0deg,
            ${accent}22 2deg,
            transparent 6deg
          )`,
          opacity: intensity * 0.7,
          mixBlendMode: "screen",
          filter: "blur(24px)",
        }}
      />
      {/* Radial glow hotspot */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          width: "60vmax",
          height: "60vmax",
          background: `radial-gradient(circle, ${color}22 0%, ${accent}11 30%, transparent 70%)`,
          animation: `rays-pulse ${speed / 2}s ease-in-out infinite alternate`,
        }}
      />
      {/* Solid center mask so content stays readable */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          width: "35vmax",
          height: "35vmax",
          background: "radial-gradient(circle, rgba(250,248,244,1) 0%, rgba(250,248,244,0) 70%)",
        }}
      />
      {children}
      <style>{`
        @keyframes rays-spin { to { transform: translate(-50%,-50%) rotate(360deg); } }
        @keyframes rays-pulse {
          from { opacity: 0.7; transform: translate(-50%,-50%) scale(0.95); }
          to   { opacity: 1;   transform: translate(-50%,-50%) scale(1.08); }
        }
        @media (prefers-reduced-motion: reduce) {
          .rays-container, .rays-container * { animation: none !important; }
        }
      `}</style>
    </div>
  )
}
