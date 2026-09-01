import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import {
  FiAward,
  FiCoffee,
  FiFeather,
  FiHome,
  FiImage,
  FiMap,
  FiSun,
  FiTriangle,
} from "react-icons/fi"

import NationalSymbols from "../components/dashboard/NationalSymbols"
import destinationApi from "../api/destinationApi"
import { NOT_RECORDED, UPDATE_SOON, recordedCity, recordedText } from "../utils/placeUtils"

const Section = ({ id, icon: Icon, title, children }) => (
  <motion.section
    id={id}
    initial={{ opacity: 0, y: 12 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-60px" }}
    className="scroll-mt-24 py-10 border-b border-gray-100 last:border-0"
  >
    <h2 className="section-title flex items-center gap-2">
      <Icon className="text-himalaya-500" />
      {title}
    </h2>
    {children}
  </motion.section>
)

const PendingBlock = ({ label = NOT_RECORDED }) => (
  <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
    <p className="font-semibold">{label}</p>
    <p className="text-xs mt-1">{UPDATE_SOON}. An administrator can add this from the visitor desk or destination editor.</p>
  </div>
)

const DestChip = ({ dest }) => (
  <Link
    to={dest.slug ? `/destinations/${dest.slug}` : "/destinations"}
    className="text-xs font-medium bg-gray-50 text-gray-700 px-3 py-1.5 rounded-full border border-gray-100 hover:border-emerald-300 hover:bg-emerald-50"
  >
    {dest.name}
    {dest.altitude ? ` · ${dest.altitude}` : ""}
  </Link>
)

const DestCard = ({ dest, icon: Icon }) => (
  <Link to={dest.slug ? `/destinations/${dest.slug}` : "/destinations"} className="card-base p-4 hover:shadow-md transition">
    {dest.cover_image_url ? (
      <img src={dest.cover_image_url} alt={dest.name} className="w-full h-28 rounded-lg mb-3 object-cover bg-gray-100" />
    ) : (
      <div className="w-full h-28 rounded-lg mb-3 bg-himalaya-50 flex items-center justify-center text-himalaya-300">
        {Icon ? <Icon size={26} /> : <FiImage size={26} />}
      </div>
    )}
    <h3 className="font-semibold text-sm mb-1">{dest.name}</h3>
    <p className="text-xs text-gray-500">{recordedCity(dest) || dest.district || NOT_RECORDED}</p>
    <p className="text-xs text-gray-500 mt-1 line-clamp-3">{recordedText(dest.short_description || dest.description)}</p>
  </Link>
)

export default function DiscoverNepal() {
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    destinationApi.discoverNepal()
      .then(({ data }) => setPayload(data))
      .catch(() => setPayload(null))
      .finally(() => setLoading(false))
  }, [])

  const wildlife = payload?.wildlife?.items || []
  const heritage = payload?.heritage?.items || []
  const mountains = payload?.mountains?.items || []
  const culture = payload?.culture?.items || []
  const cuisine = payload?.cuisine?.items || []
  const festivals = payload?.festivals?.items || []
  const provinces = payload?.provinces || []

  return (
    <div className="container-app py-10 fade-in">
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-heading font-bold text-himalaya-500">
          Discover Nepal
        </h1>
        <p className="text-gray-500 mt-2 max-w-2xl">
          Recorded destinations, published festival notices, and official province names.
          Empty sections stay “{NOT_RECORDED}” until an administrator adds them.
        </p>
        {payload?.catalog?.destination_count != null && (
          <p className="text-xs text-emerald-800 mt-2 font-semibold">
            {payload.catalog.destination_count.toLocaleString()} recorded destinations in the catalogue
          </p>
        )}
      </div>

      <NationalSymbols />

      {loading && <p className="text-sm text-gray-500 mt-6">Loading recorded places…</p>}

      <Section id="festivals" icon={FiSun} title="Festivals">
        {festivals.length ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
            {festivals.map((festival) => (
              <div key={festival.id} className="card-base p-4">
                <div className="flex justify-between mb-1">
                  <h3 className="font-semibold text-sm">{festival.title}</h3>
                  <span className="text-[10px] bg-saffron-50 text-saffron-600 px-2 py-1 rounded-full">
                    {festival.kind || "festival"}
                  </span>
                </div>
                <p className="text-xs text-gray-500">{recordedText(festival.body)}</p>
                <p className="text-[11px] text-gray-400 mt-2">
                  {festival.city || festival.district || festival.destination_name || NOT_RECORDED}
                </p>
              </div>
            ))}
          </div>
        ) : (
          !loading && <PendingBlock />
        )}
      </Section>

      <Section id="wildlife" icon={FiAward} title="Wildlife & parks">
        {wildlife.length ? (
          <div className="grid sm:grid-cols-2 gap-4 mt-2">
            {wildlife.map((dest) => <DestCard key={dest.id} dest={dest} icon={FiAward} />)}
          </div>
        ) : (
          !loading && <PendingBlock />
        )}
      </Section>

      <Section id="unesco" icon={FiHome} title="Heritage sites">
        {heritage.length ? (
          <div className="flex flex-wrap gap-2 mt-2">
            {heritage.map((dest) => <DestChip key={dest.id} dest={dest} />)}
          </div>
        ) : (
          !loading && <PendingBlock />
        )}
      </Section>

      <Section id="culture" icon={FiFeather} title="Culture">
        {culture.length ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
            {culture.map((dest) => <DestCard key={dest.id} dest={dest} icon={FiFeather} />)}
          </div>
        ) : (
          !loading && <PendingBlock />
        )}
      </Section>

      <Section id="local-food" icon={FiCoffee} title="Local food">
        {cuisine.length ? (
          <div className="grid sm:grid-cols-2 gap-4 mt-2">
            {cuisine.map((dest) => <DestCard key={dest.id} dest={dest} icon={FiCoffee} />)}
          </div>
        ) : (
          !loading && <PendingBlock />
        )}
      </Section>

      <Section id="mountains" icon={FiTriangle} title="Mountains">
        {mountains.length ? (
          <div className="flex flex-wrap gap-2 mt-2">
            {mountains.map((dest) => <DestChip key={dest.id} dest={dest} />)}
          </div>
        ) : (
          !loading && <PendingBlock />
        )}
      </Section>

      <Section id="provinces" icon={FiMap} title="Province information">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
          {provinces.map((province) => (
            <Link
              key={province.name}
              to={`/destinations?q=${encodeURIComponent(province.name)}`}
              className="card-base p-4 hover:shadow-md transition"
            >
              <h3 className="font-semibold text-sm">{province.name}</h3>
              <p className="text-xs text-gray-400">
                {province.destination_count != null
                  ? `${province.destination_count.toLocaleString()} recorded places`
                  : NOT_RECORDED}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {province.sample_name || NOT_RECORDED}
              </p>
            </Link>
          ))}
        </div>
        {!provinces.length && !loading && <PendingBlock />}
      </Section>
    </div>
  )
}
