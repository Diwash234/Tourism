import { useEffect, useState } from "react"
import { FiStar } from "react-icons/fi"
import axiosClient from "../../api/axiosClient"
import EmptyState from "../common/EmptyState"

export default function TestimonialsSection({ section = null }) {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    let active = true
    axiosClient.get("/reviews/", { params: { page_size: 6, ordering: "-created_at" } })
      .then(({ data }) => { if (active) setReviews((data.results || data || []).filter((row) => row.comment).slice(0, 3)) })
      .catch(() => { if (active) setReviews([]) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return (
    <section className="container-app section-space" aria-labelledby="traveler-stories-title">
      <div className="max-w-2xl"><p className="ny-kicker">Traveler notes</p><h2 id="traveler-stories-title" className="mt-2">{section?.title || "Stories from the route"}</h2><p className="mt-2 text-sm text-[var(--ny-text-secondary)]">{section?.subtitle || "Published reviews appear here when travellers choose to share them."}</p></div>
      {loading ? <div className="mt-6 grid gap-5 md:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="ny-skeleton h-44" aria-hidden="true" />)}</div> : reviews.length ? <div className="mt-6 grid gap-5 md:grid-cols-3">{reviews.map((review) => <article key={review.id} className="ny-card flex h-full flex-col justify-between p-5"><div><div className="flex gap-1 text-[var(--ny-gold)]" aria-label={`${review.rating || "No"} out of 5 stars`}>{[1, 2, 3, 4, 5].map((star) => <FiStar key={star} size={15} className={star <= Number(review.rating || 0) ? "fill-current" : "opacity-30"} aria-hidden="true" />)}</div><p className="mt-4 text-sm leading-6 text-[var(--ny-text-secondary)]">“{review.comment}”</p></div><p className="mt-5 border-t border-[var(--ny-border)] pt-4 text-sm font-semibold">{review.user_name || "Traveller"}</p></article>)}</div> : <div className="mt-6"><EmptyState title="No published traveller stories yet" subtitle="Reviews will appear here after they are submitted and made available by the platform." /></div>}
    </section>
  )
}
