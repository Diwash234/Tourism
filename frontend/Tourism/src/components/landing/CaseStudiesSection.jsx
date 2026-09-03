import { useEffect, useState } from "react"
import { FiMapPin, FiArrowRight } from "react-icons/fi"
import { Link } from "react-router-dom"
import { SlideUp, HoverCard } from "../common/MotionSystem"
import destinationApi from "../../api/destinationApi"
import userApi from "../../api/userApi"
import { getDestinationImageUrl } from "../../utils/imageUtils"
import PlaceholderImage from "../common/PlaceholderImage"

export default function CaseStudiesSection() {
  const [items, setItems] = useState([])

  useEffect(() => {
    userApi.getMarketplaceListings({ featured: true })
      .then(({ data }) => {
        const packages = data.results || []
        if (packages.length) {
          setItems(packages.slice(0, 3).map((offer) => ({
            key: offer.id,
            title: offer.title,
            subtitle: offer.partner_name || offer.city || "Published package",
            desc: offer.summary || "",
            days: offer.duration_days,
            cost: offer.price_npr != null ? `NPR ${Number(offer.price_npr).toLocaleString()}` : "Not recorded",
            image: offer.image_url,
            to: `/packages/${offer.slug}`,
            cta: "View published package",
          })))
          return
        }
        return destinationApi.getDestinations({ featured: true, page_size: 3, limit: 3 })
          .then(({ data: destData }) => {
            const dests = destData.results || destData || []
            setItems((Array.isArray(dests) ? dests : []).slice(0, 3).map((dest) => ({
              key: dest.id,
              title: dest.name,
              subtitle: dest.display_city || dest.district || "Not recorded",
              desc: dest.short_description || "",
              days: dest.recommended_days,
              cost: dest.entry_fee ? `NPR ${dest.entry_fee}` : "Not recorded",
              image: getDestinationImageUrl(dest),
              to: dest.slug ? `/destinations/${dest.slug}` : "/destinations",
              cta: "View recorded destination",
            })))
          })
      })
      .catch(() => setItems([]))
  }, [])

  if (!items.length) return null

  return (
    <section className="container-app py-20 relative z-10">
      <SlideUp>
        <div className="text-center max-w-3xl mx-auto mb-14">
          <span className="px-3.5 py-1 rounded-full bg-emerald-100 text-[#1D5146] text-xs font-black uppercase tracking-wider">
            Recorded journeys
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-2 tracking-tight">
            Live packages and destinations
          </h2>
          <p className="text-gray-500 text-sm mt-2">
            These cards come from published marketplace offers or featured destinations. Costs and days are shown only when recorded.
          </p>
        </div>
      </SlideUp>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {items.map((exp) => (
          <HoverCard key={exp.key} className="card-base overflow-hidden rounded-3xl border border-[#E5E0D5]/80 shadow-xl flex flex-col justify-between bg-white">
            <div>
              <div className="h-52 w-full relative overflow-hidden bg-slate-900">
                <PlaceholderImage src={exp.image} title={exp.title} alt={exp.title} className="w-full h-full object-cover" />
                <span className="absolute top-3 left-3 px-3 py-1 rounded-full bg-black/65 backdrop-blur text-amber-300 text-xs font-bold flex items-center gap-1">
                  <FiMapPin size={12} /> {exp.subtitle}
                </span>
              </div>
              <div className="p-6 space-y-3">
                <h3 className="font-bold text-lg text-gray-900 leading-snug">{exp.title}</h3>
                <p className="text-xs text-gray-600 leading-relaxed">{exp.desc || "No recorded summary."}</p>
                <div className="p-3.5 rounded-2xl bg-[#F7F8F5]/70 border border-[#E5E0D5] grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-400 text-[10px] uppercase font-bold">Duration</span>
                    <p className="font-extrabold text-gray-800">{exp.days ? `${exp.days} days` : "Not recorded"}</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-[10px] uppercase font-bold">Recorded cost</span>
                    <p className="font-extrabold text-emerald-700">{exp.cost}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="p-6 pt-0">
              <Link
                to={exp.to}
                className="w-full py-3 rounded-xl bg-[#F7F8F5] hover:bg-emerald-100 text-[#102A2E] text-xs font-bold flex items-center justify-center gap-1.5 transition-colors border border-[#E5E0D5]"
              >
                {exp.cta} <FiArrowRight size={13} />
              </Link>
            </div>
          </HoverCard>
        ))}
      </div>
    </section>
  )
}
