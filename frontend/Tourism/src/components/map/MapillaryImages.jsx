import { useEffect, useState } from "react"
import { FiCamera, FiExternalLink, FiLoader } from "react-icons/fi"
import { MAPILLARY_ACCESS_TOKEN } from "../../utils/constants"
import configApi from "../../api/configApi"

const MAPILLARY_GRAPH_API = "https://graph.mapillary.com/images"

/**
 * MapillaryImages — street-level imagery for a location (Google-Street-View
 * style). Uses the Mapillary Graph API v4 with the access token from the
 * frontend env (VITE_MAPILLARY_ACCESS_TOKEN) or the backend public config.
 *
 * Images are fetched for a small bounding box around (latitude, longitude)
 * and displayed with their real pixel dimensions (width × height).
 */
const MapillaryImages = ({ latitude, longitude, radiusM = 400, limit = 6 }) => {
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState(MAPILLARY_ACCESS_TOKEN || "")

  useEffect(() => {
    let ignore = false
    configApi
      .getPublicConfig()
      .then(({ data }) => {
        if (!ignore && data?.mapillary_access_token) {
          setToken(data.mapillary_access_token)
        }
      })
      .catch(() => {})
    return () => {
      ignore = true
    }
  }, [])

  useEffect(() => {
    if (!latitude || !longitude || !token) {
      setImages([])
      return
    }
    let ignore = false
    setLoading(true)

    // bbox: min_lon,min_lat,max_lon,max_lat (~radiusM meters each side)
    const dLat = radiusM / 111320
    const dLon = radiusM / (111320 * Math.cos((latitude * Math.PI) / 180) || 1)
    const bbox = `${longitude - dLon},${latitude - dLat},${longitude + dLon},${latitude + dLat}`

    const params = new URLSearchParams({
      fields: "id,geometry,compass_angle,thumb_original_url,width,height,is_pano",
      bbox,
      limit: String(limit),
      access_token: token,
    })

    fetch(`${MAPILLARY_GRAPH_API}?${params.toString()}`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("Mapillary error"))))
      .then((data) => {
        if (!ignore) {
          const items = (data.data || [])
            .map((img) => {
              const m = /POINT\s*\(([-\d.]+)\s+([-\d.]+)\)/.exec(img.geometry || "")
              return {
                id: img.id,
                lat: m ? parseFloat(m[2]) : null,
                lng: m ? parseFloat(m[1]) : null,
                url: img.thumb_original_url || `https://images.mapillary.com/${img.id}/thumb-640.jpg`,
                width: img.width || null,
                height: img.height || null,
                compass: img.compass_angle != null ? Math.round(img.compass_angle) : null,
                pano: img.is_pano,
              }
            })
            .slice(0, limit)
          setImages(items)
        }
      })
      .catch(() => {
        if (!ignore) setImages([])
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })

    return () => {
      ignore = true
    }
  }, [latitude, longitude, token, radiusM, limit])

  if (!token)
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400 py-2">
        <FiCamera /> Street-level imagery is available when a Mapillary access token
        is configured (add <code className="font-mono">MAPILLARY_ACCESS_TOKEN</code> to the
        backend <code className="font-mono">.env</code> or{" "}
        <code className="font-mono">VITE_MAPILLARY_ACCESS_TOKEN</code> to the frontend{" "}
        <code className="font-mono">.env</code>).
      </div>
    )
  if (loading)
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 py-2">
        <FiLoader className="animate-spin" /> Loading Mapillary images…
      </div>
    )
  if (!images.length)
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400 py-2">
        <FiCamera /> No Mapillary imagery near this location.
      </div>
    )

  return (
    <div>
      <p className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 mb-2">
        <FiCamera className="text-himalaya-500" /> Mapillary street imagery
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {images.map((img) => (
          <a
            key={img.id}
            href={`https://www.mapillary.com/app/?pKey=${img.id}`}
            target="_blank"
            rel="noreferrer"
            className="group relative rounded-lg overflow-hidden border border-gray-100 block"
          >
            <img
              src={img.url}
              alt="Mapillary"
              loading="lazy"
              className="w-full h-20 object-cover group-hover:scale-105 transition-transform"
            />
            <span className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent px-1.5 py-1 text-[10px] text-white flex items-center justify-between">
              <span>
                {img.width && img.height ? `${img.width}×${img.height}px` : "Mapillary"}
                {img.pano ? " · 360°" : ""}
              </span>
              <FiExternalLink size={10} />
            </span>
          </a>
        ))}
      </div>
    </div>
  )
}

export default MapillaryImages
