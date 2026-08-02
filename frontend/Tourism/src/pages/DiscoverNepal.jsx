import { useState } from "react"
import { motion } from "framer-motion"
import {
  FiClock,
  FiFeather,
  FiMusic,
  FiHome,
  FiGlobe,
  FiUsers,
  FiCoffee,
  FiTool,
  FiTriangle,
  FiMap,
  FiAward,
  FiSun,
  FiImage,
} from "react-icons/fi"

import NationalSymbols from "../components/dashboard/NationalSymbols"


const ERAS = [
  {
    name: "Kirat Period",
    range: "c. 800 BCE – 300 CE",
    desc: "Nepal's earliest recorded rulers, centered in the Kathmandu Valley; the era credited with the valley's earliest urban settlements.",
  },
  {
    name: "Licchavi Dynasty",
    range: "c. 400 – 750 CE",
    desc: "A golden age of stone inscriptions, temple-building, and trade links with Tibet and India that shaped early Newari culture.",
  },
  {
    name: "Malla Dynasty",
    range: "c. 1201 – 1769",
    desc: "The era of the three Durbar Squares (Kathmandu, Patan, Bhaktapur) — pagoda architecture, art, and literature flourished.",
  },
  {
    name: "Shah Dynasty",
    range: "1768 – 2008",
    desc: "Prithvi Narayan Shah's unification campaign created modern Nepal's borders; the monarchy that followed lasted over two centuries.",
  },
  {
    name: "Rana Era",
    range: "1846 – 1951",
    desc: "Hereditary prime ministers held real power while Shah kings became largely ceremonial; ended by a popular uprising.",
  },
  {
    name: "Federal Nepal",
    range: "2008 – present",
    desc: "Nepal became a federal democratic republic, abolishing the monarchy and adopting a new constitution in 2015.",
  },
]


const CULTURE_CARDS = [
  {
    title: "Kumari",
    image: "/images/discover/culture/kumari.jfif",
    desc: "A living goddess tradition unique to the Kathmandu Valley — a young girl worshipped as an incarnation of divine feminine energy.",
  },
  {
    title: "Prayer Wheels",
    image: "/images/discover/culture/prayer-wheels.jfif",
    desc: "Cylindrical wheels inscribed with mantras, spun by Buddhist practitioners as a form of prayer.",
  },
  {
    title: "Temples",
    image: "/images/discover/culture/temples.jfif",
    desc: "Pagoda-style Hindu temples and Buddhist stupas reflect centuries of religious harmony.",
  },
  {
    title: "Traditional Dances",
    image: "/images/discover/culture/traditional-dances.jfif",
    desc: "Lakhe, Sakela, and other dances preserve Nepal's ethnic and spiritual traditions.",
  },
  {
    title: "Traditional Music",
    image: "/images/discover/culture/traditional-music.jfif",
    desc: "Madal and Sarangi remain important instruments in Nepali folk music.",
  },
  {
    title: "Architecture",
    image: "/images/discover/culture/architectures.jfif",
    desc: "Pagoda roofs, carved windows, and Newari brickwork define Nepal's heritage architecture.",
  },
  {
    title: "Local Food",
    image: "/images/discover/culture/nepali-food.jfif",
    desc: "Dal Bhat, momo, sel roti, and Newari cuisine represent Nepal's diverse food culture.",
  },
  {
    title: "Heritage Sites",
    image: "/images/discover/culture/bhaktapur.jfif",
    desc: "Nepal's UNESCO heritage sites preserve history, religion, and architecture.",
  },
]


