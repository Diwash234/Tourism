import { useEffect, useState } from "react";
import {
  FiSun,
  FiCloud,
  FiCloudRain,
  FiMapPin,
  FiHeart,
  FiUpload,
  FiSearch,
  FiImage,
} from "react-icons/fi";

import useAuth from "../hooks/useAuth";
import useGeolocation from "../hooks/useGeolocation";

import weatherApi from "../api/weatherApi";
import recommendationApi from "../api/recommendationApi";
import alertApi from "../api/alertApi";
import budgetApi from "../api/budgetApi";
import userApi from "../api/userApi";

import { destinationApi, photoApi } from "../services/api";

import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";

import BudgetCard from "../components/cards/BudgetCard";
import AlertCard from "../components/cards/AlertCard";
import RecommendationCard from "../components/cards/RecommendationCard";
import DestinationCard from "../components/cards/DestinationCard";

const weatherIcons = {
  clear: FiSun,
  clouds: FiCloud,
  rain: FiCloudRain,
};

// Small helper: every one of our paginated/ML endpoints returns
// { results: [...] } (or, for ML recommendations, { source, results: [...] }).
// Centralizing the unwrap here means we only have to get the shape right once.
function unwrapList(response) {
  return response?.data?.results || response?.data?.items || response?.data || [];
}

