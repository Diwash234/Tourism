import { motion } from "framer-motion"
import {
  FiClock, FiFeather, FiMusic, FiHome, FiGlobe, FiUsers,
  FiCoffee, FiTool, FiTriangle, FiMap, FiAward, FiSun,
} from "react-icons/fi"
import NationalSymbols from "../components/dashboard/NationalSymbols"

/**
 * DiscoverNepal — a single, well-built hub instead of ~15 separate thin
 * pages. Reasoning (same as the Culture/Local Experience call earlier):
 * the backend has no content models for History/Festivals/Wildlife/
 * UNESCO Sites/Traditional Dress/etc — building that many disconnected
 * pages with no real data behind them would be worse UX than one rich,
 * anchor-linked page with curated content written in original wording.
 * Sidebar "Discover Nepal" group links here with #anchors per topic.
 */

const ERAS = [
  { name: "Kirat Period", range: "c. 800 BCE – 300 CE", desc: "Nepal's earliest recorded rulers, centered in the Kathmandu Valley; the era credited with the valley's earliest urban settlements." },
  { name: "Licchavi Dynasty", range: "c. 400 – 750 CE", desc: "A golden age of stone inscriptions, temple-building, and trade links with Tibet and India that shaped early Newari culture." },
  { name: "Malla Dynasty", range: "c. 1201 – 1769", desc: "The era of the three Durbar Squares (Kathmandu, Patan, Bhaktapur) — pagoda architecture, art, and literature flourished." },
  { name: "Shah Dynasty", range: "1768 – 2008", desc: "Prithvi Narayan Shah's unification campaign created modern Nepal's borders; the monarchy that followed lasted over two centuries." },
  { name: "Rana Era", range: "1846 – 1951", desc: "Hereditary prime ministers held real power while the Shah kings became largely ceremonial; ended by a popular uprising." },
  { name: "Federal Nepal", range: "2008 – present", desc: "Nepal became a federal democratic republic, abolishing the monarchy and adopting a new constitution in 2015." },
]

const CULTURE_CARDS = [
  { title: "Kumari", desc: "A living goddess tradition unique to the Kathmandu Valley — a young girl worshipped as an incarnation of the divine feminine." },
  { title: "Prayer Wheels", desc: "Cylindrical wheels inscribed with mantras, spun by Buddhist practitioners as a form of prayer, common around stupas." },
  { title: "Temples", desc: "Pagoda-style Hindu temples and Buddhist stupas often stand within the same neighborhoods, reflecting centuries of coexistence." },
  { title: "Traditional Dances", desc: "From the masked Lakhe dance to the Sakela of the Kirat communities, dance carries distinct ethnic and religious meaning." },
  { title: "Traditional Music", desc: "Instruments like the Madal (hand drum) and Sarangi (bowed fiddle) anchor Nepali folk music traditions." },
  { title: "Architecture", desc: "Multi-tiered pagoda roofs, intricately carved wooden windows, and Newari brickwork define much of the valley's skyline." },
  { title: "Local Food", desc: "Dal Bhat is the daily staple nationwide, while momo, sel roti, and Newari feast cuisine vary sharply by region." },
  { title: "Heritage Sites", desc: "Nepal holds 10 UNESCO World Heritage Sites, seven of them within the Kathmandu Valley alone." },
]

const FESTIVALS = [
  { name: "Dashain", when: "Sept–Oct", desc: "The longest and most significant Hindu festival, marked by family gatherings and tika blessings." },
  { name: "Tihar", when: "Oct–Nov", desc: "The festival of lights, honoring crows, dogs, cows, and the bond between brothers and sisters." },
  { name: "Holi", when: "March", desc: "The festival of colors, celebrated with powder and water fights nationwide." },
  { name: "Indra Jatra", when: "Sept", desc: "Kathmandu's chariot festival honoring the Kumari and the god Indra, with masked dances." },
  { name: "Bisket Jatra", when: "April", desc: "Bhaktapur's dramatic chariot-pulling New Year festival." },
  { name: "Gai Jatra", when: "Aug–Sept", desc: "The 'cow festival' commemorating those who died in the past year, marked by satire and processions." },
  { name: "Losar", when: "Feb", desc: "Tibetan/Sherpa New Year, celebrated with prayer flags, dance, and family feasts in the high Himalaya." },
  { name: "Teej", when: "Aug–Sept", desc: "A women's festival of fasting and dance for marital happiness and family wellbeing." },
  { name: "Chhath", when: "Oct–Nov", desc: "A Terai-region festival worshipping the sun god, observed at riverbanks and ponds." },
  { name: "Maghe Sankranti", when: "Jan", desc: "Marks the winter solstice's end with sesame sweets and ghee-based dishes." },
  { name: "Janai Purnima", when: "Aug", desc: "Hindu men renew a sacred thread (janai); also a Rakhi-tying festival for siblings." },
  { name: "Buddha Jayanti", when: "May", desc: "Celebrates Buddha's birth, enlightenment, and death — especially significant since he was born in Lumbini, Nepal." },
]

