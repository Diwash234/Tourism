import { useCallback, useEffect, useRef, useState } from "react"
import axiosClient from "../api/axiosClient"

/**
 * useTurnByTurn — live navigation state machine over the road-routing
 * subsystem (POST /navigation/road-route/ + /navigation/progress/).
 *
 * States: IDLE -> GETTING_LOCATION -> LOADING_ROUTE -> ROUTE_PREVIEW
 *         -> NAVIGATING -> REROUTING -> ARRIVED  (errors -> ERROR)
 *
 * GPS: navigator.geolocation.watchPosition (high accuracy, 3 s cache).
 * Throttling: map marker updates immediately; progress requests at most
 * every PROGRESS_INTERVAL_MS; reroute only when the backend says
 * reroute_required (accuracy-aware hysteresis lives server-side).
 */
export const NAV_STATES = {
  IDLE: "IDLE",
  GETTING_LOCATION: "GETTING_LOCATION",
  LOADING_ROUTE: "LOADING_ROUTE",
  ROUTE_PREVIEW: "ROUTE_PREVIEW",
  NAVIGATING: "NAVIGATING",
  REROUTING: "REROUTING",
  ARRIVED: "ARRIVED",
  ERROR: "ERROR",
}

const PROGRESS_INTERVAL_MS = 6000
const REROUTE_COOLDOWN_MS = 15000

