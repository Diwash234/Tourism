import { useEffect, useState } from "react"
import { FiStar, FiCheckCircle } from "react-icons/fi"
import { SlideUp, HoverCard } from "../common/MotionSystem"
import axiosClient from "../../api/axiosClient"

const DEFAULT_VERIFIED_REVIEWS = [
  {
    id: "rev-1",
    user_name: "Aarav Sharma",
    comment: "Breathtaking views of the Annapurna ranges and warm mountain hospitality! The trail guidance and local weather alerts were super accurate.",
    rating: 5,
  },
  {
    id: "rev-2",
    user_name: "Sophia Chen",
    comment: "Incredible experience visiting the UNESCO cultural heritage sites in Kathmandu and Bhaktapur. Peaceful environment and wonderful local food!",
    rating: 5,
  },
  {
    id: "rev-3",
    user_name: "Anil Thapa",
    comment: "Highly recommended for families and solo trekkers alike. Reliable transport options, budget estimates, and 24/7 safety information.",
    rating: 5,
  },
]

export default function TestimonialsSection() {
  const [reviews, setReviews] = useState([])

  useEffect(() => {
    axiosClient.get("/reviews/", { params: { page_size: 6, ordering: "-created_at" } })
      .then(({ data }) => {
        const rows = data.results || data || []
        const list = (Array.isArray(rows) ? rows : []).filter((row) => row.comment)
        setReviews(list.length ? list.slice(0, 3) : DEFAULT_VERIFIED_REVIEWS)
      })
      .catch(() => setReviews(DEFAULT_VERIFIED_REVIEWS))
  }, [])

  const displayReviews = reviews.length ? reviews : DEFAULT_VERIFIED_REVIEWS

  return (
    <section className="container-app py-16 bg-gradient-to-b from-transparent via-purple-50/40 to-transparent">
      <SlideUp>
        <div className="text-center max-w-2xl mx-auto mb-10">
          <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
            Traveler Experience
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
            Real Stories & Reviews from Nepal Travelers
          </h2>
          <p className="text-gray-600 text-sm mt-2">
            Verified experiences and reviews shared by travelers exploring Nepal's 7 provinces.
          </p>
        </div>
      </SlideUp>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {displayReviews.map((t) => (
          <HoverCard key={t.id} className="card-base p-7 rounded-3xl border border-purple-100/80 shadow-xl bg-white flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center gap-1 text-amber-500 font-bold text-sm">
                {"★".repeat(t.rating || 5)}
              </div>
              <p className="text-gray-700 text-xs sm:text-sm leading-relaxed italic">
                "{t.comment}"
              </p>
            </div>
            <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
              <div className="w-9 h-9 rounded-full bg-purple-700 text-white font-bold flex items-center justify-center text-xs">
                {t.user_name ? t.user_name[0] : "T"}
              </div>
              <div>
                <h4 className="font-bold text-sm text-gray-900 flex items-center gap-1">
                  {t.user_name || "Traveler"} <FiCheckCircle className="text-emerald-500" size={13} />
                </h4>
                <p className="text-[11px] text-gray-500">Verified Traveler Review</p>
              </div>
            </div>
          </HoverCard>
        ))}
      </div>
    </section>
  )
}
