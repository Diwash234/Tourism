import { useState, useCallback } from "react"
import { FiHeart } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"

/**
 * Like button with animation, optimistic updates, and authentication check.
 */
export default function LikeButton({
  targetId,
  targetType = "destination",
  initialLiked = false,
  initialCount = 0,
  onToggle,
  size = "md",
  className = "",
}) {
  const { isAuthenticated } = useAuth()
  const { addToast } = useToast()
  const [liked, setLiked] = useState(initialLiked)
  const [count, setCount] = useState(initialCount)
  const [animating, setAnimating] = useState(false)

  const sizes = { sm: "h-8 w-8", md: "h-10 w-10", lg: "h-12 w-12" }
  const iconSizes = { sm: 14, md: 18, lg: 22 }

  const handleClick = useCallback(async (e) => {
    e.stopPropagation()
    e.preventDefault()

    if (!isAuthenticated) {
      addToast("Please login to like this", "warning")
      return
    }

    // Optimistic update
    const newLiked = !liked
    setLiked(newLiked)
    setCount(c => newLiked ? c + 1 : c - 1)

    // Animation
    setAnimating(true)
    setTimeout(() => setAnimating(false), 300)

    try {
      // Call API
      // await api.post(`/likes/${targetType}/${targetId}`)
      onToggle?.(newLiked)
    } catch (err) {
      // Revert on error
      setLiked(!newLiked)
      setCount(c => newLiked ? c - 1 : c + 1)
      addToast("Failed to update like", "error")
    }
  }, [liked, isAuthenticated, targetId, targetType, onToggle, addToast])

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`inline-flex items-center gap-1.5 rounded-full transition-all ${sizes[size]} ${
        liked
          ? "bg-red-50 text-red-500 hover:bg-red-100"
          : "bg-gray-50 text-gray-400 hover:bg-gray-100 hover:text-red-400"
      } ${animating ? "scale-125" : "scale-100"} ${className}`}
      aria-label={liked ? "Unlike" : "Like"}
      aria-pressed={liked}
    >
      <FiHeart
        size={iconSizes[size]}
        className={`transition-all ${liked ? "fill-current" : ""} ${animating ? "animate-bounce" : ""}`}
      />
      {count > 0 && (
        <span className="text-xs font-semibold">{count.toLocaleString()}</span>
      )}
    </button>
  )
}
