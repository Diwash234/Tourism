import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FiMapPin,
  FiHeart,
  FiUpload,
  FiSearch,
  FiImage,
  FiTrendingUp,
  FiX,
} from "react-icons/fi";

import useAuth from "../hooks/useAuth";
import useGeolocation from "../hooks/useGeolocation";
import usePublicConfig from "../hooks/usePublicConfig";
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
import WeatherCard from "../components/cards/WeatherCard";
import SafetyOverview from "../components/cards/SafetyOverview";
import HotelCard from "../components/cards/HotelCard";
import NepalExperienceSection from "../components/dashboard/NepalExperienceSection";
import NepalHighlights from "../components/dashboard/NepalHighlights";
import NationalSymbols from "../components/dashboard/NationalSymbols";
import VisitorNoticeBanner from "../components/common/VisitorNoticeBanner";
import hotelService from "../services/hotelService";

// Small helper: every one of our paginated/ML endpoints returns
// { results: [...] } (or, for ML recommendations, { source, results: [...] }).
// Centralizing the unwrap here means we only have to get the shape right once.
function unwrapList(response) {
  return response?.data?.results || response?.data?.items || response?.data || [];
}

// Heuristic safety score from live alert count until a dedicated
// /risk/overview endpoint exists — HIGH-severity alerts cost more.
function scoreFromAlerts(alerts = []) {
  const penalty = alerts.reduce((sum, a) => {
    const level = (a.level || a.severity || "").toLowerCase();
    return sum + (level === "high" ? 15 : level === "moderate" ? 8 : 4);
  }, 0);
  return Math.max(40, 100 - penalty);
}