const WILDLIFE = [
  { name: "Chitwan National Park", desc: "One-horned rhinos, Bengal tigers, and gharial crocodiles in the Terai lowlands." },
  { name: "Bardia National Park", desc: "Nepal's largest wilderness area — tigers, elephants, and the Karnali River's fresh-water dolphins." },
  { name: "Sagarmatha National Park", desc: "Everest's home turf — snow leopards, Himalayan tahr, and red pandas at altitude." },
  { name: "Annapurna Conservation Area", desc: "Extraordinary bird diversity across dramatically varied elevation zones." },
]

const UNESCO_SITES = [
  "Kathmandu Durbar Square", "Patan Durbar Square", "Bhaktapur Durbar Square",
  "Pashupatinath Temple", "Swayambhunath Stupa", "Boudhanath Stupa",
  "Changu Narayan Temple", "Lumbini (Buddha's birthplace)",
  "Sagarmatha National Park", "Chitwan National Park",
]

const NATIONAL_PARKS = ["Chitwan", "Bardia", "Sagarmatha", "Langtang", "Shivapuri Nagarjun", "Rara"]

const MOUNTAINS = ["Everest (8,849m)", "Kangchenjunga (8,586m)", "Lhotse (8,516m)", "Makalu (8,485m)", "Cho Oyu (8,188m)", "Dhaulagiri (8,167m)", "Manaslu (8,163m)", "Annapurna I (8,091m)"]

const ETHNIC_GROUPS = ["Newar", "Sherpa", "Gurung", "Magar", "Tamang", "Tharu", "Rai", "Limbu", "Chhetri", "Brahmin"]

const PROVINCES = [
  { name: "Koshi", capital: "Biratnagar", highlight: "Eastern hill tea gardens and Kanchenjunga views" },
  { name: "Madhesh", capital: "Janakpur", highlight: "Terai plains and the Janaki Temple" },
  { name: "Bagmati", capital: "Kathmandu", highlight: "The capital region and Kathmandu Valley heritage" },
  { name: "Gandaki", capital: "Pokhara", highlight: "Annapurna range and Phewa Lake" },
  { name: "Lumbini", capital: "Butwal/Deukhuri", highlight: "Buddha's birthplace" },
  { name: "Karnali", capital: "Surkhet", highlight: "Nepal's largest, least-visited province — Rara Lake" },
  { name: "Sudurpashchim", capital: "Dhangadhi", highlight: "Far-western Nepal, Bardia's wildlife corridor" },
]

