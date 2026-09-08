import { useEffect, useMemo, useRef, useState } from "react"
import { motion } from "framer-motion"

import MapView from "../components/map/MapView"
import MapillaryImages from "../components/map/MapillaryImages"
import useGeolocation from "../hooks/useGeolocation"

import {
  FiNavigation,
  FiMapPin,
  FiZap,
  FiShield,
  FiDollarSign,
  FiTrendingUp,
  FiArrowLeft,
  FiArrowRight,
  FiArrowUp,
  FiRotateCcw,
  FiChevronLeft,
  FiChevronRight,
  FiCompass,
  FiTarget,
  FiLayers,
  FiRadio,
  FiFlag,
} from "react-icons/fi"

import navigationApi from "../api/navigationApi"

import {
  formatDistance,
  formatDuration,
} from "../utils/formatDistance"

import {
  getTurnByTurnDirections,
} from "../utils/turnByTurn"


/* =========================================================
   ROUTE TYPES
========================================================= */

const ROUTE_TYPES = [
  {
    id: "fastest",
    label: "⚡ Fastest Highway",
    shortLabel: "⚡ Fastest",
    icon: FiZap,
    available: true,
  },
  {
    id: "safest",
    label: "🛡️ Safest Low-Risk",
    shortLabel: "🛡️ Safest",
    icon: FiShield,
    available: true,
  },
  {
    id: "cheapest",
    label: "💰 Budget Scenic",
    shortLabel: "💰 Cheapest",
    icon: FiDollarSign,
    available: true,
  },
  {
    id: "trekking",
    label: "🏔️ Alpine Trekking",
    shortLabel: "🏔️ Trekking",
    icon: FiTrendingUp,
    available: true,
  },
]


/* =========================================================
   QUICK ROUTE PRESETS
========================================================= */

const QUICK_INTERNAL_ROUTES = [
  {
    label: "Kathmandu ➔ Pokhara (Prithvi Hwy)",
    dest: "Pokhara",
  },
  {
    label: "Pokhara ➔ Annapurna Base Camp",
    dest: "Annapurna Base Camp",
  },
  {
    label: "Kathmandu ➔ Everest Base Camp",
    dest: "Everest Base Camp",
  },
  {
    label: "Kathmandu ➔ Chitwan Safari",
    dest: "Chitwan National Park Safari",
  },
  {
    label: "Pokhara ➔ Muktinath (Mustang)",
    dest: "Upper Mustang & Lo Manthang",
  },
  {
    label: "Kathmandu ➔ Nagarkot Sunrise",
    dest: "Nagarkot Himalayan Sunrise Viewpoint",
  },
]


/* =========================================================
   TURN ICONS
========================================================= */

const TURN_ICONS = {
  start: FiFlag,
  finish: FiFlag,

  straight: FiArrowUp,

  "slight-left": FiChevronLeft,
  slight_left: FiChevronLeft,

  left: FiArrowLeft,

  "sharp-left": FiChevronLeft,
  sharp_left: FiChevronLeft,

  "slight-right": FiChevronRight,
  slight_right: FiChevronRight,

  right: FiArrowRight,

  "sharp-right": FiChevronRight,
  sharp_right: FiChevronRight,

  uturn: FiRotateCcw,
}


/* =========================================================
   HAVERSINE DISTANCE
========================================================= */

const calculateDistance = (
  lat1,
  lon1,
  lat2,
  lon2
) => {
  const R = 6371

  const dLat =
    ((lat2 - lat1) * Math.PI) / 180

  const dLon =
    ((lon2 - lon1) * Math.PI) / 180

  const a =
    Math.sin(dLat / 2) *
      Math.sin(dLat / 2) +

    Math.cos(
      (lat1 * Math.PI) / 180
    ) *

    Math.cos(
      (lat2 * Math.PI) / 180
    ) *

    Math.sin(dLon / 2) *
      Math.sin(dLon / 2)

  const c =
    2 *
    Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a)
    )

  return R * c
}


/* =========================================================
   NORMALIZE ROUTE
========================================================= */

