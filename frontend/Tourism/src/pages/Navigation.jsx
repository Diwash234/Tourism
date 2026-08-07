import { useState } from "react";
import { motion } from "framer-motion";
import MapView from "../components/map/MapView";
import MapillaryImages from "../components/map/MapillaryImages";
import useGeolocation from "../hooks/useGeolocation";
import {
  FiNavigation,
  FiMapPin,
  FiZap,
  FiShield,
  FiDollarSign,
  FiTrendingUp,
  FiLock,
  FiArrowLeft,
  FiArrowRight,
  FiArrowUp,
  FiRotateCcw,
  FiChevronLeft,
  FiChevronRight,
} from "react-icons/fi";
import navigationApi from "../api/navigationApi";
import { formatDistance, formatDuration } from "../utils/formatDistance";

// Route-type options. "fastest" is backed by the graphml road graph; the
// others are still being wired to real per-route cost/risk data.
const ROUTE_TYPES = [
  { id: "fastest", label: "Fastest", icon: FiZap, available: true },
  { id: "safest", label: "Safest", icon: FiShield, available: true },
  { id: "cheapest", label: "Cheapest", icon: FiDollarSign, available: true },
  { id: "trekking", label: "Trekking", icon: FiTrendingUp, available: false },
];

// Turn icon per step direction (Google-Maps style).
const TURN_ICONS = {
  start: FiArrowUp,
  straight: FiArrowUp,
  left: FiArrowLeft,
  right: FiArrowRight,
  sharp_left: FiChevronLeft,
  sharp_right: FiChevronRight,
  uturn: FiRotateCcw,
};

const Navigation = () => {
  const { position } = useGeolocation();

  const [destinationQuery, setDestinationQuery] = useState("");
  const [destination, setDestination] = useState(null);
  const [route, setRoute] = useState([]);
  const [routeType, setRouteType] = useState("fastest");
  const [distance, setDistance] = useState(null);
  const [steps, setSteps] = useState([]);
  const [durationMin, setDurationMin] = useState(null);
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGetRoute = async (e) => {
    e.preventDefault();
    setError("");

    if (!position) {
      setError("Waiting for GPS location — allow location access and try again.");
      return;
    }
    if (!destinationQuery.trim()) return;

    setLoading(true);
    setDistance(null);
    setSteps([]);
    setDurationMin(null);
    setNote(null);

    try {
      const payload = {
        start_latitude: position.lat,
        start_longitude: position.lng,
        destination_name: destinationQuery,
        route_type: routeType,
      };

      const response = await navigationApi.getRoute(payload);
      const dest = response.data.destination || null;

      setDestination(dest);
      setRoute(response.data.route || []);

      // NEW: the ML route engine now returns turn-by-turn directions
      // (left/right + distance in km/m) and an estimated duration,
      // computed from the graphml road graph.
      setSteps(response.data.steps || []);
      setDurationMin(response.data.duration_min ?? null);
      setNote(response.data.note || null);

      if (response.data.distance_km) {
        setDistance(response.data.distance_km);
      } else if (dest?.latitude && dest?.longitude) {
        // Fallback haversine straight-line distance.
        const R = 6371;
        const dLat = ((dest.latitude - position.lat) * Math.PI) / 180;
        const dLon = ((dest.longitude - position.lng) * Math.PI) / 180;
        const a =
          Math.sin(dLat / 2) ** 2 +
          Math.cos((position.lat * Math.PI) / 180) *
            Math.cos((dest.latitude * Math.PI) / 180) *
            Math.sin(dLon / 2) ** 2;
        setDistance(2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
      }
    } catch (error) {
      console.error("Navigation error:", error.response?.data || error.message);
      setError(error.response?.data?.detail || error.response?.data?.message || error.message || "Something went wrong");
      setRoute([]);
    } finally {
      setLoading(false);
    }
  };

  const destLat = destination?.latitude != null ? Number(destination.latitude) : null;
  const destLng = destination?.longitude != null ? Number(destination.longitude) : null;

  return (
    <div className="container-app py-10">
      <h1 className="section-title flex items-center gap-2">
        <FiNavigation />
        Navigation
      </h1>

      <form onSubmit={handleGetRoute} className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1">
          <FiMapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input-field pl-11"
            placeholder="Where are you going?"
            value={destinationQuery}
            onChange={(e) => setDestinationQuery(e.target.value)}
          />
        </div>
        <button className="btn-primary" disabled={loading}>
          {loading ? "Finding..." : "Get Route"}
        </button>
      </form>

      {/* Route type selector */}
      <div className="flex flex-wrap gap-2 mb-6">
        {ROUTE_TYPES.map((type) => {
          const Icon = type.icon;
          const isActive = routeType === type.id;
          return (
            <button
              key={type.id}
              type="button"
              disabled={!type.available}
              onClick={() => type.available && setRouteType(type.id)}
              title={type.available ? undefined : "Not supported by the routing service yet"}
              className={`flex items-center gap-1.5 text-sm font-medium px-3.5 py-2 rounded-xl transition-colors ${
                isActive
                  ? "bg-himalaya-500 text-white"
                  : type.available
                  ? "bg-white border border-gray-200 text-gray-600 hover:border-himalaya-300"
                  : "bg-gray-50 border border-gray-100 text-gray-300 cursor-not-allowed"
              }`}
            >
              <Icon size={14} />
              {type.label}
              {!type.available && <FiLock size={11} />}
            </button>
          );
        })}
      </div>

      {/* Summary */}
      {(distance != null || durationMin != null) && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-base p-4 mb-4 inline-flex flex-wrap items-center gap-x-4 gap-y-1 text-sm"
        >
          <span>
            Distance: <b className="text-himalaya-600">{formatDistance(distance)}</b>
          </span>
          {durationMin != null && (
            <span>
              Duration: <b className="text-himalaya-600">{formatDuration(durationMin)}</b>
            </span>
          )}
          <span className="text-xs text-gray-400">
            · {ROUTE_TYPES.find((t) => t.id === routeType)?.label} route
          </span>
          {note && <span className="text-xs text-amber-600 w-full">{note}</span>}
        </motion.div>
      )}

      {error && (
        <p className="text-sm text-nepalred-500 bg-nepalred-50 rounded-xl px-4 py-3 mb-4">{error}</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl2 overflow-hidden shadow-premium">
          <MapView userLocation={position} destination={destination} route={route} height="500px" />
        </div>

        {/* Turn-by-turn directions (Google-Maps style) */}
        <div className="space-y-4">
          {steps.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="card-base p-4"
            >
              <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
                <FiNavigation className="text-himalaya-500" /> Directions
                <span className="text-[11px] text-gray-400 font-normal ml-auto">
                  {steps.length} step{steps.length > 1 ? "s" : ""}
                </span>
              </h3>
              <ol className="space-y-0 max-h-[420px] overflow-y-auto">
                {steps.map((step, i) => {
                  const Icon = TURN_ICONS[step.turn] || FiArrowUp;
                  return (
                    <li key={i} className="flex gap-3 py-2 border-b border-gray-50 last:border-0">
                      <span
                        className={`mt-0.5 w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                          step.turn === "left" || step.turn === "right"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        <Icon size={15} />
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm text-gray-700 leading-snug">{step.instruction}</p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {formatDistance(step.distance_km)} · {step.distance_m} m
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ol>
            </motion.div>
          )}

          {/* Mapillary street imagery at the destination */}
          {destLat && destLng && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="card-base p-4"
            >
              <MapillaryImages latitude={destLat} longitude={destLng} />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Navigation;
