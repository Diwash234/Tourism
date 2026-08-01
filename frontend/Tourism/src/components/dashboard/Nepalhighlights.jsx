import { motion } from "framer-motion"
import {
  FiTriangle, FiCompass, FiHome, FiFeather,
  FiWind, FiDroplet, FiMusic, FiCoffee,
} from "react-icons/fi"

// Content summarized in original wording from general, widely-known
// facts about Nepal tourism (Everest/Himalayas, UNESCO heritage sites,
// national parks, etc.) — not copied from any single source.
const HIGHLIGHTS = [
  {
    icon: FiTriangle,
    title: "The Himalayas",
    gradient: "from-himalaya-500 to-himalaya-700",
    desc: "Home to 8 of the world's 14 highest peaks, including Everest — the reason most travelers first think of Nepal.",
    tags: ["Everest", "Annapurna", "Langtang"],
  },
  {
    icon: FiCompass,
    title: "Trekking Routes",
    gradient: "from-forest-500 to-himalaya-600",
    desc: "From multi-week classics to shorter teahouse treks, routes exist for every fitness level and season.",
    tags: ["Everest Base Camp", "Annapurna Circuit", "Langtang Valley"],
  },
  {
    icon: FiHome,
    title: "Temples & Heritage",
    gradient: "from-saffron-500 to-nepalred-500",
    desc: "Kathmandu Valley alone holds seven UNESCO World Heritage Sites — living temples, not just ruins.",
    tags: ["Pashupatinath", "Boudhanath", "Kathmandu Durbar Square"],
  },
  {
    icon: FiFeather,
    title: "Wildlife Safaris",
    gradient: "from-forest-600 to-forest-400",
    desc: "The southern lowlands hold rhinos, Bengal tigers, elephants, and hundreds of bird species.",
    tags: ["Chitwan National Park", "Bardia National Park"],
  },
  {
    icon: FiWind,
    title: "Adventure Sports",
    gradient: "from-himalaya-600 to-saffron-500",
    desc: "Pokhara alone is one of the world's top spots for paragliding, alongside rafting, biking and more.",
    tags: ["Paragliding", "White-water Rafting", "Bungee Jumping"],
  },
  {
    icon: FiDroplet,
    title: "Peaceful Lakes",
    gradient: "from-himalaya-500 to-forest-500",
    desc: "Phewa Lake in Pokhara mirrors the Annapurna range on a clear morning — a favorite for boating.",
    tags: ["Phewa Lake", "Begnas Lake"],
  },
  {
    icon: FiMusic,
    title: "Culture & Festivals",
    gradient: "from-nepalred-500 to-saffron-500",
    desc: "Over 120 ethnic groups mean festivals happen almost year-round, each with its own traditions.",
    tags: ["Dashain", "Tihar", "Holi"],
  },
  {
    icon: FiCoffee,
    title: "Local Food",
    gradient: "from-saffron-600 to-forest-500",
    desc: "From daily staples to Newari feast cuisine, Nepali food varies dramatically by region and altitude.",
    tags: ["Dal Bhat", "Momo", "Sel Roti", "Thukpa"],
  },
]

const NepalHighlights = ({ bare = false }) => (
  <section className={bare ? "" : "container-app py-16"}>
    <h2 className="section-title text-center mx-auto w-fit">Why Visit Nepal</h2>
    <p className="text-gray-500 text-center max-w-2xl mx-auto mb-10 -mt-2">
      Beyond Everest — mountains, culture, wildlife, and hospitality that keep travelers coming back.
    </p>

    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {HIGHLIGHTS.map(({ icon: Icon, title, desc, tags, gradient }, i) => (
        <motion.div
          key={title}
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ delay: i * 0.05 }}
          className="card-base overflow-hidden"
        >
          <div className={`h-24 bg-gradient-to-br ${gradient} flex items-center justify-center`}>
            <Icon size={32} className="text-white/90" />
          </div>
          <div className="p-4">
            <h3 className="font-bold text-dark mb-1.5">{title}</h3>
            <p className="text-sm text-gray-500 mb-3">{desc}</p>
            <div className="flex flex-wrap gap-1.5">
              {tags.map((tag) => (
                <span key={tag} className="text-[11px] font-medium bg-gray-50 text-gray-500 px-2 py-1 rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  </section>
)

export default NepalHighlights