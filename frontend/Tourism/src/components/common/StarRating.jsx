import { FiStar } from "react-icons/fi"

/**
 * Star rating component with interactive and read-only modes.
 */
export default function StarRating({ value = 0, max = 5, onChange, size = "md", className = "" }) {
  const sizes = { sm: "h-3.5 w-3.5", md: "h-5 w-5", lg: "h-6 w-6" }

  return (
    <div className={`flex items-center gap-0.5 ${className}`} role={onChange ? "radiogroup" : "img"} aria-label={`Rating: ${value} out of ${max}`}>
      {Array.from({ length: max }).map((_, i) => {
        const filled = i < Math.round(value)
        const star = (
          <FiStar
            className={`${sizes[size] || sizes.md} ${filled ? "text-amber-400 fill-amber-400" : "text-gray-300 dark:text-slate-600"}`}
          />
        )
        return onChange ? (
          <button
            key={i}
            type="button"
            onClick={() => onChange(i + 1)}
            className="focus:outline-none focus:ring-2 focus:ring-amber-400 rounded"
            role="radio"
            aria-checked={value === i + 1}
            aria-label={`Rate ${i + 1} star${i > 0 ? "s" : ""}`}
          >
            {star}
          </button>
        ) : (
          <span key={i}>{star}</span>
        )
      })}
    </div>
  )
}
