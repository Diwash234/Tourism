import { useState } from 'react'
import { FiMapPin, FiNavigation, FiLayers, FiMaximize2 } from 'react-icons/fi'
import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Map component that adapts to different screen sizes.
 * - Mobile: Full-screen map with bottom sheet controls
 * - Tablet/Desktop: Inline map with sidebar controls
 */
const ResponsiveMap = ({
  center = [27.7172, 85.3240],
  zoom: _zoom = 13,
  markers = [],
  onMarkerClick,
  className = '',
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [activeLayer, setActiveLayer] = useState('street')
  const { isMobile } = useResponsive()

  const layers = [
    { id: 'street', label: 'Street' },
    { id: 'satellite', label: 'Satellite' },
    { id: 'terrain', label: 'Terrain' },
  ]

  // Mobile: Full-screen map
  if (isMobile || isFullscreen) {
    return (
      <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50' : 'h-64'} ${className}`}>
        {/* Map placeholder */}
        <div className="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
          <div className="text-center">
            <FiMapPin className="w-12 h-12 mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-500">Map View</p>
          </div>
        </div>

        {/* Controls */}
        <div className="absolute top-4 right-4 flex flex-col gap-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg text-gray-700 dark:text-gray-300"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            <FiMaximize2 className="w-5 h-5" />
          </button>
          <button
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg text-gray-700 dark:text-gray-300"
            aria-label="My location"
          >
            <FiNavigation className="w-5 h-5" />
          </button>
        </div>

        {/* Layer selector */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-2">
            <div className="flex gap-1">
              {layers.map((layer) => (
                <button
                  key={layer.id}
                  onClick={() => setActiveLayer(layer.id)}
                  className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                    activeLayer === layer.id
                      ? 'bg-emerald-600 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {layer.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Desktop: Inline map with sidebar
  return (
    <div className={`flex gap-4 ${className}`}>
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <FiLayers className="w-5 h-5" />
          Map Layers
        </h3>
        <div className="space-y-2">
          {layers.map((layer) => (
            <button
              key={layer.id}
              onClick={() => setActiveLayer(layer.id)}
              className={`w-full px-3 py-2 text-sm rounded-lg text-left transition-colors ${
                activeLayer === layer.id
                  ? 'bg-emerald-100 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {layer.label}
            </button>
          ))}
        </div>

        {/* Markers list */}
        {markers.length > 0 && (
          <div className="mt-6">
            <h4 className="font-medium mb-2 text-sm text-gray-500">Locations</h4>
            <div className="space-y-1">
              {markers.map((marker, index) => (
                <button
                  key={index}
                  onClick={() => onMarkerClick?.(marker)}
                  className="w-full px-3 py-2 text-sm text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                >
                  {marker.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Map */}
      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-xl flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <FiMapPin className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-500">Interactive Map</p>
          <p className="text-sm text-gray-400 mt-1">Center: {center.join(', ')}</p>
        </div>
      </div>
    </div>
  )
}

export default ResponsiveMap
