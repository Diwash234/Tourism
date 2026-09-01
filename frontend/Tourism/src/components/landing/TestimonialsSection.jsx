import { useEffect, useState } from "react"
import { FiStar, FiCheckCircle } from "react-icons/fi"
import { SlideUp, HoverCard } from "../common/MotionSystem"
import axiosClient from "../../api/axiosClient"
import { NOT_RECORDED, UPDATE_SOON } from "../../utils/placeUtils"

export default function TestimonialsSection() {
  const [reviews, setReviews] = useState([])

  useEffect(() => {
    axiosClient.get("/reviews/", { params: { page_size: 6, ordering: "-created_at" } })
      .then(({ data }) => {
        const rows = data.results || data || []
        setReviews((Array.isArray(rows) ? rows : []).filter((row) => row.comment).slice(0, 3))
      })
      .catch(() => setReviews([]))
  }, [])

  return (
    <section className="container-app py-20 bg-gradient-to-b from-transparent via-purple-50/40 to-transparent">
      <SlideUp>
        <div className="text-center max-w-2xl mx-auto mb-14">
          <span className="px-3.5 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-black uppercase tracking-wider">
            Recorded traveller reviews
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
            Approved comments from the database
          </h2>
          <p className="text-gray-500 text-sm mt-2">
            Invented testimonials were removed. Empty reviews stay {NOT_RECORDED}.
          </p>
        </div>
      </SlideUp>

      {reviews.length ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {reviews.map((t) => (
            <HoverCard key={t.id} className="card-base p-7 rounded-3xl border border-purple-100/80 shadow-xl bg-white flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-1 text-amber-500">
                  <FiStar size={16} className="fill-amber-400 text-amber-400" />
                </div>
                <p className="text-gray-700 text-xs sm:text-sm leading-relaxed italic">
                  "{t.comment}"
                </p>
              </div>
              <div className="flex items-center gap-3 pt-3 border-t border-gray-100">
                <div>
                  <h4 className="font-bold text-sm text-gray-900 flex items-center gap-1">
                    {t.user_name || "Traveller"} <FiCheckCircle className="text-emerald-500" size={13} />
                  </h4>
                  <p className="text-[11px] text-gray-400">Approved review</p>
                </div>
              </div>
            </HoverCard>
          ))}
        </div>
      ) : (
        <div className="max-w-xl mx-auto rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center text-sm text-amber-950">
          <p className="font-semibold">{NOT_RECORDED}</p>
          <p className="text-xs mt-1">{UPDATE_SOON}. Approved reviews will appear here once travellers post them.</p>
        </div>
      )}
    </section>
  )
}