const FESTIVALS = [
  {
    name: "Dashain",
    image: "/images/discover/festivals/dashain.jpg",
    when: "Sept–Oct",
    desc: "Nepal's biggest Hindu festival celebrated with family gatherings and tika blessings.",
  },
  {
    name: "Tihar",
    image: "/images/discover/festivals/tihar.jpg",
    when: "Oct–Nov",
    desc: "Festival of lights celebrating animals, family bonds, and prosperity.",
  },
  {
    name: "Holi",
    image: "/images/discover/festivals/holi.jfif",
    when: "March",
    desc: "Festival of colors celebrated across Nepal.",
  },
  {
    name: "Indra Jatra",
    image: "/images/discover/festivals/indra-jatra.jpg",
    when: "Sept",
    desc: "Kathmandu's historic festival featuring chariot processions and dances.",
  },
  {
    name: "Bisket Jatra",
    image: "/images/discover/festivals/biscuit-jatra.jfif",
    when: "April",
    desc: "Bhaktapur's famous New Year chariot festival.",
  },
  {
    name: "Losar",
    image: "/images/discover/festivals/losar.jfif",
    when: "Feb",
    desc: "Tibetan and Sherpa New Year celebrated with prayers and gatherings.",
  },
]


const WILDLIFE = [
  {
    name: "Chitwan National Park",
    image: "/images/discover/wildlife/chitwan.jfif",
    desc: "Home to rhinos, Bengal tigers, elephants, and gharial crocodiles.",
  },
  {
    name: "Bardia National Park",
    image: "/images/discover/wildlife/bardia.jfif",
    desc: "A remote wilderness area known for tigers and river wildlife.",
  },
  {
    name: "Sagarmatha National Park",
    image: "/images/discover/wildlife/sagarmatha.jfif",
    desc: "Everest region with Himalayan wildlife including snow leopards.",
  },  
  { 
    name: "Annapurna Conservation Area",
    image: "/images/discover/wildlife/annapurna.jfif ",
    desc: "A biodiversity hotspot covering multiple altitude zones.",
  },
]


const UNESCO_SITES = [
  "Kathmandu Durbar Square",
  "Patan Durbar Square",
  "Bhaktapur Durbar Square",
  "Pashupatinath Temple",
  "Swayambhunath Stupa",
  "Boudhanath Stupa",
  "Changu Narayan Temple",
  "Lumbini",
  "Sagarmatha National Park",
  "Chitwan National Park",
]


const NATIONAL_PARKS = [
  "Chitwan",
  "Bardia",
  "Sagarmatha",
  "Langtang",
  "Shivapuri Nagarjun",
  "Rara",
]


const MOUNTAINS = [
  "Everest (8,849m)",
  "Kangchenjunga (8,586m)",
  "Lhotse (8,516m)",
  "Makalu (8,485m)",
  "Cho Oyu (8,188m)",
  "Dhaulagiri (8,167m)",
  "Manaslu (8,163m)",
  "Annapurna I (8,091m)",
]


const ETHNIC_GROUPS = [
  "Newar",
  "Sherpa",
  "Gurung",
  "Magar",
  "Tamang",
  "Tharu",
  "Rai",
  "Limbu",
  "Chhetri",
  "Brahmin",
]


const PROVINCES = [
  {
    name: "Koshi",
    capital: "Biratnagar",
    highlight: "Eastern hills, tea gardens, and Kanchenjunga views",
  },
  {
    name: "Madhesh",
    capital: "Janakpur",
    highlight: "Terai culture and Janaki Temple",
  },
  {
    name: "Bagmati",
    capital: "Kathmandu",
    highlight: "Capital region and Kathmandu Valley heritage",
  },
  {
    name: "Gandaki",
    capital: "Pokhara",
    highlight: "Annapurna range and Phewa Lake",
  },
  {
    name: "Lumbini",
    capital: "Butwal/Deukhuri",
    highlight: "Birthplace of Buddha",
  },
  {
    name: "Karnali",
    capital: "Surkhet",
    highlight: "Rara Lake and remote Himalayan landscapes",
  },
  {
    name: "Sudurpashchim",
    capital: "Dhangadhi",
    highlight: "Western Nepal wildlife corridor",
  },
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
      <Icon className="text-himalaya-500" />
      {title}
    </h2>

    {children}
  </motion.section>
)


