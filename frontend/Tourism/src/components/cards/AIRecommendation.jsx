import { Link } from "react-router-dom"
import { FiCpu, FiArrowRight } from "react-icons/fi"

/**
 * AIRecommendationCard
 * Explains *why* a set of destinations is being suggested, driven by the
 * ML similarity-match recommendation endpoint (mlService.getSimilarPlaces).
 *
 * props:
 *  - basedOn: { name, slug } -- the place the user showed interest in
 *  - suggestions: [{ name, slug, similarity }] -- 0-100 similarity score
 */
const AIRecommendationCard = ({ basedOn, suggestions = [] }) => {
  if (!basedOn || suggestions.length === 0) return null

  return (
    <div className="card-base p-5 border border-himalaya-100">
      <div className="flex items-center gap-2 text-himalaya-500 font-semibold text-sm mb-3">
        <FiCpu size={16} />
        AI Suggestion
      </div>

      <p className="text-sm text-gray-500 mb-3">
        Because you liked{" "}
        <span className="font-semibold text-dark">{basedOn.name}</span>, you may like:
      </p>

      <ul className="space-y-2">
        {suggestions.map((s) => (
          <li key={s.slug || s.name}>
            <Link
              to={s.slug ? `/destinations/${s.slug}` : "#"}
              className="flex items-center justify-between gap-3 rounded-xl px-3 py-2 hover:bg-forest-50 transition-colors group"
            >
              <span className="text-sm font-medium text-dark">{s.name}</span>
              <span className="flex items-center gap-2 text-xs">
                <span className="text-forest-600 font-semibold">
                  {Math.round(s.similarity ?? 0)}% match
                </span>
                <FiArrowRight className="text-gray-300 group-hover:text-forest-500 transition-colors" size={14} />
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default AIRecommendationCard