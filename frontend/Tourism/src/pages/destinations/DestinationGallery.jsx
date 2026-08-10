import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiX, FiChevronLeft, FiChevronRight } from "react-icons/fi"
import PlaceholderImage from "../../components/common/PlaceholderImage"
/**
 * DestinationGallery
 *
 * Was previously hardcoded in DestinationDetails.jsx to show exactly
 * gallery[0] and gallery[1] -- meaning a destination with 5-10 real
 * photos still only ever showed 2. This renders every image actually
 * present: the cover photo large, up to 5 more in a grid, and a
 * "+N more" tile + click-through lightbox for anything beyond that.
 */
const DestinationGallery = ({ coverImageUrl, gallery = [], destinationId, destinationName }) => {
  const [lightboxIndex, setLightboxIndex] = useState(null)

  const galleryUrls = gallery
    .map((g) => g.image || g.external_url)
    .filter(Boolean)

  // Cover image counts as the first slide too, so the lightbox can page
  // through everything including it, not just the grid thumbnails.
  const allImages = coverImageUrl ? [coverImageUrl, ...galleryUrls] : galleryUrls
  const visibleGridImages = galleryUrls.slice(0, 5)
  const remainingCount = galleryUrls.length - visibleGridImages.length

  const openLightbox = (indexInAllImages) => setLightboxIndex(indexInAllImages)
  const closeLightbox = () => setLightboxIndex(null)
  const showNext = () => setLightboxIndex((i) => (i + 1) % allImages.length)
  const showPrev = () => setLightboxIndex((i) => (i - 1 + allImages.length) % allImages.length)

  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-8 rounded-xl2 overflow-hidden">
        {coverImageUrl ? (
          <img
            src={coverImageUrl}
            alt={destinationName}
            onClick={() => openLightbox(0)}
            className="lg:col-span-2 h-80 w-full object-cover cursor-pointer hover:opacity-95 transition-opacity"
          />
        ) : (
          <PlaceholderImage seed={destinationId} className="lg:col-span-2 h-80 w-full" iconSize={40} />
        )}

        <div className="grid grid-cols-2 lg:grid-cols-1 grid-rows-2 gap-3">
          {visibleGridImages.length > 0 ? (
            visibleGridImages.slice(0, 2).map((url, i) => {
              const allImagesIndex = coverImageUrl ? i + 1 : i
              const isLastVisibleTile = i === 1 && remainingCount > 0
              return (
                <div
                  key={url}
                  onClick={() => openLightbox(allImagesIndex)}
                  className="relative h-full w-full cursor-pointer group"
                >
                  <img
                    src={url}
                    alt={`${destinationName} ${i + 2}`}
                    className="h-full w-full object-cover group-hover:opacity-90 transition-opacity"
                  />
                  {isLastVisibleTile && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white font-semibold text-lg">
                      +{remainingCount} more
                    </div>
                  )}
                </div>
              )
            })
          ) : (
            <>
              <PlaceholderImage seed={destinationId + 1} className="h-full w-full" />
              <PlaceholderImage seed={destinationId + 2} className="h-full w-full" />
            </>
          )}
        </div>
      </div>

      <AnimatePresence>
        {lightboxIndex !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
            onClick={closeLightbox}
          >
            <button
              onClick={closeLightbox}
              className="absolute top-5 right-5 text-white/80 hover:text-white p-2"
              aria-label="Close"
            >
              <FiX size={28} />
            </button>

            {allImages.length > 1 && (
              <button
                onClick={(e) => { e.stopPropagation(); showPrev() }}
                className="absolute left-4 text-white/80 hover:text-white p-2"
                aria-label="Previous image"
              >
                <FiChevronLeft size={32} />
              </button>
            )}

            <motion.img
              key={lightboxIndex}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              src={allImages[lightboxIndex]}
              alt={`${destinationName} full size`}
              onClick={(e) => e.stopPropagation()}
              className="max-h-[85vh] max-w-[90vw] object-contain rounded-lg"
            />

            {allImages.length > 1 && (
              <button
                onClick={(e) => { e.stopPropagation(); showNext() }}
                className="absolute right-4 text-white/80 hover:text-white p-2"
                aria-label="Next image"
              >
                <FiChevronRight size={32} />
              </button>
            )}

            <span className="absolute bottom-5 text-white/70 text-sm">
              {lightboxIndex + 1} / {allImages.length}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default DestinationGallery