const Chip = ({ children }) => (
  <span className="text-xs font-medium bg-gray-50 text-gray-600 px-3 py-1.5 rounded-full border border-gray-100">
    {children}
  </span>
)


const CardImage = ({ src, alt, icon: Icon }) => {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <div className="w-full h-28 rounded-lg mb-3 bg-himalaya-50 flex items-center justify-center text-himalaya-300">
        {Icon ? <Icon size={26} /> : <FiImage size={26} />}
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      className="w-full h-28 rounded-lg mb-3 object-cover bg-gray-100"
    />
  )
}



const DiscoverNepal = () => (
  <div className="container-app py-10 fade-in">

    <div className="mb-8">
      <h1 className="text-3xl md:text-4xl font-heading font-bold text-himalaya-500">
        Discover Nepal
      </h1>

      <p className="text-gray-500 mt-2 max-w-2xl">
        History, culture, wildlife, and heritage — everything that makes Nepal more than just a mountain.
      </p>
    </div>


    <NationalSymbols />


    <Section
      id="history"
      icon={FiClock}
      title="History — Six Eras"
    >
      <div className="relative border-l border-gray-100 ml-3 mt-6">

        {ERAS.map((era) => (
          <div
            key={era.name}
            className="mb-6 ml-6 last:mb-0"
          >

            <span className="absolute w-3 h-3 rounded-full bg-himalaya-500 -ml-[31px] mt-1.5 ring-4 ring-white" />

            <div className="card-base p-4">

              <div className="flex justify-between gap-3 flex-wrap">

                <h3 className="font-semibold text-dark">
                  {era.name}
                </h3>

                <span className="text-xs text-gray-400">
                  {era.range}
                </span>

              </div>

              <p className="text-sm text-gray-500 mt-1">
                {era.desc}
              </p>

            </div>

          </div>
        ))}

      </div>

    </Section>



    <Section
      id="culture"
      icon={FiFeather}
      title="Culture"
    >

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">

        {CULTURE_CARDS.map((item) => (

          <div
            key={item.title}
            className="card-base p-4"
          >

            <CardImage
              src={item.image}
              alt={item.title}
              icon={FiFeather}
            />

            <h3 className="font-semibold text-sm mb-1">
              {item.title}
            </h3>

            <p className="text-xs text-gray-500">
              {item.desc}
            </p>

          </div>

        ))}

      </div>

    </Section>



    <Section
      id="festivals"
      icon={FiSun}
      title="Festivals"
    >

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">

        {FESTIVALS.map((festival)=>(

          <div
            key={festival.name}
            className="card-base p-4"
          >

            <CardImage
              src={festival.image}
              alt={festival.name}
              icon={FiSun}
            />


            <div className="flex justify-between mb-1">

              <h3 className="font-semibold text-sm">
                {festival.name}
              </h3>

              <span className="text-[10px] bg-saffron-50 text-saffron-600 px-2 py-1 rounded-full">
                {festival.when}
              </span>

            </div>


            <p className="text-xs text-gray-500">
              {festival.desc}
            </p>


          </div>

        ))}

      </div>

    </Section>



    <Section
      id="wildlife"
      icon={FiAward}
      title="Wildlife"
    >

      <div className="grid sm:grid-cols-2 gap-4">

        {WILDLIFE.map((animal)=>(

          <div
            key={animal.name}
            className="card-base p-4"
          >

            <CardImage
              src={animal.image}
              alt={animal.name}
              icon={FiAward}
            />

            <h3 className="font-semibold text-sm">
              {animal.name}
            </h3>

            <p className="text-xs text-gray-500">
              {animal.desc}
            </p>

          </div>

        ))}

      </div>

    </Section>



    <Section
      id="unesco"
      icon={FiHome}
      title="UNESCO World Heritage Sites"
    >

      <div className="flex flex-wrap gap-2">

        {UNESCO_SITES.map(site=>(
          <Chip key={site}>
            {site}
          </Chip>
        ))}

      </div>

    </Section>



    <Section
      id="national-parks"
      icon={FiTriangle}
      title="National Parks"
    >

      <div className="flex flex-wrap gap-2">

        {NATIONAL_PARKS.map(item=>(
          <Chip key={item}>
            {item}
          </Chip>
        ))}

      </div>

    </Section>



    <Section
      id="dress-music-architecture"
      icon={FiMusic}
      title="Traditional Dress, Music & Architecture"
    >

      <div className="grid sm:grid-cols-3 gap-4">

        <div className="card-base p-4">
          <h3 className="font-semibold text-sm">
            Traditional Dress
          </h3>

          <p className="text-xs text-gray-500 mt-1">
            Daura-Suruwal, Dhaka Topi, Gunyu Cholo and Haku Patasi represent Nepal's diverse clothing traditions.
          </p>
        </div>


        <div className="card-base p-4">

          <h3 className="font-semibold text-sm">
            Music & Dance
          </h3>

          <p className="text-xs text-gray-500 mt-1">
            Madal, Sarangi, Lakhe dance and Sakela preserve Nepal's cultural identity.
          </p>

        </div>


        <div className="card-base p-4">

          <h3 className="font-semibold text-sm">
            Architecture
          </h3>

          <p className="text-xs text-gray-500 mt-1">
            Pagoda temples, carved windows and Newari architecture define Nepal's heritage.
          </p>

        </div>


      </div>

    </Section>



    <Section
      id="religion-languages"
      icon={FiGlobe}
      title="Religion & Languages"
    >

      <p className="text-sm text-gray-600 max-w-3xl">
        Hinduism and Buddhism have coexisted in Nepal for centuries.
        Nepal has more than 120 languages, with Nepali as the official language.
      </p>

    </Section>



    <Section
      id="ethnic-groups"
      icon={FiUsers}
      title="Ethnic Groups"
    >

      <div className="flex flex-wrap gap-2">

        {ETHNIC_GROUPS.map(group=>(
          <Chip key={group}>
            {group}
          </Chip>
        ))}

      </div>

    </Section>



    <Section
      id="local-food"
      icon={FiCoffee}
      title="Local Food"
    >

      <p className="text-sm text-gray-600">
        Dal Bhat, momo, sel roti, thukpa and Newari cuisine represent Nepal's rich food culture.
      </p>

    </Section>



    <Section
      id="crafts"
      icon={FiTool}
      title="Traditional Crafts"
    >

      <div className="flex flex-wrap gap-2">

        {[
          "Lokta Paper",
          "Thangka Painting",
          "Pashmina Weaving",
          "Wood Carving",
          "Metal Statue Casting",
          "Dhaka Weaving",
        ].map(item=>(
          <Chip key={item}>
            {item}
          </Chip>
        ))}

      </div>

    </Section>



    <Section
      id="mountains"
      icon={FiTriangle}
      title="Mountains"
    >

      <div className="flex flex-wrap gap-2">

        {MOUNTAINS.map(mountain=>(
          <Chip key={mountain}>
            {mountain}
          </Chip>
        ))}

      </div>

    </Section>



    <Section
      id="provinces"
      icon={FiMap}
      title="Province Information"
    >

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">

        {PROVINCES.map(province=>(

          <div
            key={province.name}
            className="card-base p-4"
          >

            <h3 className="font-semibold text-sm">
              {province.name}
            </h3>

            <p className="text-xs text-gray-400">
              Capital: {province.capital}
            </p>

            <p className="text-xs text-gray-500 mt-1">
              {province.highlight}
            </p>

          </div>

        ))}

      </div>

    </Section>


  </div>
)


export default DiscoverNepal