const normalizeRoute = (route) => {
  if (!route) {
    return []
  }


  /*
   * GeoJSON object:
   *
   * {
   *   coordinates: [
   *     [lng, lat],
   *     [lng, lat]
   *   ]
   * }
   */

  if (
    !Array.isArray(route) &&
    Array.isArray(route.coordinates)
  ) {
    return route.coordinates
      .map((coordinate) => {
        if (!Array.isArray(coordinate)) {
          return null
        }

        const lng = Number(coordinate[0])
        const lat = Number(coordinate[1])

        if (
          !Number.isFinite(lat) ||
          !Number.isFinite(lng)
        ) {
          return null
        }

        return [lat, lng]
      })
      .filter(Boolean)
  }


  if (!Array.isArray(route)) {
    return []
  }


  if (route.length === 0) {
    return []
  }


  /*
   * Array coordinate route:
   *
   * [[lat, lng], [lat, lng]]
   */

  if (Array.isArray(route[0])) {
    return route
      .map((point) => {
        if (!Array.isArray(point)) {
          return null
        }

        const lat = Number(point[0])
        const lng = Number(point[1])

        if (
          !Number.isFinite(lat) ||
          !Number.isFinite(lng)
        ) {
          return null
        }

        return [lat, lng]
      })
      .filter(Boolean)
  }


  /*
   * Object route:
   *
   * { lat, lng }
   *
   * { latitude, longitude }
   *
   * { coordinates: [...] }
   */

  return route
    .flatMap((point) => {
      if (!point) {
        return []
      }


      /*
       * GeoJSON geometry inside array
       */

      if (
        Array.isArray(point.coordinates)
      ) {
        return point.coordinates
          .map((coordinate) => {
            if (!Array.isArray(coordinate)) {
              return null
            }

            const lng = Number(coordinate[0])
            const lat = Number(coordinate[1])

            if (
              !Number.isFinite(lat) ||
              !Number.isFinite(lng)
            ) {
              return null
            }

            return [lat, lng]
          })
          .filter(Boolean)
      }


      const lat = Number(
        point.lat ??
        point.latitude
      )

      const lng = Number(
        point.lng ??
        point.longitude
      )

      if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lng)
      ) {
        return []
      }

      return [[lat, lng]]
    })
    .filter(Boolean)
}


/* =========================================================
   NORMALIZE TURN TYPE
========================================================= */

const normalizeTurnType = (turn) => {
  if (!turn) {
    return "straight"
  }

  const value = String(turn)
    .trim()
    .toLowerCase()
    .replace(/_/g, "-")


  if (value === "slight-left") {
    return "slight-left"
  }

  if (value === "sharp-left") {
    return "sharp-left"
  }

  if (value === "slight-right") {
    return "slight-right"
  }

  if (value === "sharp-right") {
    return "sharp-right"
  }

  if (
    value === "uturn" ||
    value === "u-turn"
  ) {
    return "uturn"
  }

  if (
    value === "start" ||
    value === "finish" ||
    value === "straight" ||
    value === "left" ||
    value === "right"
  ) {
    return value
  }

  return "straight"
}


/* =========================================================
   CATEGORIZE BACKEND INSTRUCTION
========================================================= */

const categorizeTurn = (instruction) => {
  const text = String(
    instruction || ""
  ).toLowerCase()


  if (
    text.includes("arrive") ||
    text.includes("destination")
  ) {
    return "finish"
  }


  if (
    text.startsWith("head") ||
    text.startsWith("start")
  ) {
    return "start"
  }


  if (
    text.includes("sharp right")
  ) {
    return "sharp-right"
  }


  if (
    text.includes("sharp left")
  ) {
    return "sharp-left"
  }


  if (
    text.includes("slight right") ||
    text.includes("slightly right")
  ) {
    return "slight-right"
  }


  if (
    text.includes("slight left") ||
    text.includes("slightly left")
  ) {
    return "slight-left"
  }


  if (
    text.includes("u-turn") ||
    text.includes("uturn") ||
    text.includes("u turn")
  ) {
    return "uturn"
  }


  if (text.includes("right")) {
    return "right"
  }


  if (text.includes("left")) {
    return "left"
  }


  return "straight"
}


/* =========================================================
   NORMALIZE STEP
========================================================= */

const normalizeStep = (step) => {
  if (!step) {
    return null
  }


  const distanceKm = Number(
    step.distanceKm ??
    step.distance_km ??
    step.distance ??
    0
  )


  const rawTurn =
    step.icon ??
    step.turn ??
    step.type


  const turn = normalizeTurnType(
    rawTurn
  )


  return {
    ...step,

    turn,

    icon: turn,

    instruction:
      step.instruction ||
      step.text ||
      "Continue along the route",

    distanceKm:
      Number.isFinite(distanceKm)
        ? distanceKm
        : 0,

    distance_km:
      Number.isFinite(distanceKm)
        ? distanceKm
        : 0,

    distance_m:
      Math.round(
        (
          Number.isFinite(distanceKm)
            ? distanceKm
            : 0
        ) * 1000
      ),
  }
}


/* =========================================================
   BACKEND DIRECTIONS NORMALIZER
========================================================= */

