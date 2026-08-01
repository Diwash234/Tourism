import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FiSearch, FiStar } from "react-icons/fi";
import hotelApi from "../api/hotelApi";
import EmptyState from "../components/common/EmptyState";
import PlaceholderImage from "../components/common/PlaceholderImage";

const HotelSearch = () => {
  const [query, setQuery] = useState("");
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await hotelApi.search(query);
      // depends on whether the backend paginates this endpoint
      setHotels(data.results || data || []);
    } catch (error) {
      console.log("Hotel search error:", error.response?.data || error.message);
      setHotels([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-app py-10 fade-in">
      <h1 className="section-title">Find a Hotel</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-8 max-w-2xl">
        <div className="relative flex-1">
          <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input-field pl-11"
            placeholder="Search Pokhara, Lakeside, or a hotel name..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {hotels.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {hotels.map((hotel, i) => (
            <motion.div
              key={hotel.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="card-base overflow-hidden"
            >
              {hotel.image_url ? (
                <img src={hotel.image_url} alt={hotel.name} className="h-40 w-full object-cover" />
              ) : (
                <PlaceholderImage seed={hotel.id} className="h-40 w-full" />
              )}
              <div className="p-4">
                <h3 className="font-bold text-dark">{hotel.name}</h3>
                <p className="text-sm text-gray-500">{hotel.destination_name}</p>
                <p className="text-sm mt-1 flex items-center gap-1">
                  <FiStar className="fill-saffron-500 text-saffron-500" size={14} />
                  {hotel.rating} · <span className="font-semibold text-forest-600">${hotel.price_per_night}/night</span>
                </p>
                <button
                  className="btn-primary w-full mt-3"
                  onClick={() => navigate(`/hotels/${hotel.id}/book`)}
                >
                  Book Now
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      ) : searched && !loading ? (
        <EmptyState title="No hotels found" subtitle="Try a different city, area, or hotel name." />
      ) : null}
    </div>
  );
};

export default HotelSearch;