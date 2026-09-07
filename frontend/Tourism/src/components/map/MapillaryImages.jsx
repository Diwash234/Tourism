import { useEffect, useState } from "react"
import { FiCamera, FiExternalLink, FiLoader } from "react-icons/fi"
import { MAPILLARY_ACCESS_TOKEN } from "../../utils/constants"
import configApi from "../../api/configApi"

const MAPILLARY_GRAPH_API = "https://graph.mapillary.com/images"

const NEPAL_STREET_FALLBACKS = [
  { id: "ktm-street", url: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/KATHMANDU_NEPAL_FEB_2013_%288581665041%29.jpg/960px-KATHMANDU_NEPAL_FEB_2013_%288581665041%29.jpg", title: "Kathmandu Valley Street View" },
  { id: "pokhara-lakeside-street", url: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Panorama_view_of_Kathmandu.jpg/960px-Panorama_view_of_Kathmandu.jpg", title: "Pokhara Lakeside Corridor" },
  { id: "highway-transit", url: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Sunkoshi_River_and_BP_Highway_Sindhuli.jpg/960px-Sunkoshi_River_and_BP_Highway_Sindhuli.jpg", title: "BP Highway Transit Route" },
  { id: "mustang-trail", url: "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/The_village_of_Tsarang.jpg/960px-The_village_of_Tsarang.jpg", title: "Mustang High-Altitude Corridor" },
]

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
    if (!latitude || !longitude) {
      setImages([])
      return
    }
    if (!token) {
      setImages(NEPAL_STREET_FALLBACKS.slice(0, limit))
      return
    }

    let ignore = false
    setLoading(true)

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
          const items = (data.data || []).map((img) => {
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
          setImages(items.length ? items.slice(0, limit) : NEPAL_STREET_FALLBACKS.slice(0, limit))
        }
      })
      .catch(() => {
        if (!ignore) setImages(NEPAL_STREET_FALLBACKS.slice(0, limit))
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })

    return () => {
      ignore = true
    }
  }, [latitude, longitude, token, radiusM, limit])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 py-2">
        <FiLoader className="animate-spin" /> Loading street-level imagery…
      </div>
    )
  }

  const itemsToDisplay = images.length ? images : NEPAL_STREET_FALLBACKS.slice(0, limit)

  return (
    <div className="space-y-2">
      <p className="flex items-center justify-between text-xs font-bold text-slate-700">
        <span className="flex items-center gap-1.5"><FiCamera className="text-blue-600" /> Street-Level & Corridor Views</span>
        <span className="text-[10px] text-slate-400 font-mono">Nepal Transit Imagery</span>
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {itemsToDisplay.map((img, idx) => (
          <a
            key={img.id || idx}
            href={img.id ? `https://www.mapillary.com/app/?pKey=${img.id}` : img.url}
            target="_blank"
            rel="noreferrer"
            className="group relative rounded-xl overflow-hidden border border-slate-200 block shadow-sm hover:shadow"
          >
            <img
              src={img.url}
              alt={img.title || "Street View"}
              loading="lazy"
              className="w-full h-20 object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <span className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-1.5 text-[10px] text-white flex items-center justify-between font-medium">
              <span className="truncate">{img.title || (img.width ? `${img.width}×${img.height}px` : "Nepal Corridor")}</span>
              <FiExternalLink size={10} className="shrink-0 ml-1" />
            </span>
          </a>
        ))}
      </div>
    </div>
  )
}

export default MapillaryImages
