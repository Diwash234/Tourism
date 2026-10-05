import { useCallback, useEffect, useState } from "react"
import { FiHeart } from "react-icons/fi"
import useAuth from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import userApi from "../../api/userApi"

/**
 * Like (favourite) button with optimistic updates and an auth check.
 *
 * This used to be a no-op: the API call was commented out
 * (`// await api.post('/likes/...')`), so the heart only flipped local state
 * and was lost on refresh. There is no `/likes/` route on this backend — the
 * real store is FavoriteViewSet at `/favorites/`, which is per-user and
 * unique on (user, destination). It now creates/deletes a real Favorite and
 * only flips the UI once the server agrees.
 *
 * Note: Favorite is destination-only, so targetType other than "destination"
 * is reported as unsupported rather than silently pretending to save.
 */
export default function LikeButton({
  targetId,
  targetType = "destination",
  initialLiked = false,
  initialCount = 0,
  favoriteId = null,
  onToggle,
  size = "md",
  className = "",
}) {
  const { isAuthenticated } = useAuth()
  const { showToast } = useToast()
  const [liked, setLiked] = useState(initialLiked)
  const [count, setCount] = useState(initialCount)
  const [animating, setAnimating] = useState(false)
  const [busy, setBusy] = useState(false)
  // The Favorite row id is needed to delete; keep it in state once we have it.
  const [rowId, setRowId] = useState(favoriteId)

  useEffect(() => {
    setRowId(favoriteId)
  }, [favoriteId])

  const sizes = { sm: "h-8 w-8", md: "h-10 w-10", lg: "h-12 w-12" }
  const iconSizes = { sm: 14, md: 18, lg: 22 }

  const handleClick = useCallback(async (e) => {
    e.stopPropagation()
    e.preventDefault()

    if (!isAuthenticated) {
      showToast("Please sign in to save this", "warning")
      return
    }
    if (busy) return
    if (targetType !== "destination") {
      showToast("Saving is only available for destinations", "warning")
      return
    }

    setBusy(true)
    try {
      if (liked) {
        if (rowId == null) {
          throw new Error("missing-favorite-id")
        }
        await userApi.removeFavorite(rowId)
        setLiked(false)
        setCount((c) => Math.max(0, c - 1))
        setRowId(null)
      } else {
        const { data } = await userApi.addFavorite(targetId)
        setLiked(true)
        setCount((c) => c + 1)
        if (data?.id != null) setRowId(data.id)
      }
      setAnimating(true)
      setTimeout(() => setAnimating(false), 300)
      onToggle?.(!liked)
    } catch (err) {
      // Nothing is flipped on failure, so the UI can never claim a save that
      // did not happen.
      showToast(
        err?.response?.data?.detail || "Could not update your saved list",
        "error"
      )
    } finally {
      setBusy(false)
    }
  }, [liked, rowId, busy, isAuthenticated, targetId, targetType, onToggle, showToast])

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={busy}
      className={`inline-flex items-center gap-1.5 rounded-full transition-all disabled:opacity-60 ${sizes[size]} ${
        liked
          ? "bg-red-50 text-red-500 hover:bg-red-100"
          : "bg-gray-50 text-gray-400 hover:bg-gray-100 hover:text-red-400"
      } ${animating ? "scale-125" : "scale-100"} ${className}`}
      aria-label={liked ? "Remove from saved" : "Save"}
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