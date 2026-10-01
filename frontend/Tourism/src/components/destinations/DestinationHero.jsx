import { useState } from "react"
import { FiMapPin, FiCamera, FiHeart, FiShare2, FiNavigation, FiStar } from "react-icons/fi"
import { useAuth } from "../../hooks/useAuth"
import useToast from "../../hooks/useToast"
import LazyImage from "../common/LazyImage"

/**
 * Destination hero section with image gallery, quick actions,
 * rating display, and call-to-action buttons.
 */
export default function DestinationHero({ destination, onNavigate, onShare }) {
  const { isAuthenticated } = useAuth()
  const { addToast } = useToast()
  const [liked, setLiked] = useState(false)
  const [imageIndex, setImageIndex] = useState(0)

  const images = destination?.images?.length > 0
    ? destination.images
    : [{ src: destination?.image_url || "/placeholder-destination.jpg", alt: destination?.name }]

  const handleLike = () => {
    if (!isAuthenticated) {
      addToast("Please login to save destinations", "warning")
      return
    }
    setLiked(v => !v)
    addToast(liked ? "Removed from favorites" : "Added to favorites!", "success")
  }

  const handleShare = async () => {
    const shareData = {
      title: destination?.name,
      text: `Check out ${destination?.name} - ${destination?.description?.slice(0, 100)}...`,
      url: window.location.href,
    }
    if (navigator.share) {
      try { await navigator.share(shareData) } catch { /* user cancelled */ }
    } else {
      await navigator.clipboard.writeText(window.location.href)
      addToast("Link copied to clipboard!", "success")
    }
    onShare?.()
  }

  return (
    <div className="relative">
      {/* Image Gallery */}
      <div className="relative h-[300px] sm:h-[400px] md:h-[500px] overflow-hidden rounded-2xl">
        <LazyImage
          src={images[imageIndex]?.src || images[imageIndex]}
          alt={images[imageIndex]?.alt || destination?.name}
          className="w-full h-full"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

        {/* Quick Actions */}
        <div className="absolute top-4 right-4 flex gap-2">
          <button
            type="button"
            onClick={handleLike}
            className={`p-2.5 rounded-full backdrop-blur-sm transition-all ${
              liked ? "bg-red-500 text-white" : "bg-black/40 text-white hover:bg-black/60"
            }`}
            aria-label={liked ? "Remove from favorites" : "Add to favorites"}
          >
            <FiHeart size={18} className={liked ? "fill-current" : ""} />
          </button>
          <button
            type="button"
            onClick={handleShare}
            className="p-2.5 rounded-full bg-black/40 text-white backdrop-blur-sm hover:bg-black/60 transition-all"
            aria-label="Share destination"
          >
            <FiShare2 size={18} />
          </button>
        </div>

        {/* Image indicators */}
        {images.length > 1 && (
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 flex gap-1.5">
            {images.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setImageIndex(i)}
                className={`h-1.5 rounded-full transition-all ${
                  i === imageIndex ? "w-6 bg-white" : "w-1.5 bg-white/50 hover:bg-white/75"
                }`}
                aria-label={`View image ${i + 1}`}
              />
            ))}
          </div>
        )}

        {/* Navigation CTA */}
        {onNavigate && (
          <button
            type="button"
            onClick={onNavigate}
            className="absolute bottom-20 right-4 flex items-center gap-2 px-4 py-2.5 rounded-full bg-[var(--ny-green)] text-white font-semibold shadow-lg hover:bg-[var(--ny-emerald)] transition-colors"
          >
            <FiNavigation size={16} />
            <span className="hidden sm:inline">Navigate</span>
          </button>
        )}

        {/* Title & Info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-6">
          <div className="flex items-end justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white truncate">
                {destination?.name}
              </h1>
              <div className="flex items-center gap-3 mt-2 text-white/90">
                <span className="flex items-center gap-1 text-sm">
                  <FiMapPin size={14} />
                  {destination?.district || destination?.province || "Nepal"}
                </span>
                {destination?.rating && (
                  <span className="flex items-center gap-1 text-sm">
                    <FiStar size={14} className="text-amber-400 fill-amber-400" />
                    {destination.rating.toFixed(1)}
                  </span>
                )}
              </div>
            </div>
            {images.length > 1 && (
              <div className="flex items-center gap-1 text-white/80 text-sm shrink-0">
                <FiCamera size={14} />
                {images.length} photos
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
