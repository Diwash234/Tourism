import { Link } from "react-router-dom"
import { FiMapPin, FiStar, FiHeart, FiCamera } from "react-icons/fi"
import Badge from "../common/Badge"
import LazyImage from "../common/LazyImage"

/**
 * Enhanced destination card with image, rating, location,
 * quick actions, and hover effects.
 */
export default function DestinationCard({ destination, onFavorite, className = "" }) {
  const {
    id,
    name,
    slug,
    district,
    province,
    category,
    rating,
    image_url,
    images,
    description,
    tags,
    is_featured,
  } = destination

  const detailPath = `/destinations/${slug || id}`
  const imageSrc = image_url || images?.[0]?.src || images?.[0] || "/placeholder-destination.jpg"

  return (
    <div className={`group bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${className}`}>
      {/* Image */}
      <div className="relative aspect-[4/3] overflow-hidden">
        <Link to={detailPath}>
          <LazyImage
            src={imageSrc}
            alt={name}
            className="w-full h-full group-hover:scale-105 transition-transform duration-500"
          />
        </Link>
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />

        {/* Badges */}
        <div className="absolute top-3 left-3 flex gap-1.5">
          {is_featured && <Badge variant="warning" size="sm">Featured</Badge>}
          {category && <Badge variant="primary" size="sm">{category}</Badge>}
        </div>

        {/* Quick Actions */}
        <div className="absolute top-3 right-3 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={() => onFavorite?.(id)}
            className="p-2 rounded-full bg-white/90 text-gray-600 hover:text-red-500 hover:bg-white transition-colors shadow-sm"
            aria-label="Add to favorites"
          >
            <FiHeart size={14} />
          </button>
          <Link
            to={`${detailPath}?tab=gallery`}
            className="p-2 rounded-full bg-white/90 text-gray-600 hover:text-blue-500 hover:bg-white transition-colors shadow-sm"
            aria-label="View gallery"
          >
            <FiCamera size={14} />
          </Link>
        </div>

        {/* Rating */}
        {rating && (
          <div className="absolute bottom-3 right-3 flex items-center gap-1 px-2 py-1 rounded-full bg-black/60 text-white text-xs font-semibold">
            <FiStar size={12} className="text-amber-400 fill-amber-400" />
            {rating.toFixed(1)}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <Link to={detailPath} className="block">
          <h3 className="text-sm font-bold text-gray-900 dark:text-white group-hover:text-[var(--ny-green)] transition-colors line-clamp-1">
            {name}
          </h3>
        </Link>

        <div className="flex items-center gap-1 mt-1 text-xs text-gray-500 dark:text-gray-400">
          <FiMapPin size={12} />
          <span className="truncate">{district}{province ? `, ${province}` : ""}</span>
        </div>

        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 line-clamp-2 leading-relaxed">
            {description}
          </p>
        )}

        {tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 text-xs font-medium rounded-full bg-[var(--ny-soft-green)] text-[var(--ny-green)]"
              >
                {tag}
              </span>
            ))}
            {tags.length > 3 && (
              <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-gray-400">
                +{tags.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
