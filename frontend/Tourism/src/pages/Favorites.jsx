import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FiHeart } from "react-icons/fi";
import { favoriteApi } from "../services/api.js";
import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";
import DestinationCard from "../components/cards/DestinationCard";
import useToast from "../hooks/useToast";

const Favorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  const { showToast } = useToast();

  const load = () => {
    setLoading(true);

    favoriteApi
      .list()
      .then(({ data }) => {
        setFavorites(data.results || data || []);
      })
      .catch(() => {
        setFavorites([]);
        showToast("Log in to see your favourites.", "error");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleRemove = async (id) => {
    try {
      await favoriteApi.remove(id);

      setFavorites((prev) => prev.filter((fav) => fav.id !== id));

      showToast("Removed from favourites", "info");
    } catch {
      showToast("Could not remove favourite", "error");
    }
  };

  if (loading) return <Loader />;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="fade-in">
      <h1 className="section-title flex items-center gap-2">
        <FiHeart className="text-nepalred-500" />
        My Favourites
      </h1>

      {favorites.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {favorites.map((fav) => (
            <DestinationCard
              key={fav.id}
              destination={fav.destination_detail}
              isFavorite
              onToggleFavorite={() => handleRemove(fav.id)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No favourites yet"
          subtitle="Tap the heart on a destination to save it here."
        />
      )}
    </motion.div>
  );
};

export default Favorites;