const Section = ({ id, icon: Icon, title, children }) => (
  <motion.section
    id={id}
    initial={{ opacity: 0, y: 12 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-60px" }}
    className="scroll-mt-24 py-10 border-b border-gray-100 last:border-0"
  >
    <h2 className="section-title flex items-center gap-2">
      <Icon className="text-himalaya-500" /> {title}
    </h2>
    {children}
  </motion.section>
)

const Chip = ({ children }) => (
  <span className="text-xs font-medium bg-gray-50 text-gray-600 px-3 py-1.5 rounded-full border border-gray-100">
    {children}
  </span>
)

const DiscoverNepal = () => (
  <div className="container-app py-10 fade-in">
    <div className="mb-8">
      <h1 className="text-3xl md:text-4xl font-heading font-bold text-himalaya-500">Discover Nepal</h1>
      <p className="text-gray-500 mt-2 max-w-2xl">
        History, culture, wildlife, and heritage — everything that makes Nepal more than just a mountain.
      </p>
    </div>

    <NationalSymbols />

    <Section id="history" icon={FiClock} title="History — Five Eras">
      <div className="relative border-l border-gray-100 ml-3 mt-6">
        {ERAS.map((era) => (
          <div key={era.name} className="mb-6 ml-6 last:mb-0">
            <span className="absolute w-3 h-3 rounded-full bg-himalaya-500 -ml-[31px] mt-1.5 ring-4 ring-white" />
            <div className="card-base p-4">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <h3 className="font-semibold text-dark">{era.name}</h3>
                <span className="text-xs text-gray-400">{era.range}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{era.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </Section>

    <Section id="culture" icon={FiFeather} title="Culture">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
        {CULTURE_CARDS.map((c) => (
          <div key={c.title} className="card-base p-4">
            <h3 className="font-semibold text-sm mb-1">{c.title}</h3>
            <p className="text-xs text-gray-500">{c.desc}</p>
          </div>
        ))}
      </div>
    </Section>

    <Section id="festivals" icon={FiSun} title="Festivals">
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
        {FESTIVALS.map((f) => (
          <div key={f.name} className="card-base p-4">
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-semibold text-sm">{f.name}</h3>
              <span className="text-[10px] font-medium text-saffron-600 bg-saffron-50 px-2 py-0.5 rounded-full">{f.when}</span>
            </div>
            <p className="text-xs text-gray-500">{f.desc}</p>
          </div>
        ))}
      </div>
    </Section>

    <Section id="wildlife" icon={FiAward} title="Wildlife">
      <div className="grid sm:grid-cols-2 gap-4 mt-2">
        {WILDLIFE.map((w) => (
          <div key={w.name} className="card-base p-4">
            <h3 className="font-semibold text-sm mb-1">{w.name}</h3>
            <p className="text-xs text-gray-500">{w.desc}</p>
          </div>
        ))}
      </div>
    </Section>

    <Section id="unesco" icon={FiHome} title="UNESCO World Heritage Sites">
      <div className="flex flex-wrap gap-2 mt-2">
        {UNESCO_SITES.map((s) => <Chip key={s}>{s}</Chip>)}
      </div>
    </Section>

    <Section id="national-parks" icon={FiTriangle} title="National Parks">
      <div className="flex flex-wrap gap-2 mt-2">
        {NATIONAL_PARKS.map((p) => <Chip key={p}>{p}</Chip>)}
      </div>
    </Section>

    <Section id="dress-music-architecture" icon={FiMusic} title="Traditional Dress, Music & Architecture">
      <div className="grid sm:grid-cols-3 gap-4 mt-2">
        <div className="card-base p-4">
          <h3 className="font-semibold text-sm mb-1">Traditional Dress</h3>
          <p className="text-xs text-gray-500">Daura-Suruwal and Dhaka Topi for men; Gunyu Cholo and regional variants like the Newari Haku Patasi for women.</p>
        </div>
        <div className="card-base p-4">
          <h3 className="font-semibold text-sm mb-1">Music & Dance</h3>
          <p className="text-xs text-gray-500">The Madal (hand drum) and Sarangi (bowed fiddle) anchor folk music; Lakhe and Sakela are among the best-known dance forms.</p>
        </div>
        <div className="card-base p-4">
          <h3 className="font-semibold text-sm mb-1">Architecture</h3>
          <p className="text-xs text-gray-500">Multi-tiered pagoda roofs, carved wooden windows, and Newari brickwork define much of the Kathmandu Valley.</p>
        </div>
      </div>
    </Section>

    <Section id="religion-languages" icon={FiGlobe} title="Religion & Languages">
      <p className="text-sm text-gray-600 max-w-3xl">
        Hinduism and Buddhism have coexisted in Nepal for centuries, often sharing the same sacred sites. Over 120 languages
        are spoken across the country; Nepali serves as the official lingua franca, while Newari, Maithili, Bhojpuri,
        Tamang, and dozens of others remain in daily use regionally.
      </p>
    </Section>

    <Section id="ethnic-groups" icon={FiUsers} title="Ethnic Groups">
      <div className="flex flex-wrap gap-2 mt-2">
        {ETHNIC_GROUPS.map((e) => <Chip key={e}>{e}</Chip>)}
      </div>
    </Section>

    <Section id="local-food" icon={FiCoffee} title="Local Food">
      <p className="text-sm text-gray-600 max-w-3xl">
        Dal Bhat (lentils and rice) is the daily staple nationwide. Momo dumplings, Sel Roti (a ring-shaped rice bread),
        Thukpa noodle soup, and elaborate Newari feast cuisine each carry distinct regional identities.
      </p>
    </Section>

    <Section id="crafts" icon={FiTool} title="Traditional Crafts">
      <div className="flex flex-wrap gap-2 mt-2">
        {["Lokta Paper", "Thangka Painting", "Pashmina Weaving", "Wood Carving", "Metal Statue Casting", "Dhaka Weaving"].map((c) => (
          <Chip key={c}>{c}</Chip>
        ))}
      </div>
    </Section>

    <Section id="mountains" icon={FiTriangle} title="Mountains">
      <div className="flex flex-wrap gap-2 mt-2">
        {MOUNTAINS.map((m) => <Chip key={m}>{m}</Chip>)}
      </div>
    </Section>

    <Section id="provinces" icon={FiMap} title="Province Information">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
        {PROVINCES.map((p) => (
          <div key={p.name} className="card-base p-4">
            <h3 className="font-semibold text-sm">{p.name}</h3>
            <p className="text-xs text-gray-400 mb-1">Capital: {p.capital}</p>
            <p className="text-xs text-gray-500">{p.highlight}</p>
          </div>
        ))}
      </div>
    </Section>
  </div>
)

export default DiscoverNepal