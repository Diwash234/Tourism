import { Link } from "react-router-dom"
import { FiArrowRight, FiCompass, FiShield } from "react-icons/fi"

/**
 * Trip CTA is intentionally inline. The previous fixed bar could cover the
 * footer, emergency controls and the mobile navigation; placing it before
 * the footer gives every page a deliberate end point without collisions.
 */
const StickyCTA = ({ section = null }) => (
  <section className="container-app py-12 sm:py-16" aria-labelledby="trip-cta-title">
    <div className="overflow-hidden rounded-[var(--ny-radius-xl)] bg-[var(--ny-green-dark)] px-6 py-8 text-white shadow-[var(--ny-shadow-elevated)] sm:px-10 sm:py-10">
      <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold text-[#BDEBD9]">Ready when you are</p>
          <h2 id="trip-cta-title" className="mt-2 !text-2xl !text-white sm:!text-3xl">{section?.cta_text || "Planning a trip to Nepal?"}</h2>
          <p className="mt-2 text-sm leading-6 text-[#C7D9D2]">Start with a place, then shape the route, budget and support around the way you actually travel.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to={section?.cta_url || "/destinations"} className="ny-btn ny-btn-accent"><FiCompass size={16} aria-hidden="true" /> Explore destinations <FiArrowRight size={15} aria-hidden="true" /></Link>
          <Link to="/itinerary" className="ny-btn border border-white/30 bg-transparent text-white hover:border-white hover:bg-white/10"><FiShield size={16} aria-hidden="true" /> Build my trip</Link>
        </div>
      </div>
    </div>
  </section>
)

export default StickyCTA
