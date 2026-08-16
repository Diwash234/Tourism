/**
 * Tourist brand mark — a bold "T" set in a rounded badge.
 * size: pixel size of the badge (default 36)
 * variant: "sunrise" (crimson→marigold, for light headers) | "white" (for dark/gradient headers)
 */
const Logo = ({ size = 36, variant = "sunrise", className = "" }) => {
  const isWhite = variant === "white"

  return (
    <span
      className={`inline-flex items-center justify-center rounded-xl shrink-0 font-display font-bold select-none ${className}`}
      style={{
        width: size,
        height: size,
        fontSize: size * 0.52,
        background: isWhite
          ? "rgba(255,255,255,0.16)"
          : "linear-gradient(135deg, #C0293B 0%, #E8A33D 100%)",
        color: "#FFFFFF",
        border: isWhite ? "1px solid rgba(255,255,255,0.35)" : "none",
        boxShadow: isWhite ? "none" : "0 4px 10px rgba(192,41,59,0.35)",
      }}
      aria-hidden="true"
    >
      T
    </span>
  )
}

export default Logo