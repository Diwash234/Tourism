import PlaceholderImage from "./PlaceholderImage"

/**
 * ImageGallery
 * Shows only images attached to the place record. Unknown or empty records
 * receive a neutral unavailable treatment rather than unrelated stock media.
 */
const toUrl = (item) =>
  typeof item === "string" ? item : item?.image || item?.external_url || item?.display_url || null

const ImageGallery = ({ images = [], name, count = 6, seed = 0 }) => {
  const backendUrls = (Array.isArray(images) ? images : []).map(toUrl).filter(Boolean)
  const allImages = backendUrls.slice(0, count).map((url) => ({ url, source: "backend" }))

  if (allImages.length === 0) {
    return <PlaceholderImage seed={seed} className="h-64 w-full rounded-xl" />
  }

  return (
    <div className="columns-2 sm:columns-3 gap-3 [column-fill:_balance]">
      {allImages.map((img, i) => (
        <div key={img.url + i} className="relative mb-3 break-inside-avoid">
          <img
            src={img.url}
            alt={`${name || "Place"} photo ${i + 1}`}
            loading="lazy"
            className="w-full rounded-xl object-cover"
            onError={(e) => {
              e.currentTarget.parentElement.style.display = "none"
            }}
          />
        </div>
      ))}
    </div>
  )
}

export default ImageGallery