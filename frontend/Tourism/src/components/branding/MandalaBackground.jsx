/**
 * MandalaBackground — original SVG pattern of concentric dashed rings +
 * petal motifs, meant to sit behind a content card at low opacity.
 * Reused wherever the brief asks for a "mandala background" (Profile
 * page today).
 */
const MandalaBackground = ({ className = "" }) => (
  <svg
    className={`absolute pointer-events-none ${className}`}
    viewBox="0 0 300 300"
    aria-hidden="true"
  >
    {[130, 100, 70].map((r, i) => (
      <circle
        key={r}
        cx="150"
        cy="150"
        r={r}
        fill="none"
        stroke="#0B3D91"
        strokeOpacity={0.08 + i * 0.03}
        strokeWidth="1.5"
        strokeDasharray={i % 2 === 0 ? "3 4" : "1 3"}
      />
    ))}
    {Array.from({ length: 16 }).map((_, i) => {
      const angle = (i * 22.5 * Math.PI) / 180
      const x = 150 + 130 * Math.cos(angle)
      const y = 150 + 130 * Math.sin(angle)
      return <circle key={i} cx={x} cy={y} r="3" fill="#F59E0B" fillOpacity="0.2" />
    })}
    {Array.from({ length: 8 }).map((_, i) => {
      const angle = (i * 45 * Math.PI) / 180
      const x = 150 + 70 * Math.cos(angle)
      const y = 150 + 70 * Math.sin(angle)
      return <circle key={i} cx={x} cy={y} r="4" fill="#1B8A5A" fillOpacity="0.12" />
    })}
  </svg>
)

export default MandalaBackground