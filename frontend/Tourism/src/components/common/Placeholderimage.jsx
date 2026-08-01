import { FiImage } from "react-icons/fi"

// GRADIENT_SETS cycles through the app's real brand colors so
// placeholders still feel intentional rather than generic gray boxes.
const GRADIENT_SETS = [
  "from-himalaya-500 to-forest-600",
  "from-forest-500 to-saffron-500",
  "from-saffron-500 to-nepalred-500",
  "from-nepalred-500 to-himalaya-600",
]

/**
 * PlaceholderImage
 * Replaces the pattern of `src={cover_image_url || "<guessed unsplash
 * url>"}` that was scattered across DestinationCard, HotelCard,
 * NepalCultureCard, LocalExperienceCard, DestinationDetails, and
 * HotelSearch. Those fallback URLs were never verified (same issue
 * flagged earlier for the auth pages' backgrounds, just missed here) —
 * this is a real gradient + icon, so it can never 404 or show a broken
 * image, and it stays visually on-brand instead of an arbitrary photo.
 *
 * Usage: <PlaceholderImage seed={destination.id} className="w-full h-full object-cover" />
 * `seed` picks a consistent gradient per item so the same card doesn't
 * change color on every re-render.
 */
const PlaceholderImage = ({ seed = 0, className = "", iconSize = 28 }) => {
  const gradient = GRADIENT_SETS[Number(seed) % GRADIENT_SETS.length] || GRADIENT_SETS[0]
  return (
    <div className={`flex items-center justify-center bg-gradient-to-br ${gradient} ${className}`}>
      <FiImage size={iconSize} className="text-white/50" />
    </div>
  )
}

export default PlaceholderImage