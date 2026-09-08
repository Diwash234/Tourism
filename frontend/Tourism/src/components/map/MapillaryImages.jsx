import { useEffect, useState } from "react"
import {
  FiCamera,
  FiExternalLink,
  FiLoader,
  FiAlertCircle,
} from "react-icons/fi"

import {
  MAPILLARY_ACCESS_TOKEN,
} from "../../utils/constants"

import configApi from "../../api/configApi"


const MAPILLARY_GRAPH_API =
  "https://graph.mapillary.com/images"


/**
 * MapillaryImages
 *
 * Fetches Mapillary street-level images around a latitude/longitude.
 *
 * The token can be supplied by the parent component:
 *
 * <MapillaryImages
 *   latitude={27.7172}
 *   longitude={85.3240}
 *   accessToken={mapillaryToken}
 * />
 *
 * If no token is supplied, this component falls back to:
 *
 * 1. VITE_MAPILLARY_ACCESS_TOKEN
 * 2. Backend public config
 */
const MapillaryImages = ({
  latitude,
  longitude,
  radiusM = 400,
  limit = 6,
  accessToken = "",
}) => {

  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const [token, setToken] = useState(
    accessToken ||
    MAPILLARY_ACCESS_TOKEN ||
    ""
  )


  /**
   * Update token when parent passes one.
   */
  useEffect(() => {
    if (accessToken) {
      setToken(accessToken)
    }
  }, [accessToken])


  /**
   * Fallback to backend public config if
   * no token was supplied by the parent.
   */
  useEffect(() => {

    if (accessToken) {
      return
    }

    let ignore = false

    configApi
      .getPublicConfig()
      .then(({ data }) => {

        if (
          !ignore &&
          data?.mapillary_access_token
        ) {
          setToken(
            data.mapillary_access_token
          )
        }

      })
      .catch(() => {
        // Keep frontend token if backend config fails.
      })

    return () => {
      ignore = true
    }

  }, [accessToken])


  /**
   * Fetch Mapillary images.
   */
  useEffect(() => {

    if (
      latitude == null ||
      longitude == null ||
      !Number.isFinite(Number(latitude)) ||
      !Number.isFinite(Number(longitude)) ||
      !token
    ) {
      setImages([])
      return
    }


    const lat = Number(latitude)
    const lng = Number(longitude)


    let ignore = false

    setLoading(true)
    setError("")


    /**
     * Convert radius from meters into
     * approximate latitude/longitude degrees.
     */
    const dLat =
      radiusM / 111320

    const cosLat =
      Math.cos(
        (lat * Math.PI) / 180
      )

    const dLon =
      radiusM /
      (111320 * Math.max(Math.abs(cosLat), 0.01))


    /**
     * Mapillary bbox format:
     *
     * minLon,minLat,maxLon,maxLat
     */
    const bbox = [
      lng - dLon,
      lat - dLat,
      lng + dLon,
      lat + dLat,
    ].join(",")


    const params = new URLSearchParams({
      access_token: token,

      fields: [
        "id",
        "geometry",
        "compass_angle",
        "thumb_1024_url",
        "thumb_2048_url",
        "width",
        "height",
        "is_pano",
      ].join(","),

      bbox,

      limit: String(limit),
    })


    const url =
      `${MAPILLARY_GRAPH_API}?${params.toString()}`


    fetch(url)
      .then(async (response) => {

        if (!response.ok) {

          let message =
            `Mapillary request failed (${response.status})`

          try {
            const body =
              await response.json()

            if (body?.error?.message) {
              message =
                body.error.message
            }
          } catch {
            // Ignore JSON parsing failure.
          }

          throw new Error(message)
        }

        return response.json()
      })


      .then((data) => {

        if (ignore) return


        const items =
          Array.isArray(data?.data)
            ? data.data
            : []


        const normalized =
          items
            .map((img) => {

              let lat = null
              let lng = null


              /**
               * Mapillary geometry normally comes
               * back as GeoJSON:
               *
               * {
               *   type: "Point",
               *   coordinates: [lng, lat]
               * }
               *
               * Handle that first.
               */
              if (
                img?.geometry?.coordinates &&
                Array.isArray(
                  img.geometry.coordinates
                )
              ) {

                lng = Number(
                  img.geometry.coordinates[0]
                )

                lat = Number(
                  img.geometry.coordinates[1]
                )

              }


              /**
               * Also support WKT geometry if returned.
               */
              if (
                (lat == null || lng == null) &&
                typeof img?.geometry === "string"
              ) {

                const match =
                  /POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/
                    .exec(img.geometry)

                if (match) {
                  lng = Number(match[1])
                  lat = Number(match[2])
                }
              }


              return {
                id: img.id,

                lat:
                  Number.isFinite(lat)
                    ? lat
                    : null,

                lng:
                  Number.isFinite(lng)
                    ? lng
                    : null,

                /**
                 * Prefer 2048px image,
                 * then 1024px image.
                 */
                url:
                  img.thumb_2048_url ||
                  img.thumb_1024_url ||
                  "",

                width:
                  img.width || null,

                height:
                  img.height || null,

                compass:
                  img.compass_angle != null
                    ? Math.round(
                        img.compass_angle
                      )
                    : null,

                pano:
                  Boolean(img.is_pano),
              }
            })

            /**
             * Don't render records without
             * an actual image URL.
             */
            .filter(
              (img) => Boolean(img.url)
            )

            .slice(0, limit)


        setImages(normalized)

      })


      .catch((err) => {

        if (ignore) return

        console.error(
          "Mapillary error:",
          err
        )

        setImages([])
        setError(
          err?.message ||
          "Unable to load Mapillary imagery."
        )

      })


      .finally(() => {

        if (!ignore) {
          setLoading(false)
        }

      })


    return () => {
      ignore = true
    }

  }, [
    latitude,
    longitude,
    token,
    radiusM,
    limit,
  ])


  /**
   * No Mapillary token.
   */
  if (!token) {

    return (
      <div className="flex items-center gap-2 text-xs text-gray-400 py-2">
        <FiCamera />
        Mapillary is not configured.
      </div>
    )
  }


  /**
   * Loading state.
   */
  if (loading) {

    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 py-2">
        <FiLoader className="animate-spin" />
        Loading Mapillary images…
      </div>
    )
  }


  /**
   * Error state.
   */
  if (error) {

    return (
      <div className="flex items-start gap-2 text-xs text-red-500 py-2">
        <FiAlertCircle className="mt-0.5 shrink-0" />

        <span>
          Unable to load Mapillary imagery.
          <br />

          <span className="text-[10px] text-gray-400">
            {error}
          </span>
        </span>
      </div>
    )
  }


  /**
   * No imagery near location.
   */
  if (!images.length) {

    return (
      <div className="flex items-center gap-2 text-xs text-gray-400 py-2">
        <FiCamera />
        No Mapillary imagery near this location.
      </div>
    )
  }


  /**
   * Render images.
   */
  return (
    <div>

      <p className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 mb-2">

        <FiCamera className="text-himalaya-500" />

        Mapillary street imagery

      </p>


      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">

        {images.map((img) => (

          <a
            key={img.id}

            href={
              `https://www.mapillary.com/app/?pKey=${img.id}`
            }

            target="_blank"

            rel="noopener noreferrer"

            className="
              group
              relative
              rounded-lg
              overflow-hidden
              border
              border-gray-100
              block
              bg-gray-100
            "
          >

            <img
              src={img.url}

              alt="Mapillary street imagery"

              loading="lazy"

              className="
                w-full
                h-20
                object-cover
                group-hover:scale-105
                transition-transform
              "

              onError={(event) => {
                event.currentTarget.style.display =
                  "none"
              }}
            />


            <span
              className="
                absolute
                bottom-0
                inset-x-0
                bg-gradient-to-t
                from-black/70
                to-transparent
                px-1.5
                py-1
                text-[10px]
                text-white
                flex
                items-center
                justify-between
              "
            >

              <span>

                {img.width &&
                img.height
                  ? `${img.width}×${img.height}px`
                  : "Mapillary"}

                {img.pano
                  ? " · 360°"
                  : ""}

              </span>


              <FiExternalLink
                size={10}
              />

            </span>

          </a>

        ))}

      </div>

    </div>
  )
}


export default MapillaryImages