import { useEffect, useState } from "react"
import { FiArrowRight, FiMapPin } from "react-icons/fi"
import { Link } from "react-router-dom"
import { SlideUp } from "../common/MotionSystem"
import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"
import { getDestinationImageUrl } from "../../utils/imageUtils"
import PlaceholderImage from "../common/PlaceholderImage"

const offerCard = (offer) => ({
  key: `offer-${offer.id}`,
  title: offer.title,
  subtitle: offer.partner_name || offer.city || "Published package",
  desc: offer.summary || offer.description || "Package details are available on the offer page.",
  days: offer.duration_days,
  cost: offer.price_npr != null ? `NPR ${Number(offer.price_npr).toLocaleString()}` : "Information unavailable",
  image: offer.image_url,
  to: `/packages/${offer.slug}`,
  cta: "View published package",
})

const destinationCard = (destination) => ({
  key: `destination-${destination.id || destination.slug}`,
  title: destination.name,
  subtitle: destination.display_city || destination.district || "Recorded destination",
  desc: destination.short_description || destination.description || "Destination details are available on the record.",
  days: destination.recommended_days,
  cost: destination.entry_fee != null ? `NPR ${Number(destination.entry_fee).toLocaleString()}` : "Information unavailable",
  image: getDestinationImageUrl(destination),
  to: destination.slug ? `/destinations/${destination.slug}` : "/destinations",
  cta: "View recorded destination",
})

export default function CaseStudiesSection({ section = null, offers = [], destinations = [] }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    if (offers.length) {
      const timer = setTimeout(() => setItems(offers.slice(0, 3).map(offerCard)), 0)
      return () => clearTimeout(timer)
    }
    if (destinations.length) {
      const timer = setTimeout(() => setItems(destinations.slice(0, 3).map(destinationCard)), 0)
      return () => clearTimeout(timer)
    }

    let active = true
    userApi.getMarketplaceListings({ featured: true })
      .then(({ data }) => {
        const packages = data.results || []
        if (active && packages.length) setItems(packages.slice(0, 3).map(offerCard))
        else if (active) return destinationApi.getDestinations({ featured: true, page_size: 3, limit: 3 }).then(({ data: destData }) => {
          if (active) setItems((destData.results || destData || []).slice(0, 3).map(destinationCard))
        })
      })
      .catch(() => {
        if (active) setItems([])
      })
    return () => { active = false }
  }, [offers, destinations])

  if (!items.length) return null

  return (
    <section className="container-app section-space">
      <SlideUp>
        <div className="section-head mx-auto max-w-3xl text-center sm:mx-0 sm:text-left">
          <p className="ny-kicker">Recorded journeys</p>
          <h2 className="mt-2">{section?.title || "Live packages and destinations"}</h2>
          <p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">{section?.subtitle || "These cards come from published marketplace offers or featured destinations. Costs and days are shown only when recorded."}</p>
        </div>
      </SlideUp>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <article key={item.key} className="ny-card flex h-full flex-col overflow-hidden">
            <div className="relative aspect-[16/9] overflow-hidden bg-[var(--ny-soft-green)]">
              <PlaceholderImage src={item.image} title={item.title} alt={item.title} className="h-full w-full transition-transform duration-500 hover:scale-[1.03]" />
              {item.subtitle && <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-[var(--ny-green)]"><FiMapPin size={12} aria-hidden="true" />{item.subtitle}</span>}
            </div>
            <div className="flex flex-1 flex-col p-5">
              <h3 className="text-lg font-bold">{item.title}</h3>
              <p className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--ny-text-secondary)]">{item.desc}</p>
              <div className="mt-4 grid grid-cols-2 gap-2 border-t border-[var(--ny-border)] pt-4 text-xs">
                <div><span className="block text-[var(--ny-text-muted)]">Duration</span><strong>{item.days ? `${item.days} days` : "Information unavailable"}</strong></div>
                <div><span className="block text-[var(--ny-text-muted)]">Recorded cost</span><strong className="text-[var(--ny-green)]">{item.cost}</strong></div>
              </div>
              <Link to={item.to} className="ny-btn ny-btn-secondary mt-auto w-full justify-center">{item.cta} <FiArrowRight size={14} aria-hidden="true" /></Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
