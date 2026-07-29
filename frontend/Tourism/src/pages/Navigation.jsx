import { useState } from "react";
import { motion } from "framer-motion";
import MapView from "../components/map/MapView";
import useGeolocation from "../hooks/useGeolocation";
import { FiNavigation, FiMapPin, FiZap, FiShield, FiDollarSign, FiTrendingUp, FiLock } from "react-icons/fi";
import navigationApi from "../api/navigationApi";

// NEW: route-type options. IMPORTANT — only "fastest" is real right now.
// The backend (tourist/utils.py: get_ml_best_route) and the ML
// microservice it calls (/routes/best-route) take only start/end
// coordinates — there is no route_type parameter anywhere in that chain
// yet. Rather than build 4 buttons that all silently do the same thing
// (which would be actively misleading), the other three are shown but
// disabled with a clear "not supported yet" badge. `route_type` is still
// sent in the request body below so the ML service can start reading it
// the moment it's implemented, with zero frontend changes needed then.
const ROUTE_TYPES = [
  { id: "fastest", label: "Fastest", icon: FiZap, available: true },
  { id: "safest", label: "Safest", icon: FiShield, available: false },
  { id: "cheapest", label: "Cheapest", icon: FiDollarSign, available: false },
  { id: "trekking", label: "Trekking", icon: FiTrendingUp, available: false },
];

// Haversine distance — this function already existed in the original file
// but was never actually called, so the "Distance" readout in the UI was
// permanently stuck at null. Wired up below.
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return (R * c).toFixed(2);
};

const Navigation = () => {
  const { position } = useGeolocation();

  const [destinationQuery, setDestinationQuery] = useState("");
  const [destination, setDestination] = useState(null);
  const [route, setRoute] = useState([]);
  const [routeType, setRouteType] = useState("fastest");
  const [distance, setDistance] = useState(null);
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

    try {
      const payload = {
        start_latitude: position.lat,
        start_longitude: position.lng,
        destination_name: destinationQuery,
        route_type: routeType, // forward-compatible; backend ignores it today, see note above
      };

      const response = await navigationApi.getRoute(payload);
      const dest = response.data.destination || null;

      setDestination(dest);
      setRoute(response.data.route || []);

      // FIXED: this was dead code before — calculateDistance existed but
      // nothing ever called it, so "Distance" never showed anything.
      if (dest?.latitude && dest?.longitude) {
        setDistance(
          calculateDistance(position.lat, position.lng, Number(dest.latitude), Number(dest.longitude))
        );
      }
    } catch (error) {
      console.error("Navigation error:", error.response?.data || error.message);
      setError(error.response?.data?.detail || error.response?.data?.message || error.message || "Something went wrong");
      setRoute([]);
    } finally {
      setLoading(false);
    }
  };

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

      {/* NEW: route type selector */}
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

      {distance && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-base p-4 mb-4 inline-flex items-center gap-2 text-sm"
        >
          Distance: <b className="text-himalaya-600">{distance} km</b>
          <span className="text-xs text-gray-400">· {ROUTE_TYPES.find((t) => t.id === routeType)?.label} route</span>
        </motion.div>
      )}

      {error && (
        <p className="text-sm text-nepalred-500 bg-nepalred-50 rounded-xl px-4 py-3 mb-4">{error}</p>
      )}

      <div className="rounded-xl2 overflow-hidden shadow-premium">
        <MapView userLocation={position} destination={destination} route={route} height="500px" />
      </div>
    </div>
  );
};

export default Navigation;