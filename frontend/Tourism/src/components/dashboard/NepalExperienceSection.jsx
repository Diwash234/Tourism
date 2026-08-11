import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import destinationApi from "../../api/destinationApi"
import NepalCultureCard from "../cards/NepalCultureCard"
import LocalExperienceCard from "../cards/LocalExperienceCard"

const CULTURE_KEYWORDS = ["culture", "heritage", "tradition", "temple", "museum"]
const EXPERIENCE_KEYWORDS = ["experience", "local", "community", "homestay", "village"]

function findCategory(categories, keywords) {
  return categories.find((c) =>
    keywords.some((kw) => (c.name || "").toLowerCase().includes(kw))
  )
}

/**
 * NepalExperienceSection
 * Deliberately built on top of the existing Category + Destination models
 * rather than a new backend model. If your Django admin doesn't have a
 * "Culture & Heritage" or "Local Experience" category yet, this renders
 * a setup hint instead of an empty/broken section — see the chat notes
 * for the exact steps to add them.
 */
const NepalExperienceSection = () => {
  const [cultureItems, setCultureItems] = useState([])
  const [experienceItems, setExperienceItems] = useState([])
  const [status, setStatus] = useState("loading") // loading | ready | no-categories

  useEffect(() => {
    destinationApi
      .getCategories()
      .then(async ({ data }) => {
        const categories = data.results || data || []
        const cultureCat = findCategory(categories, CULTURE_KEYWORDS)
        const experienceCat = findCategory(categories, EXPERIENCE_KEYWORDS)

        if (!cultureCat && !experienceCat) {
          setStatus("no-categories")
          return
        }

        const [cultureRes, experienceRes] = await Promise.all([
          cultureCat
            ? destinationApi.getAll({ category: cultureCat.id, limit: 4 })
            : Promise.resolve({ data: { results: [] } }),
          experienceCat
            ? destinationApi.getAll({ category: experienceCat.id, limit: 4 })
            : Promise.resolve({ data: { results: [] } }),
        ])

        setCultureItems(cultureRes.data.results || cultureRes.data || [])
        setExperienceItems(experienceRes.data.results || experienceRes.data || [])
        setStatus("ready")
      })
      .catch(() => setStatus("no-categories"))
  }, [])

  if (status === "loading") return null

  if (status === "no-categories") {
    return (
      <section className="card-base p-6 border border-dashed border-himalaya-200">
        <h2 className="font-semibold text-lg mb-2">Nepal Culture & Local Experiences</h2>
        <p className="text-sm text-gray-500">
          No "Culture & Heritage" or "Local Experience" category exists yet. Add them in Django admin
          under Categories, then tag a few destinations (Dhoka architecture spots, homestay villages,
          festivals) with those categories — this section will populate automatically, no code changes
          needed. See the backend notes in chat for the exact steps.
        </p>
      </section>
    )
  }

  return (
    <div className="space-y-10">
      {cultureItems.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">Nepal Culture & Heritage</h2>
            <Link to="/destinations" className="text-sm text-himalaya-500 hover:underline">
              View all
            </Link>
          </div>
          <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-5">
            {cultureItems.map((d) => (
              <NepalCultureCard key={d.id} destination={d} />
            ))}
          </div>
        </section>
      )}

      {experienceItems.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">Local Experiences</h2>
            <Link to="/destinations" className="text-sm text-forest-600 hover:underline">
              View all
            </Link>
          </div>
          <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-5">
            {experienceItems.map((d) => (
              <LocalExperienceCard key={d.id} destination={d} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

export default NepalExperienceSection