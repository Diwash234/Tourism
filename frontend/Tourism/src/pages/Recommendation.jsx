import { useEffect, useState } from "react"
import recommendationApi from "../api/recommendationApi"
import RecommendationCard from "../components/cards/RecommendationCard"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import Filter from "../components/common/Filter"

const CATEGORY_OPTIONS = [
  { label: "Adventure", value: "adventure" },
  { label: "Cultural", value: "cultural" },
  { label: "Nature", value: "nature" },
  { label: "Relaxation", value: "relaxation" },
]

const Recommendation = () => {
  const [items, setItems] = useState([])
  const [category, setCategory] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    recommendationApi
      .getRecommendations({ category })
      .then(({ data }) => setItems(data.items || data || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [category])

  return (
    <div className="container-app py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="section-title mb-1">Recommended For You</h1>
          <p className="text-gray-500 text-sm">Personalized picks based on your interests and travel history.</p>
        </div>
        <Filter label="Category" options={CATEGORY_OPTIONS} value={category} onChange={setCategory} />
      </div>

      {loading ? (
        <Loader />
      ) : items.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {items.map((item) => <RecommendationCard key={item.id} item={item} />)}
        </div>
      ) : (
        <EmptyState title="No recommendations found" subtitle="Try a different category or explore all destinations." />
      )}
    </div>
  )
}

export default Recommendation