const Dashboard = () => {
  const { user } = useAuth();
  const { position } = useGeolocation();

  // Dashboard State
  const [weather, setWeather] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [budget, setBudget] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Community Upload State
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState("");
  const [status, setStatus] = useState("");
  const [myPhotos, setMyPhotos] = useState([]);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const [recRes, alertRes, budgetRes, favRes, destRes] = await Promise.all([
          recommendationApi.getPersonalized(),
          alertApi.getAlerts({ limit: 4 }),
          budgetApi.getSummary(),
          userApi.getFavorites(),
          destinationApi.list({ limit: 6, featured: true }),
        ]);

        setRecommendations(unwrapList(recRes));
        setAlerts(unwrapList(alertRes));
        setFavorites(unwrapList(favRes));
        setDestinations(unwrapList(destRes));

        // Budget summary is a single object, not a list — map the backend's
        // actual field names (total_amount/entry_count) to what the UI expects.
        setBudget({
          total: budgetRes?.data?.total_amount ?? 0,
          spent: budgetRes?.data?.total_amount ?? 0,
          entryCount: budgetRes?.data?.entry_count ?? 0,
          byCategory: budgetRes?.data?.by_category ?? [],
        });
      } catch (error) {
        console.log("Dashboard error:", error.response?.data || error.message);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  useEffect(() => {
    if (!position) return;

    weatherApi
      .getCurrentWeather({ lat: position.lat, lng: position.lng })
      .then((res) => setWeather(res.data))
      .catch((err) => console.log("Weather error:", err.message));
  }, [position]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      const { data } = await destinationApi.search(query);
      setResults(data.results || data || []);
    } catch (err) {
      console.log(err);
    }
  };

  const selectDestination = async (place) => {
    setSelected(place);
    try {
      const { data } = await photoApi.get(place.slug);
      setMyPhotos(data.photos || []);
    } catch (err) {
      console.log(err);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selected || !file) return;

    const formData = new FormData();
    formData.append("image", file);
    formData.append("caption", caption);

    try {
      setStatus("Uploading photo...");
      await photoApi.upload(selected.slug, formData);
      setStatus("Photo uploaded successfully! It will automatically become the cover photo if it becomes popular.");
      const { data } = await photoApi.get(selected.slug);
      setMyPhotos(data.photos || []);
      setFile(null);
      setCaption("");
    } catch (err) {
      setStatus(err.response?.status === 401 ? "Please login first." : "Upload failed.");
    }
  };

  const WeatherIcon = weatherIcons[weather?.condition?.toLowerCase()] || FiSun;

  if (loading) {
    return <Loader fullScreen={false} />;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {user?.name || "Traveler"} 👋</h1>
        <p className="text-gray-500 text-sm">Here's everything happening with your travel plans today.</p>
      </div>

      {/* Weather + Budget */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card-base p-5 flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-500 flex items-center gap-2">
              <FiMapPin />
              {weather?.location || "Current Location"}
            </p>
            <p className="text-3xl font-bold">{weather?.temperature_c ?? weather?.temperature ?? "--"}°</p>
            <p className="text-gray-400">{weather?.description || weather?.condition || "Loading..."}</p>
          </div>
          <WeatherIcon size={42} />
        </div>

        <BudgetCard label="Total Budget" amount={budget?.total} />
        <BudgetCard label="Spent" amount={budget?.spent} accent="secondary" />
      </div>

      {/* Latest Alerts */}
      <section>
        <h2 className="font-semibold text-lg mb-4">Latest Alerts</h2>
        {alerts.length ? (
          <div className="grid md:grid-cols-2 gap-4">
            {alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        ) : (
          <EmptyState title="No alerts" subtitle="No safety alerts available right now." />
        )}
      </section>

      {/* Recommendations */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-lg">Recommended For You</h2>
        </div>
        {recommendations.length ? (
          <div className="grid md:grid-cols-2 gap-4">
            {recommendations.map((item) => (
              <RecommendationCard key={item.id} item={item} />
            ))}
          </div>
        ) : (
          <EmptyState title="No recommendations" subtitle="Explore destinations to receive personalized recommendations." />
        )}
      </section>

      {/* Favorite Places */}
      <section>
        <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <FiHeart />
          Favorite Places
        </h2>
        {favorites.length ? (
          <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
            {favorites.map((destination) => (
              <DestinationCard key={destination.id} destination={destination} isFavorite />
            ))}
          </div>
        ) : (
          <EmptyState title="No favorite destinations" subtitle="Save destinations you love and they'll appear here." />
        )}
      </section>

      {/* Popular Destinations — now a SIBLING section, not nested inside
          the favorites conditional, so it renders regardless of whether
          the user has any favorites yet. */}
      <section>
        <h2 className="font-semibold text-lg mb-4">Popular Destinations</h2>
        {destinations.length ? (
          <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
            {destinations.map((destination) => (
              <DestinationCard key={destination.id} destination={destination} />
            ))}
          </div>
        ) : (
          <EmptyState title="No destinations yet" subtitle="Check back soon, or add some via the admin panel." />
        )}
      </section>

      {/* ===========================
          COMMUNITY PHOTO CONTRIBUTION
      ============================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FiImage />
            Community Contributions
          </h2>
          <p className="text-gray-500 mt-2">
            Help fellow travelers by uploading your own destination photos. Popular community photos are
            automatically promoted to official destination cover photos.
          </p>
        </div>

        {/* Search Destination */}
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3">
          <input
            className="border rounded-lg px-4 py-3 flex-1"
            placeholder="Search a destination..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            className="bg-blue-600 text-white rounded-lg px-6 py-3 flex items-center justify-center gap-2 hover:bg-blue-700 transition"
          >
            <FiSearch />
            Search
          </button>
        </form>

        {results.length > 0 && (
          <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-4">
            {results.map((place) => (
              <div
                key={place.id}
                onClick={() => selectDestination(place)}
                className="card-base p-4 cursor-pointer hover:shadow-lg transition"
              >
                {/* This <img> was missing entirely before — cover_image_url
                    comes straight from the destination list serializer. */}
                {place.cover_image_url && (
                  <img
                    src={place.cover_image_url}
                    alt={place.name}
                    className="w-full h-32 object-cover rounded-lg mb-3"
                  />
                )}
                <h3 className="font-semibold text-lg">{place.name}</h3>
                <p className="text-gray-500">{place.city}</p>
              </div>
            ))}
          </div>
        )}

        {/* Selected Destination */}
        {selected && (
          <div className="card-base p-6 space-y-6">
            <div>
              <h3 className="text-xl font-semibold">Upload a Photo for {selected.name}</h3>
              <p className="text-gray-500 mt-1">
                Share your travel experience with other travelers. High-quality and popular photos are
                automatically promoted as the destination cover photo.
              </p>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Select Photo</label>
                <input
                  type="file"
                  accept="image/*"
                  required
                  className="w-full border rounded-lg px-3 py-2"
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Caption (Optional)</label>
                <input
                  type="text"
                  placeholder="Write a short caption..."
                  className="w-full border rounded-lg px-3 py-2"
                  value={caption}
                  onChange={(e) => setCaption(e.target.value)}
                />
              </div>

              <button
                type="submit"
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition flex items-center gap-2"
              >
                <FiUpload />
                Upload Photo
              </button>
            </form>

            {status && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-700">{status}</p>
              </div>
            )}

            {/* Community Gallery */}
            {myPhotos.length > 0 && (
              <div>
                <h4 className="font-semibold text-lg mb-4">Community Gallery ({myPhotos.length})</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {myPhotos.map((photo) => (
                    <div key={photo.id} className="rounded-xl overflow-hidden shadow bg-white">
                      <img
                        src={photo.display_url}
                        alt={photo.caption || "Destination"}
                        className="w-full h-40 object-cover"
                      />
                      <div className="p-3">
                        {photo.caption && <p className="text-sm mb-2">{photo.caption}</p>}
                        <div className="flex justify-between items-center text-xs text-gray-500">
                          <span>👁 {photo.view_count} views</span>
                          {photo.is_cover && <span className="font-semibold text-yellow-600">⭐ Cover</span>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!myPhotos.length && (
              <EmptyState title="No photos yet" subtitle="Be the first traveler to upload a photo for this destination." />
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;