import { Link } from "react-router-dom"
import { FiArrowRight, FiStar } from "react-icons/fi"
import PlaceholderImage from "../common/PlaceholderImage"

const normalize = (item = {}) => ({
  id: item.id || item.destination_id || item.destination_slug || item.slug,
  title: item.title || item.destination_name || item.name,
  slug: item.destination_slug || item.slug,
  location: item.destination_city || item.display_city || item.city || item.district,
  description: item.short_description || item.description || item.summary,
  image: item.image_url || item.effective_image_url || item.cover_image_url,
  rating: item.destination_rating ?? item.average_rating ?? null,
  ctaLabel: item.cta_label,
})

export default function FeaturedEditorialGrid({ destinations = [], featuredCards = [], section = null }) {
  const list = (featuredCards.length ? featuredCards : destinations)
    .map(normalize)
    .filter((item) => item.title)
    .slice(0, 3)

  // Do not manufacture destinations or ratings when the live catalogue is
  // empty. Landing simply moves on to the next honest section.
  if (!list.length) return null

  const [main, ...supporting] = list
  const side = supporting.length ? supporting : []

  const cardLink = (item, className, children, large = false) => {
    const content = (
      <>
        <PlaceholderImage src={item.image} title={item.title} alt={item.title} className="absolute inset-0 h-full w-full transition-transform duration-500 group-hover:scale-[1.03]" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#042A24] via-[#042A24]/45 to-transparent" aria-hidden="true" />
        <div className="relative z-10 flex h-full flex-col justify-end p-5 sm:p-6">
          <div className="flex flex-wrap items-center gap-2">
            {item.location && <span className="rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-[var(--ny-green)]">{item.location}</span>}
            {item.rating != null && <span className="inline-flex items-center gap-1 rounded-full bg-black/45 px-2.5 py-1 text-xs font-semibold text-white"><FiStar size={12} className="fill-[var(--ny-gold)] text-[var(--ny-gold)]" aria-hidden="true" /> {item.rating}</span>}
          </div>
          <h3 className={`mt-3 font-bold text-white ${large ? "text-2xl sm:text-3xl" : "text-xl"}`}>{item.title}</h3>
          {item.description && <p className="mt-2 line-clamp-2 text-sm leading-6 text-[#EAF2EF]">{item.description}</p>}
          <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-[#BDEBD9]">Open destination <FiArrowRight size={15} aria-hidden="true" /></span>
        </div>
      </>
    )

    if (!item.slug) return <article className={`group relative overflow-hidden rounded-[var(--ny-radius-lg)] bg-[var(--ny-green-dark)] ${className}`}>{content}</article>
    return <Link to={`/destinations/${item.slug}`} className={`group relative block overflow-hidden rounded-[var(--ny-radius-lg)] bg-[var(--ny-green-dark)] focus-visible:outline-4 focus-visible:outline-[var(--ny-gold)] ${className}`} aria-label={`Explore ${item.title}`}>{content}</Link>
  }

  return (
    <section className="container-app section-space" aria-labelledby="featured-destinations-heading">
      <div className="section-head flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="ny-kicker">From the catalogue</p>
          <h2 id="featured-destinations-heading" className="mt-2">{section?.title || "Featured destinations"}</h2>
          {section?.subtitle && <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--ny-text-secondary)]">{section.subtitle}</p>}
        </div>
        <Link to="/destinations" className="ny-btn ny-btn-secondary shrink-0">View all destinations <FiArrowRight size={15} aria-hidden="true" /></Link>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {cardLink(main, "min-h-[360px] sm:min-h-[460px] lg:row-span-2", null, true)}
        {side.map((item) => <div key={item.id || item.slug || item.title}>{cardLink(item, "min-h-[280px] sm:min-h-[320px]")}</div>)}
      </div>
    </section>
  )
}
