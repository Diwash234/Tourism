import { Link } from "react-router-dom"

/**
 * Auto-scrolling marquee of Nepal's 7 provinces, each showing a
 * destination-specific image and the things it is famous for.
 *
 * Accessible: pauses on hover/focus, respects prefers-reduced-motion,
 * constrained to its section (no page-wide horizontal overflow).
 */
const PROVINCES = [
  {
    name: "Koshi",
    famous: "Ilam tea gardens, Kanchenjunga, Pathibhara",
    food: "Kinema, gundruk",
    festival: "Udhauli Ubhauli, Sakela",
    img: "/images/destinations/kanchenjunga/peak.jpg",
    q: "Ilam Nepal",
  },
  {
    name: "Madhesh",
    famous: "Janaki Mandir, Chitwan edge, Mithila art",
    food: "litti chokha, fish curry",
    festival: "Chhath, Vivah Panchami",
    img: "/images/destinations/janakpur/janaki-mandir.jpg",
    q: "Janakpur Nepal",
  },
  {
    name: "Bagmati",
    famous: "Kathmandu Durbar Square, Pashupatinath, Boudha",
    food: "momo, Newari khaja",
    festival: "Indra Jatra, Bisket",
    img: "/images/destinations/kathmandu/durbar-square.jpg",
    q: "Kathmandu Nepal",
  },
  {
    name: "Gandaki",
    famous: "Pokhara, Phewa Lake, Annapurna, Muktinath",
    food: "thakali thali, sel roti",
    festival: "Tamu Lhosar, Bagh Jatra",
    img: "/images/destinations/pokhara/fewatal.jpg",
    q: "Pokhara Nepal",
  },
  {
    name: "Lumbini",
    famous: "Birthplace of Buddha, Ashoka Pillar",
    food: "chukauni, dhikri",
    festival: "Buddha Jayanti",
    img: "/images/destinations/lumbini/garden.jpg",
    q: "Lumbini Nepal",
  },
  {
    name: "Karnali",
    famous: "Rara Lake, Phoksundo, Jumla wilderness",
    food: "chaklagau, marsi rice",
    festival: "Jatpokhara, Sinhasan",
    img: "/images/destinations/rara/alpine-lake.jpg",
    q: "Rara Lake Nepal",
  },
  {
    name: "Sudurpashchim",
    famous: "Khaptad plateau, Shuklaphanta, Saipal",
    food: "kachila, chyakhna",
    festival: "Gaura Parva",
    img: "/images/destinations/khaptad/landscape.jpg",
    q: "Khaptad Nepal",
  },
]

function ProvinceCard({ p }) {
  return (
    <Link
      to={`/destinations?q=${encodeURIComponent(p.q)}`}
      className="group shrink-0 w-72 sm:w-80 rounded-2xl overflow-hidden border border-gray-100 bg-white shadow-sm hover:shadow-xl transition-all"
    >
      <div className="relative h-44 overflow-hidden bg-gray-100">
        <img
          src={p.img}
          alt={p.name}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={(e) => {
            e.currentTarget.style.display = "none"
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <h3 className="absolute bottom-2 left-3 text-white font-extrabold text-lg drop-shadow">
          {p.name} Province
        </h3>
      </div>
      <div className="p-4 space-y-1.5 text-sm">
        <p className="text-gray-700"><span className="font-semibold">Famous:</span> {p.famous}</p>
        <p className="text-gray-600"><span className="font-semibold">Food:</span> {p.food}</p>
        <p className="text-gray-600"><span className="font-semibold">Festival:</span> {p.festival}</p>
      </div>
    </Link>
  )
}

export default function ProvinceMarquee() {
  const items = [...PROVINCES, ...PROVINCES]
  return (
    <section className="py-14 overflow-hidden bg-gradient-to-b from-white to-purple-50/40">
      <div className="container-app max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
            Discover all 7 provinces of Nepal
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Famous destinations, local food and festivals from east to west.
          </p>
        </div>
      </div>

      <div
        className="relative w-full overflow-hidden"
        style={{
          maskImage: "linear-gradient(to right, transparent, black 5%, black 95%, transparent)",
          WebkitMaskImage: "linear-gradient(to right, transparent, black 5%, black 95%, transparent)",
        }}
      >
        <div className="marquee-track flex gap-5 px-5 w-max motion-safe:animate-marquee hover:[animation-play-state:paused] focus-within:[animation-play-state:paused]">
          {items.map((p, i) => (
            <ProvinceCard key={`${p.name}-${i}`} p={p} />
          ))}
        </div>
      </div>
    </section>
  )
}