const Dashboard = () => {
  const { user } = useAuth();
  const { pages, section, notices = [] } = usePublicConfig();
  const dashboardPage = pages?.find((page) => page.key === "dashboard");
  const managed = Boolean(dashboardPage?.sections?.length);
  const block = (key) => section("dashboard", key);
  const showBlock = (key) => !managed || Boolean(block(key));
  const copy = (key, field, fallback) => block(key)?.[field] || fallback;
  const [phoneBannerDismissed, setPhoneBannerDismissed] = useState(false);
  const { position } = useGeolocation();
  const navigate = useNavigate();

  // Dashboard State
  const [weather, setWeather] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [budget, setBudget] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);

  // Hero / AI Search state
  const [heroQuery, setHeroQuery] = useState("");

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
        const [recRes, alertRes, budgetRes, favRes, destRes, hotelRes] = await Promise.all([
          recommendationApi.getPersonalized(),
          alertApi.getAlerts({ limit: 4 }),
          budgetApi.getSummary(),
          userApi.getFavorites(),
          destinationApi.list({ limit: 6, featured: true }),
          hotelService.recommended({ limit: 4 }),
        ]);

        setRecommendations(unwrapList(recRes));
        setAlerts(unwrapList(alertRes));
        setFavorites(unwrapList(favRes));
        setDestinations(unwrapList(destRes));
        setHotels(unwrapList(hotelRes));

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
      .catch(() => {
        const temp = position.lat > 28.2 ? 14 : 22
        setWeather({
          temperature_c: temp,
          condition: "Clear",
          description: "Pleasant mountain climate",
          humidity: 55,
        })
      });
  }, [position]);

  // Shared search: the hero bar and the community-photo search both hit
  // the same destinations endpoint, so one handler serves both inputs.
  const runSearch = async (term) => {
    if (!term.trim()) return;
    try {
      const { data } = await destinationApi.search(term);
      setResults(data.results || data || []);
    } catch (err) {
      console.log(err);
    }
  };

  const handleHeroSearch = (e) => {
    e.preventDefault();
    if (!heroQuery.trim()) return;
    // (small cards, no "Explore Now", meant for choosing a place to
    // upload a photo for) — not what someone typing a destination name
    // into the hero search expects. Now it goes to the real destination
    // search results, which have full DestinationCards with working
    // Explore Now buttons.
    navigate(`/destinations?q=${encodeURIComponent(heroQuery)}`);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    runSearch(query);
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

  if (loading) {
    return <Loader fullScreen={false} />;
  }

  return (
    <div className="space-y-10 fade-in">
      {/* NEW: National Symbols — placed first per the brief, so the
          dashboard "isn't empty" and leads with Nepal's identity before
          anything else */}
      {showBlock("national-symbols") && <NationalSymbols />}

      {/* NEW: phone verification prompt. Only shown if a phone number
          exists and hasn't been verified THIS session — see
          VerifyPhone.jsx for why sessionStorage is the best signal
          available (UserProfileSerializer doesn't expose
          phone_verified). Dismissible so it isn't naggy every visit. */}
      {user?.phone_number && sessionStorage.getItem("phone_verified_this_session") !== "true" && !phoneBannerDismissed && (
        <div className="flex items-center justify-between gap-4 bg-saffron-50 border border-saffron-100 rounded-xl px-4 py-3 text-sm">
          <span className="text-saffron-700">Verify your phone number to enable SMS risk alerts.</span>
          <div className="flex items-center gap-3 shrink-0">
            <Link to="/verify-phone" className="font-semibold text-himalaya-600 hover:underline">Verify now</Link>
            <button onClick={() => setPhoneBannerDismissed(true)} className="text-gray-400 hover:text-gray-600">
              <FiX size={16} />
            </button>
          </div>
        </div>
      )}

      {/* ===========================
          HERO SECTION
      ============================ */}
      {showBlock("hero") && <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-himalaya-500 via-himalaya-600 to-forest-600 text-white p-8 md:p-12">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_20%_20%,white,transparent_35%)]" />
        <div className="relative">
          <h1 className="text-2xl md:text-3xl font-bold">
            {copy("hero", "title", `Namaste, ${user?.name || "Traveler"} 👋`)}
          </h1>
          <p className="text-white/80 mt-2 max-w-xl">
            {copy("hero", "subtitle", copy("hero", "body", "Here's what's happening with your Nepal trip today — weather, safety, budget, and AI picks made just for you."))}
          </p>

          {/* AI SEARCH */}
          <form onSubmit={handleHeroSearch} className="mt-6 flex flex-col sm:flex-row gap-3 max-w-2xl">
            <input
              className="flex-1 rounded-xl px-4 py-3 text-dark bg-white/95 focus:outline-none focus:ring-2 focus:ring-saffron-400"
              placeholder="Search destinations, activities, or a city..."
              value={heroQuery}
              onChange={(e) => setHeroQuery(e.target.value)}
            />
            <button type="submit" className="btn-gradient flex items-center justify-center gap-2 whitespace-nowrap">
              <FiSearch />
              AI Search
            </button>
          </form>
        </div>
      </section>}

      {/* ===========================
          WEATHER + BUDGET SNAPSHOT
      ============================ */}
      {showBlock("weather-budget") && <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <WeatherCard
          location={weather?.location || "Current location"}
          temp_c={weather?.temperature_c ?? weather?.temperature}
          condition={weather?.description || weather?.condition || "clear"}
          humidity={weather?.humidity}
          wind_kmh={weather?.wind_kmh}
          loading={!weather}
        />
        <BudgetCard label="Total Budget" amount={budget?.total} />
        <BudgetCard label="Spent" amount={budget?.spent} accent="forest" />
      </div>}

      {notices.length > 0 && <VisitorNoticeBanner notices={notices} />}

      {/* Latest Alerts — kept next to the weather/budget snapshot since
          they're all "right now" info at a glance */}
      {showBlock("alerts") && alerts.length > 0 && (
        <section>
          <h2 className="font-semibold text-lg mb-4">{copy("alerts", "title", "Latest Alerts")}</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {alerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        </section>
      )}

      {/* ===========================
          RECOMMENDED PLACES (AI)
      ============================ */}
      {showBlock("recommendations") && <section>
        <div className="flex items-center gap-2 mb-4">
          <FiTrendingUp className="text-himalaya-500" />
          <h2 className="font-semibold text-lg">{copy("recommendations", "title", "Recommended For You")}</h2>
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
      </section>}

      {/* ===========================
          TRENDING NEPAL DESTINATIONS
      ============================ */}
      {showBlock("trending") && <section>
        <h2 className="font-semibold text-lg mb-4">{copy("trending", "title", "Trending Nepal Destinations")}</h2>
        {destinations.length ? (
          <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-6">
            {destinations.map((destination) => (
              <DestinationCard key={destination.id} destination={destination} />
            ))}
          </div>
        ) : (
          <EmptyState title="No destinations yet" subtitle="Check back soon, or add some via the admin panel." />
        )}
      </section>}

      {/* Favorite Places */}
      {showBlock("favorites") && <section>
        <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <FiHeart />
          {copy("favorites", "title", "Favorite Places")}
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
      </section>}

      {/* ===========================
          RECOMMENDED HOTELS (new)
      ============================ */}
      {showBlock("hotels") && hotels.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">{copy("hotels", "title", "Recommended Hotels & Stays")}</h2>
            <Link to="/hotels" className="text-sm text-himalaya-500 hover:underline">
              View all
            </Link>
          </div>
          <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-5">
            {hotels.map((hotel) => (
              <HotelCard key={hotel.id} hotel={hotel} />
            ))}
          </div>
        </section>
      )}

      {/* ===========================
          NEPAL CULTURE & LOCAL EXPERIENCES (new)
      ============================ */}
      {showBlock("culture") && <NepalExperienceSection />}

      {/* NEW: same "Why Visit Nepal" content shown on the public Landing
          page — included here too since a user who registered directly
          (without visiting Landing first) would otherwise never see it. */}
      {showBlock("highlights") && <NepalHighlights bare />}

      {/* ===========================
          SAFETY STATUS
      ============================ */}
      {showBlock("safety") && <section>
        <h2 className="font-semibold text-lg mb-4">{copy("safety", "title", "Safety Status")}</h2>
        <SafetyOverview
          score={scoreFromAlerts(alerts)}
          weatherStatus={weather?.condition || "Good"}
          earthquakeRisk={alerts.some((a) => /earthquake|seismic/i.test(a.title || a.type || "")) ? "Moderate" : "Low"}
          hospitalsNearby={budget?.byCategory?.length ? "See Risk page" : "—"}
          policeNearby="—"
        />
        <p className="text-xs text-gray-400 mt-2">
          {copy("safety", "body", "Full facility counts and live disaster data live on the Risk Analysis page.")}
        </p>
      </section>}

      {/* ===========================
          BUDGET SUMMARY
      ============================ */}
      {showBlock("budget-summary") && <section>
        <h2 className="font-semibold text-lg mb-4">{copy("budget-summary", "title", "Budget Summary")}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <BudgetCard label="Total Budget" amount={budget?.total} />
          <BudgetCard label="Spent So Far" amount={budget?.spent} accent="forest" />
          <div className="card-base p-5">
            <p className="text-sm text-gray-500">Entries Logged</p>
            <p className="text-xl font-bold text-dark mt-1">{budget?.entryCount ?? 0}</p>
          </div>
          <div className="card-base p-5">
            <p className="text-sm text-gray-500">Categories</p>
            <p className="text-xl font-bold text-dark mt-1">{budget?.byCategory?.length ?? 0}</p>
          </div>
        </div>
      </section>}

      {/* ===========================
          COMMUNITY PHOTO CONTRIBUTION
      ============================ */}
      {showBlock("community-photos") && <section id="community-search" className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FiImage />
            {copy("community-photos", "title", "Community Photos")}
          </h2>
          <p className="text-gray-500 mt-2">
            Help fellow travelers by uploading your own destination photos. Popular community photos are
            automatically promoted to official destination cover photos.
          </p>
        </div>

        {/* Search Destination */}
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3">
          <input
            className="input-field flex-1"
            placeholder="Find a destination to upload a photo for..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn-gradient flex items-center justify-center gap-2">
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
                className="card-base p-4 cursor-pointer"
              >
                {place.cover_image_url && (
                  <img
                    src={place.cover_image_url}
                    alt={place.name}
                    className="w-full h-32 object-cover rounded-lg mb-3"
                  />
                )}
                <h3 className="font-semibold text-lg">{place.name}</h3>
                <p className="text-gray-500 flex items-center gap-1">
                  <FiMapPin size={14} />
                  {place.city}
                </p>
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
                  className="input-field"
                  value={caption}
                  onChange={(e) => setCaption(e.target.value)}
                />
              </div>

              <button type="submit" className="btn-gradient flex items-center gap-2">
                <FiUpload />
                Upload Photo
              </button>
            </form>

            {status && (
              <div className="bg-himalaya-50 border border-himalaya-100 rounded-lg p-4">
                <p className="text-himalaya-600">{status}</p>
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
                          {photo.is_cover && <span className="font-semibold text-saffron-600">⭐ Cover</span>}
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
      </section>}
    </div>
  );
};

export default Dashboard;