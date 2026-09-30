import { useState, useEffect } from 'react'
import { useInView } from './Performance'

/**
 * Responsive Image component that:
 * - Lazy loads images
 * - Shows placeholder while loading
 * - Handles errors gracefully
 * - Adapts to different screen sizes
 * - Supports srcset for different resolutions
 */
const ResponsiveImage = ({
  src,
  alt = '',
  width,
  height,
  className = '',
  placeholder = '/images/placeholder.jpg',
  sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw',
  srcSet,
  priority = false,
  ...props
}) => {
  const [ref, isInView] = useInView({ threshold: 0.1 })
  const [isLoaded, setIsLoaded] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!src || !isInView) return

    const img = new Image()
    img.src = src
    img.onload = () => setIsLoaded(true)
    img.onerror = () => setError(true)
  }, [src, isInView])

  // Don't render until in view (lazy loading)
  if (!isInView) {
    return (
      <div
        ref={ref}
        className={`bg-gray-200 dark:bg-gray-700 animate-pulse ${className}`}
        style={{ width, height }}
      />
    )
  }

  // Show error state
  if (error) {
    return (
      <div
        className={`bg-gray-200 dark:bg-gray-700 flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        <div className="text-center p-4">
          <svg className="w-8 h-8 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="text-xs text-gray-500 mt-2">Failed to load image</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={ref} className={`relative overflow-hidden ${className}`} style={{ width, height }}>
      {/* Placeholder */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse" />
      )}

      {/* Actual image */}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
        onLoad={() => setIsLoaded(true)}
        onError={() => setError(true)}
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        srcSet={srcSet}
        sizes={sizes}
        {...props}
      />
    </div>
  )
}

export default ResponsiveImage