export default function useTurnByTurn({ destination, mode = "driving", voice = false, stops = null }) {
  const [state, setState] = useState(NAV_STATES.IDLE)
  const [position, setPosition] = useState(null) // {latitude, longitude, heading, accuracy}
  const [route, setRoute] = useState(null)       // canonical route + route_id
  const [steps, setSteps] = useState([])
  const [progress, setProgress] = useState(null) // last progress response
  const [error, setError] = useState("")
  const [connectionLost, setConnectionLost] = useState(false)
  const [alternatives, setAlternatives] = useState([])
  const [legs, setLegs] = useState(null)        // itinerary mode
  const [activeLeg, setActiveLeg] = useState(0)
  const [context, setContext] = useState(null)  // safety/weather layers

  const watchId = useRef(null)
  const lastProgressAt = useRef(0)
  const lastRerouteAt = useRef(0)
  const lastGoodFix = useRef(null)
  const apiFailures = useRef(0)
  const legsRef = useRef(null)
  const activeLegRef = useRef(0)
  useEffect(() => { legsRef.current = legs }, [legs])
  useEffect(() => { activeLegRef.current = activeLeg }, [activeLeg])
  const spokenRef = useRef("")
  const stateRef = useRef(state)
  const routeRef = useRef(route)
  useEffect(() => { stateRef.current = state }, [state])
  useEffect(() => { routeRef.current = route }, [route])

  const speak = useCallback((text) => {
    if (!voice || !text || typeof window === "undefined" || !window.speechSynthesis) return
    if (spokenRef.current === text) return
    spokenRef.current = text
    try {
      window.speechSynthesis.cancel()
      const utter = new window.SpeechSynthesisUtterance(text)
      utter.rate = 1.0
      window.speechSynthesis.speak(utter)
    } catch { /* speech is best-effort */ }
  }, [voice])

  const stopWatch = useCallback(() => {
    if (watchId.current !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchId.current)
      watchId.current = null
    }
  }, [])

  const loadContext = useCallback(async (routeId) => {
    if (!routeId) return
    try {
      const { data } = await axiosClient.get("/navigation/route-context/", {
        params: { route_id: routeId },
      })
      if (data.status === "success") setContext(data)
    } catch { /* context is best-effort */ }
  }, [])

  const loadRoute = useCallback(async (fromPos, autoStart = false) => {
    if (!destination?.latitude || !destination?.longitude) {
      setError("Destination has no coordinates")
      setState(NAV_STATES.ERROR)
      return
    }
    setState(autoStart ? NAV_STATES.REROUTING : NAV_STATES.LOADING_ROUTE)
    setError("")
    try {
      const { data } = await axiosClient.post("/navigation/road-route/", {
        start: fromPos
          ? { latitude: fromPos.latitude, longitude: fromPos.longitude }
          : position
            ? { latitude: position.latitude, longitude: position.longitude }
            : { latitude: destination.latitude, longitude: destination.longitude },
        destination: { latitude: destination.latitude, longitude: destination.longitude },
        mode,
        alternatives: true,
      })
      if (data.status !== "success") throw new Error(data.error || "routing failed")
      setRoute(data.route)
      setSteps(data.steps || [])
      setAlternatives(data.alternatives || [])
      setState(autoStart ? NAV_STATES.NAVIGATING : NAV_STATES.ROUTE_PREVIEW)
      loadContext(data.route.route_id)
      return data.route
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Could not load route"
      if (autoStart && routeRef.current) {
        // reroute failed (transient API issue): keep navigating the old
        // route instead of killing the session.
        setError(`Reroute failed (${msg}) — continuing on current route`)
        setState(NAV_STATES.NAVIGATING)
        return routeRef.current
      }
      setError(msg)
      setState(NAV_STATES.ERROR)
      return null
    }
  }, [destination, mode, position])

  const sendProgress = useCallback(async (pos) => {
    const rt = routeRef.current
    if (!rt?.route_id) return
    try {
      const { data } = await axiosClient.post("/navigation/progress/", {
        route_id: rt.route_id,
        latitude: pos.latitude,
        longitude: pos.longitude,
        heading: pos.heading ?? null,
        accuracy: pos.accuracy ?? null,
      })
      setProgress(data)
      apiFailures.current = 0
      setConnectionLost(false)
      if (data.arrived) {
        setState(NAV_STATES.ARRIVED)
        const inItinerary = legsRef.current &&
          activeLegRef.current < legsRef.current.length - 1
        speak(inItinerary ? "You have arrived. Next stop ready."
                          : "You have arrived at your destination")
        if (!inItinerary) stopWatch()
        return
      }
      if (data.reroute_required) {
        const now = Date.now()
        if (now - lastRerouteAt.current > REROUTE_COOLDOWN_MS) {
          lastRerouteAt.current = now
          setState(NAV_STATES.REROUTING)
          speak("Recalculating route")
          await loadRoute(pos, true)
        }
        return
      }
      if (stateRef.current === NAV_STATES.REROUTING) setState(NAV_STATES.NAVIGATING)
      if (data.next_instruction?.instruction) speak(data.next_instruction.instruction)
    } catch {
      // progress polls are best-effort; keep navigating on the last known
      // state and surface an outage banner after consecutive failures.
      apiFailures.current += 1
      if (apiFailures.current >= 2) setConnectionLost(true)
    }
  }, [speak, stopWatch])



  const selectAlternative = useCallback(async (index) => {
    const rt = routeRef.current
    if (!rt?.route_id) return
    try {
      const { data } = await axiosClient.post("/navigation/select-alternative/", {
        route_id: rt.route_id, index,
      })
      if (data.status === "success") {
        setRoute(data.route)
        setSteps(data.steps || [])
        setAlternatives([])
        loadContext(data.route.route_id)
      }
    } catch { /* keep current route on failure */ }
  }, [loadContext])

  const hasStops = Array.isArray(stops) && stops.length > 0

  const loadItinerary = useCallback(async () => {
    if (!destination || !hasStops) return null
    setState(NAV_STATES.LOADING_ROUTE)
    setError("")
    try {
      const { data } = await axiosClient.post("/navigation/itinerary-route/", {
        start: { latitude: destination.latitude, longitude: destination.longitude },
        stops, mode,
      })
      if (data.status !== "success") throw new Error("itinerary routing failed")
      setLegs(data.legs)
      setActiveLeg(0)
      const leg = data.legs[0]
      setRoute(leg)
      setSteps(leg.steps || [])
      setAlternatives([])
      setState(NAV_STATES.ROUTE_PREVIEW)
      loadContext(leg.route_id)
      return data
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || "Itinerary routing failed")
      setState(NAV_STATES.ERROR)
      return null
    }
  }, [destination, hasStops, mode, loadContext])


  const start = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not available in this browser")
      setState(NAV_STATES.ERROR)
      return
    }
    if (legsRef.current === null && hasStops) {
      loadItinerary().then((data) => { if (!data) return })
    }
    setState(NAV_STATES.GETTING_LOCATION)
    stopWatch()
    let firstFix = true
    watchId.current = navigator.geolocation.watchPosition(
      (p) => {
        const pos = {
          latitude: p.coords.latitude,
          longitude: p.coords.longitude,
          heading: p.coords.heading ?? null,
          accuracy: p.coords.accuracy ?? null,
          timestamp: p.coords.timestamp ?? Date.now(),
        }
        // Anti-jump filter: discard fixes with terrible accuracy or
        // physically impossible movement (GPS spikes in canyons/tunnels).
        const prev = lastGoodFix.current
        if (pos.accuracy != null && pos.accuracy > 100) return
        if (prev) {
          const dt = Math.max(1, (pos.timestamp - prev.timestamp) / 1000)
          const dLat = (pos.latitude - prev.latitude) * 111320
          const dLng = (pos.longitude - prev.longitude) * 111320 *
            Math.cos((pos.latitude * Math.PI) / 180)
          const speed = Math.hypot(dLat, dLng) / dt
          if (speed > 55) return // > ~200 km/h -> GPS spike, ignore
        }
        lastGoodFix.current = pos
        setPosition(pos) // marker updates immediately
        if (firstFix) {
          firstFix = false
          setState(NAV_STATES.NAVIGATING)
          sendProgress(pos)
          lastProgressAt.current = Date.now()
          return
        }
        const now = Date.now()
        if (now - lastProgressAt.current >= PROGRESS_INTERVAL_MS) {
          lastProgressAt.current = now
          sendProgress(pos)
        }
      },
      (err) => {
        setError(err?.message || "Location permission denied")
        setState(NAV_STATES.ERROR)
      },
      { enableHighAccuracy: true, maximumAge: 3000, timeout: 10000 },
    )
  }, [sendProgress, stopWatch, hasStops, loadItinerary])

  const preview = useCallback(async () => {
    const from = position || (navigator.geolocation
      ? await new Promise((resolve) => {
        setState(NAV_STATES.GETTING_LOCATION)
        navigator.geolocation.getCurrentPosition(
          (p) => resolve({ latitude: p.coords.latitude, longitude: p.coords.longitude, accuracy: p.coords.accuracy }),
          () => resolve(null),
          { enableHighAccuracy: true, timeout: 8000 },
        )
      })
      : null)
    if (from) setPosition((prev) => prev || from)
    return loadRoute(from, false)
  }, [loadRoute, position, hasStops, loadItinerary])

  const end = useCallback(() => {
    stopWatch()
    setState(NAV_STATES.IDLE)
    setProgress(null)
  }, [stopWatch])

  const nextStop = useCallback(() => {
    const ls = legsRef.current
    if (!ls) return
    const nextIdx = activeLegRef.current + 1
    if (nextIdx >= ls.length) { end(); return }
    setActiveLeg(nextIdx)
    const leg = ls[nextIdx]
    setRoute(leg)
    setSteps(leg.steps || [])
    setProgress(null)
    setAlternatives([])
    setState(NAV_STATES.NAVIGATING)
    loadContext(leg.route_id)
  }, [loadContext])

  useEffect(() => stopWatch, [stopWatch])

  return {
    state, position, route, steps, progress, error, connectionLost,
    alternatives, legs, activeLeg, context,
    start, preview, end, speak, selectAlternative, nextStop,
  }
}