const normalizeBackendDirections = (
  directions
) => {
  if (
    !Array.isArray(directions)
  ) {
    return []
  }


  return directions
    .map((direction) => {
      if (!direction) {
        return null
      }


      const instruction =
        direction.instruction ||
        direction.text ||
        "Continue along the route"


      const distanceKm = Number(
        direction.distanceKm ??
        direction.distance_km ??
        direction.distance ??
        0
      )


      const turn = normalizeTurnType(
        direction.turn ||
        direction.icon ||
        direction.type ||
        categorizeTurn(instruction)
      )


      return normalizeStep({
        ...direction,

        instruction,

        turn,

        icon: turn,

        distanceKm:
          Number.isFinite(distanceKm)
            ? distanceKm
            : 0,

        distance_km:
          Number.isFinite(distanceKm)
            ? distanceKm
            : 0,
      })
    })
    .filter(Boolean)
}


/* =========================================================
   NAVIGATION COMPONENT
========================================================= */

const Navigation = () => {
  const { position } =
    useGeolocation()


  /* =======================================================
     SEARCH / ROUTE STATE
  ======================================================= */

  const [
    destinationQuery,
    setDestinationQuery,
  ] = useState("Pokhara")


  const [
    destination,
    setDestination,
  ] = useState(null)


  const [
    route,
    setRoute,
  ] = useState([])


  const [
    routeType,
    setRouteType,
  ] = useState("fastest")


  const [
    distance,
    setDistance,
  ] = useState(null)


  const [
    durationMin,
    setDurationMin,
  ] = useState(null)


  const [
    steps,
    setSteps,
  ] = useState([])


  const [
    currentStepIdx,
    setCurrentStepIdx,
  ] = useState(0)


  const [
    note,
    setNote,
  ] = useState(null)


  const [
    loading,
    setLoading,
  ] = useState(false)


  const [
    error,
    setError,
  ] = useState("")


  /* =======================================================
     GAME HUD STATE
  ======================================================= */

  const [
    gameMode,
    setGameMode,
  ] = useState(true)


  const [
    speedKmh,
    setSpeedKmh,
  ] = useState(0)


  const [
    compassBearing,
    setCompassBearing,
  ] = useState("—")


  const [
    altitudeM,
    setAltitudeM,
  ] = useState(null)


  const [
    satelliteView,
    setSatelliteView,
  ] = useState(false)


  /* =======================================================
     INITIAL ROUTE CONTROL
  ======================================================= */

  const initialRouteLoaded =
    useRef(false)


  /* =======================================================
     ACTIVE REQUEST CONTROL
  ======================================================= */

  const requestIdRef =
    useRef(0)


  /* =======================================================
     NORMALIZED ROUTE
  ======================================================= */

  const normalizedRoute =
    useMemo(
      () =>
        normalizeRoute(route),
      [route]
    )


  /* =======================================================
     GPS HUD TELEMETRY
  ======================================================= */

  useEffect(() => {
    if (!position) {
      return
    }


    /*
     * Browser Geolocation speed:
     * meters / second
     */

    if (
      Number.isFinite(
        position.speed
      )
    ) {
      setSpeedKmh(
        Math.max(
          0,
          Math.round(
            position.speed * 3.6
          )
        )
      )
    } else {
      setSpeedKmh(0)
    }


    /*
     * Browser heading:
     * degrees from north
     */

    if (
      Number.isFinite(
        position.heading
      )
    ) {
      setCompassBearing(
        `${Math.round(
          position.heading
        )}°`
      )
    } else {
      setCompassBearing("—")
    }


    /*
     * Browser altitude
     */

    if (
      Number.isFinite(
        position.altitude
      )
    ) {
      setAltitudeM(
        Math.round(
          position.altitude
        )
      )
    } else {
      setAltitudeM(null)
    }
  }, [position])


  /* =======================================================
     GET ROUTE
  ======================================================= */

  const handleGetRoute = async (
    targetDest = null
  ) => {
    const destName =
      typeof targetDest === "string"
        ? targetDest.trim()
        : destinationQuery.trim()


    if (!destName) {
      setError(
        "Please enter a destination."
      )
      return
    }


    /*
     * Do not invent GPS coordinates.
     */

    if (!position) {
      setError(
        "Waiting for GPS location. Please allow location access and try again."
      )
      return
    }


    const currentRequestId =
      ++requestIdRef.current


    setLoading(true)
    setError("")


    /*
     * Clear previous route
     * while calculating.
     */

    setRoute([])
    setSteps([])
    setDestination(null)
    setDistance(null)
    setDurationMin(null)
    setNote(null)
    setCurrentStepIdx(0)


    try {
      const payload = {
        start_latitude:
          position.lat,

        start_longitude:
          position.lng,

        destination_name:
          destName,

        route_type:
          routeType,
      }


      console.log(
        "Navigation request:",
        payload
      )


      const response =
        await navigationApi.getRoute(
          payload
        )


      /*
       * Ignore stale responses.
       */

      if (
        currentRequestId !==
        requestIdRef.current
      ) {
        return
      }


      const data =
        response?.data || {}


      console.log(
        "Navigation response:",
        data
      )


      /* =====================================================
         DESTINATION
      ===================================================== */

      const dest =
        data.destination || null


      setDestination(dest)


      /* =====================================================
         SERVER ROUTE
      ===================================================== */

      let serverRoute = []


      if (
        Array.isArray(
          data.route
        )
      ) {
        serverRoute =
          data.route
      } else if (
        data.route &&
        Array.isArray(
          data.route.coordinates
        )
      ) {
        serverRoute =
          data.route.coordinates
      }


      setRoute(serverRoute)


      /* =====================================================
         NORMALIZE ROUTE
      ===================================================== */

      const cleanRoute =
        normalizeRoute(
          serverRoute
        )


      /* =====================================================
         TURN-BY-TURN
         
         PRIORITY:
         
         1. Backend directions
         2. Local geometry directions
         3. Empty state
      ===================================================== */

      let cleanSteps = []


      /*
       * First use backend-generated
       * directions if available.
       */

      if (
        Array.isArray(
          data.directions
        ) &&
        data.directions.length > 0
      ) {
        cleanSteps =
          normalizeBackendDirections(
            data.directions
          )


        console.log(
          "Using backend turn-by-turn directions:",
          cleanSteps
        )
      }


      /*
       * If backend directions are unavailable,
       * calculate directions locally from
       * actual route geometry.
       */

      if (
        cleanSteps.length === 0 &&
        cleanRoute.length > 1
      ) {
        try {
          const generatedSteps =
            getTurnByTurnDirections(
              cleanRoute
            ) || []


          cleanSteps =
            generatedSteps
              .map(
                normalizeStep
              )
              .filter(Boolean)


          console.log(
            "Using locally generated turn-by-turn directions:",
            cleanSteps
          )
        } catch (
          directionError
        ) {
          console.warn(
            "Local turn-by-turn calculation failed:",
            directionError
          )

          cleanSteps = []
        }
      }


      setSteps(cleanSteps)
      setCurrentStepIdx(0)


      /* =====================================================
         DISTANCE
      ===================================================== */

      let finalDistance =
        Number(
          data.distance_km
        )


      /*
       * If backend doesn't provide
       * road distance, calculate
       * straight-line display fallback.
       */

      if (
        !Number.isFinite(
          finalDistance
        ) &&
        dest
      ) {
        const destLat =
          Number(
            dest.latitude ??
            dest.lat
          )


        const destLng =
          Number(
            dest.longitude ??
            dest.lng
          )


        if (
          Number.isFinite(
            destLat
          ) &&
          Number.isFinite(
            destLng
          )
        ) {
          finalDistance =
            calculateDistance(
              position.lat,
              position.lng,
              destLat,
              destLng
            )
        }
      }


      if (
        Number.isFinite(
          finalDistance
        )
      ) {
        setDistance(
          finalDistance
        )
      } else {
        setDistance(null)
      }


      /* =====================================================
         DURATION
      ===================================================== */

      const serverDuration =
        Number(
          data.duration_min
        )


      if (
        Number.isFinite(
          serverDuration
        )
      ) {
        setDurationMin(
          serverDuration
        )
      } else if (
        Number.isFinite(
          finalDistance
        )
      ) {
        /*
         * Display-only estimate.
         */

        setDurationMin(
          Math.round(
            finalDistance * 1.6
          )
        )
      } else {
        setDurationMin(null)
      }


      /* =====================================================
         SERVER NOTE
      ===================================================== */

      setNote(
        data.note || null
      )


      initialRouteLoaded.current =
        true

    } catch (err) {
      console.error(
        "Navigation error:",
        err?.response?.data ||
        err?.message ||
        err
      )


      /*
       * Ignore stale errors.
       */

      if (
        currentRequestId !==
        requestIdRef.current
      ) {
        return
      }


      setError(
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Unable to calculate route."
      )


      /*
       * IMPORTANT:
       *
       * Never create fake coordinates,
       * fake route geometry,
       * fake directions,
       * or fake distance.
       */

      setDestination(null)
      setRoute([])
      setSteps([])
      setDistance(null)
      setDurationMin(null)
      setNote(null)

    } finally {
      if (
        currentRequestId ===
        requestIdRef.current
      ) {
        setLoading(false)
      }
    }
  }


  /* =======================================================
     INITIAL ROUTE
  ======================================================= */

  useEffect(() => {
    if (!position) {
      return
    }


    if (
      initialRouteLoaded.current
    ) {
      return
    }


    handleGetRoute(
      "Pokhara"
    )
  }, [position])


  /* =======================================================
     RECALCULATE WHEN ROUTE TYPE CHANGES
     
     IMPORTANT:
     
     This effect does NOT depend on
     destinationQuery or a callback.
     
     Therefore typing in the search box
     does not automatically request routes.
  ======================================================= */

  const previousRouteType =
    useRef(routeType)


  useEffect(() => {
    if (!position) {
      return
    }


    if (
      !initialRouteLoaded.current
    ) {
      previousRouteType.current =
        routeType

      return
    }


    if (
      previousRouteType.current ===
      routeType
    ) {
      return
    }


    previousRouteType.current =
      routeType


    if (
      !destinationQuery.trim()
    ) {
      return
    }


    handleGetRoute(
      destinationQuery
    )
  }, [
    routeType,
    position,
  ])


  /* =======================================================
     CURRENT STEP
  ======================================================= */

  const currentStep =
    steps[currentStepIdx] ||
    steps[0] ||
    null


  const TurnIcon =
    TURN_ICONS[
      currentStep?.icon
    ] ||
    TURN_ICONS[
      currentStep?.turn
    ] ||
    FiArrowUp


  /* =======================================================
     DESTINATION COORDINATES
  ======================================================= */

  const destinationLat =
    destination
      ? Number(
          destination.latitude ??
          destination.lat
        )
      : null


  const destinationLng =
    destination
      ? Number(
          destination.longitude ??
          destination.lng
        )
      : null


  const hasDestinationCoordinates =
    Number.isFinite(
      destinationLat
    ) &&
    Number.isFinite(
      destinationLng
    )


  /* =======================================================
     ACTIVE ROUTE TYPE
  ======================================================= */

  const activeRouteType =
    ROUTE_TYPES.find(
      (type) =>
        type.id === routeType
    )


  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div className="container-app py-6 space-y-6 animate-fadeIn">

      {/* =================================================
          HEADER
      ================================================= */}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">

        <div>

          <div className="flex items-center gap-2 flex-wrap">

            <span className="px-3 py-1 rounded-full bg-amber-400 text-gray-950 text-xs font-black uppercase tracking-wider flex items-center gap-1.5 shadow-md shadow-amber-400/20">

              <FiRadio className="animate-pulse text-red-600" />

              Tactical Game HUD Mode

            </span>

            <span className="text-xs text-gray-500 font-medium">

              GPS Navigation

            </span>

          </div>


          <h1 className="text-3xl font-black text-gray-900 tracking-tight mt-1 flex items-center gap-2">

            <FiNavigation className="text-purple-700" />

            Nepal Route Navigation & HUD

          </h1>

        </div>


        {/* HUD CONTROLS */}

        <div className="flex items-center gap-2 flex-wrap">

          <button
            type="button"
            onClick={() =>
              setGameMode(
                (current) => !current
              )
            }
            className={`
              px-4
              py-2
              rounded-xl
              text-xs
              font-extrabold
              flex
              items-center
              gap-2
              transition-all
              ${
                gameMode
                  ? "bg-purple-900 text-amber-300 shadow-lg shadow-purple-950/30 ring-2 ring-amber-400"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }
            `}
          >

            <FiTarget />

            {gameMode
              ? "🎮 Game HUD: ON"
              : "🗺️ Standard Map"}

          </button>


          <button
            type="button"
            onClick={() =>
              setSatelliteView(
                (current) => !current
              )
            }
            className={`
              px-3.5
              py-2
              rounded-xl
              text-xs
              font-bold
              flex
              items-center
              gap-1.5
              transition-all
              ${
                satelliteView
                  ? "bg-emerald-700 text-white shadow-lg"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }
            `}
          >

            <FiLayers />

            {satelliteView
              ? "🛰️ Satellite"
              : "🗺️ Terrain"}

          </button>

        </div>

      </div>


      {/* =================================================
          QUICK ROUTES
      ================================================= */}

      <div className="flex overflow-x-auto gap-2 pb-2 no-scrollbar">

        {QUICK_INTERNAL_ROUTES.map(
          (qr) => (

            <button
              key={qr.dest}
              type="button"
              onClick={() => {
                setDestinationQuery(
                  qr.dest
                )

                handleGetRoute(
                  qr.dest
                )
              }}
              disabled={
                loading ||
                !position
              }
              className="
                px-3.5
                py-1.5
                rounded-xl
                bg-white
                hover:bg-purple-50
                border
                border-purple-100
                text-purple-900
                text-xs
                font-bold
                whitespace-nowrap
                shadow-sm
                transition-all
                hover:border-purple-300
                disabled:opacity-50
                disabled:cursor-not-allowed
              "
            >

              {qr.label}

            </button>
          )
        )}

      </div>


      {/* =================================================
          SEARCH
      ================================================= */}

      <form
        onSubmit={(event) => {
          event.preventDefault()

          handleGetRoute()
        }}
        className="flex flex-col sm:flex-row gap-3"
      >

        <div className="relative flex-1">

          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-purple-600" />

          <input
            className="input-field pl-11 text-sm font-medium"
            placeholder="Search any destination in Nepal..."
            value={destinationQuery}
            onChange={(event) =>
              setDestinationQuery(
                event.target.value
              )
            }
          />

        </div>


        <button
          type="submit"
          disabled={
            loading ||
            !position
          }
          className="
            btn-primary
            px-8
            py-3
            bg-gradient-to-r
            from-purple-700
            to-rose-600
            hover:from-purple-800
            hover:to-rose-700
            text-white
            font-bold
            rounded-xl
            shadow-lg
            transition-all
            disabled:opacity-50
            disabled:cursor-not-allowed
          "
        >

          {loading
            ? "Calculating..."
            : !position
              ? "Waiting for GPS..."
              : "Find Route & Start HUD"}

        </button>

      </form>


      {/* =================================================
          ROUTE TYPES
      ================================================= */}

      <div className="flex flex-wrap gap-2">

        {ROUTE_TYPES.map(
          (type) => {
            const Icon =
              type.icon

            const isActive =
              routeType ===
              type.id


            return (
              <button
                key={type.id}
                type="button"
                disabled={
                  !type.available ||
                  loading ||
                  !position
                }
                onClick={() => {
                  if (
                    !type.available
                  ) {
                    return
                  }

                  setRouteType(
                    type.id
                  )
                }}
                title={
                  type.label
                }
                className={`
                  flex
                  items-center
                  gap-1.5
                  text-sm
                  font-medium
                  px-3.5
                  py-2
                  rounded-xl
                  transition-all
                  ${
                    isActive
                      ? "bg-himalaya-500 text-white shadow-md"
                      : "bg-white border border-gray-200 text-gray-600 hover:border-himalaya-300"
                  }
                  disabled:opacity-50
                  disabled:cursor-not-allowed
                `}
              >

                <Icon size={14} />

                {type.shortLabel}

              </button>
            )
          }
        )}

      </div>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (

        <div className="
          text-sm
          text-nepalred-500
          bg-nepalred-50
          border
          border-nepalred-100
          rounded-xl
          px-4
          py-3
        ">

          {error}

        </div>

      )}


      {/* =================================================
          ROUTE SUMMARY
      ================================================= */}

      {distance != null && (

        <motion.div
          initial={{
            opacity: 0,
            y: 6,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          className="
            card-base
            p-4
            inline-flex
            flex-wrap
            items-center
            gap-2
            text-sm
          "
        >

          <span>
            Distance:
          </span>

          <b className="text-himalaya-600">

            {formatDistance(
              distance
            )}

          </b>


          {durationMin != null && (
            <>
              <span className="text-gray-300">
                ·
              </span>

              <span>

                {formatDuration(
                  durationMin
                )}

              </span>
            </>
          )}


          {activeRouteType && (
            <span className="text-xs text-gray-400">

              ·{" "}
              {activeRouteType.label}

            </span>
          )}

        </motion.div>

      )}


      {/* =================================================
          SERVER NOTE
      ================================================= */}

      {note && (

        <div className="
          text-xs
          text-gray-500
          bg-gray-50
          border
          border-gray-100
          rounded-xl
          px-4
          py-3
        ">

          {note}

        </div>

      )}


      {/* =================================================
          GAME HUD
      ================================================= */}

      {gameMode && (

        <motion.div
          initial={{
            opacity: 0,
            scale: 0.98,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
          className="
            relative
            bg-gradient-to-r
            from-[#0c0217]
            via-[#1c042e]
            to-[#26052b]
            border-2
            border-purple-500/60
            rounded-3xl
            p-5
            sm:p-6
            shadow-2xl
            text-white
            overflow-hidden
          "
        >

          {/* HUD GRID */}

          <div className="
            absolute
            inset-0
            bg-[radial-gradient(#a855f7_1px,transparent_1px)]
            [background-size:20px_20px]
            opacity-15
            pointer-events-none
          " />


          {/* =================================================
              TOP MANEUVER
          ================================================= */}

          <div className="
            relative
            z-10
            flex
            flex-col
            md:flex-row
            items-center
            justify-between
            gap-4
            border-b
            border-purple-700/50
            pb-5
          ">

            <div className="
              flex
              items-center
              gap-4
              w-full
              md:w-auto
            ">

              <div className="
                w-16
                h-16
                rounded-2xl
                bg-amber-400
                text-gray-950
                flex
                items-center
                justify-center
                font-black
                shadow-lg
                shadow-amber-400/30
                shrink-0
              ">

                <TurnIcon size={36} />

              </div>


              <div className="min-w-0">

                <div className="
                  flex
                  items-center
                  gap-2
                ">

                  <span className="
                    text-xs
                    font-black
                    uppercase
                    tracking-widest
                    text-amber-300
                  ">

                    NEXT MANEUVER

                    {currentStep
                      ? ` · ${formatDistance(
                          currentStep.distanceKm || 0
                        )}`
                      : ""}

                  </span>


                  <span className="
                    w-2
                    h-2
                    rounded-full
                    bg-emerald-400
                    animate-ping
                  " />

                </div>


                <h2 className="
                  text-xl
                  sm:text-2xl
                  font-black
                  text-white
                  leading-tight
                  break-words
                ">

                  {currentStep?.instruction ||
                    (
                      loading
                        ? "Calculating route..."
                        : `Head towards ${destinationQuery}`
                    )}

                </h2>

              </div>

            </div>


            {/* OBJECTIVE */}

            <div className="
              bg-purple-950/80
              border
              border-purple-500/40
              px-4
              py-2.5
              rounded-2xl
              text-right
              shrink-0
            ">

              <p className="
                text-[10px]
                text-purple-300
                uppercase
                font-black
                tracking-widest
              ">

                🎯 CURRENT OBJECTIVE

              </p>


              <p className="
                text-base
                font-extrabold
                text-amber-300
              ">

                {destination?.name ||
                  destinationQuery}

              </p>


              <p className="
                text-[11px]
                text-purple-200
              ">

                Remaining:{" "}

                <b className="text-white">

                  {distance != null
                    ? formatDistance(
                        distance
                      )
                    : "—"}

                </b>

                {" · "}

                {durationMin != null
                  ? formatDuration(
                      durationMin
                    )
                  : "—"}

              </p>

            </div>

          </div>


          {/* =================================================
              HUD INSTRUMENTS
          ================================================= */}

          <div className="
            relative
            z-10
            grid
            grid-cols-2
            sm:grid-cols-4
            gap-4
            my-5
          ">

            {/* SPEED */}

            <div className="
              bg-black/40
              border
              border-purple-800/60
              p-3
              rounded-2xl
              text-center
            ">

              <p className="
                text-[10px]
                text-purple-300
                uppercase
                font-bold
                tracking-wider
              ">

                GPS Speed

              </p>


              <p className="
                text-2xl
                font-black
                text-emerald-400
                mt-0.5
              ">

                {speedKmh}

                <span className="
                  text-xs
                  text-white
                ">

                  {" "}KM/H

                </span>

              </p>

            </div>


            {/* COMPASS */}

            <div className="
              bg-black/40
              border
              border-purple-800/60
              p-3
              rounded-2xl
              text-center
            ">

              <p className="
                text-[10px]
                text-purple-300
                uppercase
                font-bold
                tracking-wider
              ">

                Compass Bearing

              </p>


              <p className="
                text-2xl
                font-black
                text-amber-300
                mt-0.5
              ">

                {compassBearing}

              </p>

            </div>


            {/* ALTITUDE */}

            <div className="
              bg-black/40
              border
              border-purple-800/60
              p-3
              rounded-2xl
              text-center
            ">

              <p className="
                text-[10px]
                text-purple-300
                uppercase
                font-bold
                tracking-wider
              ">

                Current Altitude

              </p>


              <p className="
                text-2xl
                font-black
                text-cyan-300
                mt-0.5
              ">

                {altitudeM != null
                  ? altitudeM
                  : "—"}

                <span className="
                  text-xs
                  text-white
                ">

                  {" "}M

                </span>

              </p>

            </div>


            {/* ROUTE STATUS */}

            <div className="
              bg-black/40
              border
              border-purple-800/60
              p-3
              rounded-2xl
              text-center
            ">

              <p className="
                text-[10px]
                text-purple-300
                uppercase
                font-bold
                tracking-wider
              ">

                Route Status

              </p>


              <p className="
                text-lg
                font-black
                text-emerald-300
                mt-1
              ">

                {normalizedRoute.length > 1
                  ? "ROUTE READY"
                  : loading
                    ? "CALCULATING"
                    : "NO ROUTE"}

              </p>

            </div>

          </div>


          {/* =================================================
              STEP NAVIGATION
          ================================================= */}

          {steps.length > 1 && (

            <div className="
              relative
              z-10
              flex
              items-center
              justify-between
              pt-2
              border-t
              border-purple-800/40
              text-xs
              text-purple-200
            ">

              <span>

                Step{" "}
                {currentStepIdx + 1}
                {" "}of{" "}
                {steps.length}

              </span>


              <div className="flex gap-2">

                <button
                  type="button"
                  disabled={
                    currentStepIdx === 0
                  }
                  onClick={() =>
                    setCurrentStepIdx(
                      (previous) =>
                        Math.max(
                          0,
                          previous - 1
                        )
                    )
                  }
                  className="
                    px-3
                    py-1
                    bg-purple-900/60
                    hover:bg-purple-800
                    rounded-lg
                    disabled:opacity-30
                  "
                >

                  Previous Turn

                </button>


                <button
                  type="button"
                  disabled={
                    currentStepIdx ===
                    steps.length - 1
                  }
                  onClick={() =>
                    setCurrentStepIdx(
                      (previous) =>
                        Math.min(
                          steps.length - 1,
                          previous + 1
                        )
                    )
                  }
                  className="
                    px-3
                    py-1
                    bg-amber-400
                    hover:bg-amber-500
                    text-gray-950
                    font-bold
                    rounded-lg
                    disabled:opacity-30
                  "
                >

                  Next Turn

                </button>

              </div>

            </div>

          )}

        </motion.div>

      )}


      {/* =================================================
          MAP + DIRECTIONS
      ================================================= */}

      <div className="
        grid
        grid-cols-1
        lg:grid-cols-3
        gap-6
      ">

        {/* MAP */}

        <div className="
          lg:col-span-2
          rounded-2xl
          overflow-hidden
          shadow-2xl
          border
          border-gray-200
        ">

          <MapView
            userLocation={
              position
            }

            destination={
              destination
            }

            route={
              normalizedRoute
            }

            height="520px"

            satellite={
              satelliteView
            }

            satelliteView={
              satelliteView
            }
          />

        </div>


        {/* RIGHT PANEL */}

        <div className="space-y-4">

          {/* TURN BY TURN */}

          <div className="
            card-base
            p-5
            shadow-lg
            border
            border-purple-100
            rounded-2xl
          ">

            <div className="
              flex
              items-center
              justify-between
              mb-4
            ">

              <h3 className="
                font-bold
                text-base
                text-gray-900
                flex
                items-center
                gap-2
              ">

                <FiCompass className="text-purple-700" />

                Turn-by-Turn Route

              </h3>


              <span className="
                text-xs
                px-2.5
                py-1
                rounded-full
                bg-purple-50
                text-purple-700
                font-bold
              ">

                {steps.length} Steps

              </span>

            </div>


            {steps.length > 0 ? (

              <ol className="
                space-y-3
                max-h-[420px]
                overflow-y-auto
                pr-1
              ">

                {steps.map(
                  (step, idx) => {
                    const Icon =
                      TURN_ICONS[
                        step.icon
                      ] ||
                      TURN_ICONS[
                        step.turn
                      ] ||
                      FiArrowUp


                    const isCurrent =
                      idx ===
                      currentStepIdx


                    const stepDistance =
                      Number(
                        step.distanceKm ??
                        step.distance_km ??
                        0
                      )


                    return (

                      <li
                        key={idx}
                        onClick={() =>
                          setCurrentStepIdx(
                            idx
                          )
                        }
                        className={`
                          p-3
                          rounded-xl
                          cursor-pointer
                          transition-all
                          flex
                          items-start
                          gap-3
                          border
                          ${
                            isCurrent
                              ? "bg-purple-50 border-purple-400 shadow-sm"
                              : "hover:bg-gray-50 border-gray-100"
                          }
                        `}
                      >

                        <div className={`
                          w-9
                          h-9
                          rounded-xl
                          flex
                          items-center
                          justify-center
                          font-bold
                          shrink-0
                          ${
                            isCurrent
                              ? "bg-amber-400 text-gray-950 shadow"
                              : "bg-gray-100 text-gray-600"
                          }
                        `}>

                          <Icon size={18} />

                        </div>


                        <div className="min-w-0">

                          <p className="
                            text-xs
                            font-bold
                            text-gray-800
                            leading-snug
                          ">

                            {step.instruction}

                          </p>


                          {stepDistance > 0 && (

                            <p className="
                              text-[11px]
                              text-gray-400
                              mt-1
                            ">

                              {formatDistance(
                                stepDistance
                              )}

                            </p>

                          )}

                        </div>

                      </li>

                    )
                  }
                )}

              </ol>

            ) : (

              <p className="
                text-sm
                text-gray-400
              ">

                {loading
                  ? "Calculating turn-by-turn directions..."
                  : normalizedRoute.length > 1
                    ? "Calculating turn-by-turn directions..."
                    : "Get a route to see step-by-step directions here."}

              </p>

            )}

          </div>


          {/* MAPILLARY */}

          {hasDestinationCoordinates && (

            <div className="
              card-base
              p-5
              shadow-lg
              border
              border-purple-100
              rounded-2xl
            ">

              <h4 className="
                font-bold
                text-sm
                text-gray-800
                mb-2
              ">

                Street-Level Imagery & Views

              </h4>


              <MapillaryImages
                latitude={
                  destinationLat
                }

                longitude={
                  destinationLng
                }

                limit={6}
              />

            </div>

          )}

        </div>

      </div>

    </div>
  )
}


export default Navigation
