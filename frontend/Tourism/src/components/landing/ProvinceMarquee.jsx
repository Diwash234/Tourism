import React from "react"
import { Link } from "react-router-dom"

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
      className="group shrink-0 w-72 sm:w-80 rounded-3xl overflow-hidden border border-[#E5E0D5] bg-white shadow-sm hover:shadow-2xl transition-all duration-300"
    >
      <div className="relative h-44 overflow-hidden bg-slate-100">
        <img
          src={p.img}
          alt={p.name}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          onError={(e) => {
            e.currentTarget.style.display = "none"
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#102A2E] via-[#102A2E]/40 to-transparent opacity-90" />
        <h3 className="absolute bottom-3 left-4 text-white font-black text-lg drop-shadow">
          {p.name} Province
        </h3>
      </div>
      <div className="p-4 space-y-2 text-xs text-[#172022]">
        <p className="leading-relaxed"><b className="text-[#102A2E] font-bold">Famous:</b> {p.famous}</p>
        <p className="leading-relaxed"><b className="text-[#1D5146] font-bold">Cuisine:</b> {p.food}</p>
        <p className="leading-relaxed"><b className="text-[#D99048] font-bold">Festivals:</b> {p.festival}</p>
      </div>
    </Link>
  )
}

export default function ProvinceMarquee() {
  const items = [...PROVINCES, ...PROVINCES]
  return (
    <section className="section-space overflow-hidden bg-gradient-to-b from-white to-[#F7F8F5] border-t border-[#E5E0D5]">
      <div className="container-app max-w-6xl mx-auto px-4 mb-8 text-center">
        <span className="px-3.5 py-1 rounded-full bg-[#E5E0D5] text-[#102A2E] text-xs font-black uppercase tracking-widest">
          SEVEN PROVINCES OF NEPAL
        </span>
        <h2 className="text-3xl sm:text-4xl font-black text-[#172022] mt-2 tracking-tight">
          Explore Regional Attractions & Living Heritage
        </h2>
        <p className="text-sm text-[#697675] mt-1 max-w-2xl mx-auto">
          From the tea hills of Koshi to the mountain passes of Sudurpashchim.
        </p>
      </div>

      <div
        className="relative w-full overflow-hidden"
        style={{
          maskImage: "linear-gradient(to right, transparent, black 5%, black 95%, transparent)",
          WebkitMaskImage: "linear-gradient(to right, transparent, black 5%, black 95%, transparent)",
        }}
      >
        <div className="marquee-track flex gap-6 px-5 w-max motion-safe:animate-marquee hover:[animation-play-state:paused] focus-within:[animation-play-state:paused]">
          {items.map((p, i) => (
            <ProvinceCard key={`${p.name}-${i}`} p={p} />
          ))}
        </div>
      </div>
    </section>
  )
}
