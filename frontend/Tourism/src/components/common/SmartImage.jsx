import { useState } from "react"
import PlaceholderImage from "./PlaceholderImage"

/**
 * Render only an image that is attached to the record. If the record has no
 * usable image, or the supplied image fails to load, show the honest neutral
 * placeholder instead of searching for unrelated stock photography.
 */
const SmartImage = ({
  src,
  seed = 0,
  alt = "",
  className = "",
}) => {
  const [failed, setFailed] = useState(false)
  const [previousSrc, setPreviousSrc] = useState(src)

  if (previousSrc !== src) {
    setPreviousSrc(src)
    setFailed(false)
  }

  if (!src || failed) return <PlaceholderImage seed={seed} title={alt || "Image unavailable"} alt={alt} className={className} />

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}

export default SmartImage
