import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import {
  FiBookOpen, FiX, FiAward, FiCoffee, FiMap, FiSun,
  FiCompass, FiTriangle, FiCheckCircle, FiInfo, FiLayers, FiCalendar
} from "react-icons/fi";

import FlagImg from "./flag,png.jfif";
import MapImg from "./map.jfif";
import CowImg from "./cow.jfif";
import DanpheImg from "./images.jfif";
import RhododendronImg from "./rhododendron.jfif";
import EmblemImg from "./emblem.jfif";
import TopiImg from "./dhaka-topi.jfif";
import StupaImg from "./stupa.jfif";

// Export images so other components can use them
export {
  FlagImg,
  MapImg,
  CowImg,
  DanpheImg,
  RhododendronImg,
  EmblemImg,
  TopiImg,
  StupaImg,
};

export const SUMMARY_SYMBOLS = [
  {
    image: FlagImg,
    label: "National Flag",
    fact: "The only non-rectangular national flag in the world",
  },
  {
    image: MapImg,
    label: "Nepal Map",
    fact: "7 provinces from Terai to the Himalayas",
  },
  {
    image: CowImg,
    label: "National Animal",
    fact: "The cow is Nepal's sacred national animal",
  },
  {
    image: DanpheImg,
    label: "National Bird",
    fact: "Danphe (Himalayan Monal)",
  },
  {
    image: RhododendronImg,
    label: "National Flower",
    fact: "Lali Gurans — Nepal's national flower",
  },
  {
    image: EmblemImg,
    label: "National Emblem",
    fact: "Symbol of Nepal's unity & Everest",
  },
  {
    image: TopiImg,
    label: "Dhaka Topi",
    fact: "Traditional Nepali cap",
  },
  {
    image: StupaImg,
    label: "Stupa",
    fact: "Buddhist heritage monuments",
  },
];

export const ALL_26_NATIONAL_SYMBOLS = [
  { id: "flag", category: "National Flag", title: "National Flag", icon: "🏳️", nepali: "राष्ट्रिय झण्डा", value: "Unique double-triangle flag with sun and moon, symbolizing the Himalayas and eternal bravery.", image: FlagImg },
  { id: "emblem", category: "National Emblem", title: "National Emblem / Coat of Arms", icon: "🪶", nepali: "राष्ट्रिय निशान छाप", value: "Features Mount Everest, green hills, rhododendron wreath, female/male hands shaking, and national motto.", image: EmblemImg },
  { id: "animal", category: "National Animal", title: "National Animal", icon: "🐾", nepali: "गाय (Gai)", value: "The sacred Cow (Gai), symbolizing peace, prosperity, and motherly care.", image: CowImg },
  { id: "bird", category: "National Bird", title: "National Bird", icon: "🐦", nepali: "डाँफे (Danphe)", value: "Himalayan Monal (Danphe), iridescent 9-colored high alpine pheasant living in high ranges.", image: DanpheImg },
  { id: "flower", category: "National Flower", title: "National Flower", icon: "🌸", nepali: "लालीगुराँस (Lali Gurans)", value: "Rhododendron arboreum (Lali Gurans), blooming crimson across high hill forests in spring.", image: RhododendronImg },
  { id: "dress", category: "National Dress", title: "National Dress / Costume", icon: "🎭", nepali: "दौरा सुरूवाल र ढाका टोपी / गुन्यू चोली", value: "Daura Suruwal with traditional Dhaka Topi for men & Gunyu Cholo for women.", image: TopiImg },
  { id: "map", category: "Geographic Map", title: "Nepal Sovereign Territory", icon: "🗺️", nepali: "नेपालको नक्सा", value: "147,516 km² spanning Terai plains, mid-hill valleys, and high Himalayas across 7 provinces.", image: MapImg },
  { id: "stupa", category: "Heritage Stupa", title: "Buddhist Stupa Heritage", icon: "☸️", nepali: "बौद्ध स्तुप सम्पदा", value: "Ancient stupa architecture representing enlightenment, peace, and wisdom (Swayambhu & Boudha).", image: StupaImg },
  
  { id: "tree", category: "National Tree", title: "National Tree", icon: "🌳", nepali: "पीपल (Peepal / Sacred Fig)", value: "Peepal tree (Ficus religiosa), revered for providing shade, continuous oxygen, and spiritual sanctuary.", image: "/images/destinations/bandipur/hilltop-village.jpg" },
  { id: "fruit", category: "National Fruit", title: "National Fruit", icon: "🍎", nepali: "आँप (Mango / Aap)", value: "Juicy Terai and mid-hill mangoes harvested during sunny summer months.", image: "/images/destinations/chitwan/safari.jpg" },
  { id: "anthem", category: "National Anthem", title: "National Anthem", icon: "🎵", nepali: "सयौं थुँगा फूलका", value: "'Sayaun Thunga Phool Ka' celebrating national sovereignty and unity across 120+ ethnic groups.", image: FlagImg },
  { id: "currency", category: "National Currency", title: "National Currency", icon: "💰", nepali: "नेपाली रुपैयाँ (NPR 1,000 Note)", value: "Nepali Rupee (NPR / Re / Rs), issued by Nepal Rastra Bank with Mt. Everest & twin elephants.", image: EmblemImg },
  { id: "language", category: "Official Language", title: "Official Language (Devanagari)", icon: "🗣️", nepali: "नेपाली भाषा (क, ख, ग, घ, ङ)", value: "Nepali (Devanagari script), spoken alongside 120+ indigenous languages across 77 districts.", image: StupaImg },
  { id: "capital", category: "Capital City", title: "Capital City", icon: "🏛️", nepali: "काठमाडौं (Kathmandu)", value: "Kathmandu Valley (1,400m altitude), historic City of Temples and cultural crossroads.", image: "/images/destinations/kathmandu/durbar-square.jpg" },
  { id: "governance", category: "Head of State / State", title: "State System & Governance", icon: "👑", nepali: "संघीय लोकतान्त्रिक गणतन्त्र", value: "Federal Democratic Republic of Nepal governed under the 2015 Constitution.", image: EmblemImg },
  { id: "sport", category: "National Sport", title: "National Sport (Volleyball)", icon: "🏞️", nepali: "भलिबल (Volleyball)", value: "Volleyball, officially declared national sport played in mountain villages and valley courts.", image: "/images/destinations/pokhara/fewatal.jpg" },
  { id: "dish", category: "National Dish", title: "National Food / Dish", icon: "🍲", nepali: "दाल भात तरकारी", value: "Dal Bhat Tarkari (Steamed rice, lentil soup, seasonal curried vegetables, Gundruk, and pickle).", image: "/images/destinations/food/newari-bhoj.jpg" },
  { id: "fish", category: "National Fish", title: "National Fish", icon: "🐟", nepali: "सहर (Sahar / Golden Mahseer)", value: "Sahar (Tor putitora / Himalayan Golden Mahseer), king of fast-flowing snow-fed Himalayan rivers.", image: "/images/destinations/koshi-tappu/wetlands.jpg" },
  { id: "river", category: "National River", title: "Major Sacred River Systems", icon: "🌊", nepali: "सप्तकोशी, गण्डकी, कर्णाली", value: "Karnali (longest), Gandaki, and Koshi snow-fed Himalayan river basins.", image: "/images/destinations/koshi-tappu/wetlands.jpg" },
  { id: "mountain", category: "National Mountain", title: "National Mountain Peak", icon: "🏔️", nepali: "सगरमाथा (Mount Everest)", value: "Mount Everest / Sagarmatha (8,848.86 m), highest peak on Earth located in Mahalangur Himal.", image: "/images/destinations/everest/base-camp.jpg" },
  { id: "dance", category: "National Dance", title: "National Heritage Dance", icon: "💃", nepali: "मारुनी र लाखे नाच", value: "Maruni, Lakhey, and Charya cultural dances celebrating harvests and spiritual myths.", image: DanpheImg },
  { id: "motto", category: "National Motto", title: "National Motto", icon: "🦅", nepali: "जननी जन्मभूमिश्च स्वर्गादपि गरीयसी", value: "'Janani Janmabhumischa Swargadapi Gariyasi' — Mother and motherland are dearer than heaven itself.", image: EmblemImg },
  { id: "poet", category: "National Poet", title: "National Poet / Adikavi", icon: "✍️", nepali: "राष्ट्रकवि माधवप्रसाद घिमिरे / भानुभक्त", value: "Bhanubhakta Acharya (Adikavi) & Madhav Prasad Ghimire (Rashtrakavi).", image: TopiImg },
  { id: "day", category: "Constitution / National Day", title: "National Constitution Day", icon: "📜", nepali: "संविधान दिवस (Ashoj 3 / Sept 20)", value: "Constitution Day celebrating democratic constitutional rule (Promulgated Sept 20, 2015).", image: FlagImg },
  { id: "gemstone", category: "Himalayan Gemstone", title: "National Gemstone", icon: "💎", nepali: "नेपाली काईनाइट र रुबी", value: "Ganesh Himal Quartz, Himalayan Kyanite, and Ruby mined in high altitudes.", image: "/images/destinations/tilicho/himalayan-lake.jpg" },
  { id: "plant", category: "Sacred Medicinal Herb", title: "Sacred Plant / Herb", icon: "🌿", nepali: "यार्सागुम्बा / जिम्बु", value: "Yarsagumba (Cordyceps sinensis) & Himalayan Jimbu mountain herbs.", image: "/images/destinations/gosaikunda/glacial-lake.jpg" },
  { id: "insect", category: "National Butterfly", title: "National Insect / Butterfly", icon: "🐝", nepali: "कृष्णा कालीज (Kaiser-i-Hind)", value: "Kaiser-i-Hind & Himalayan Swallowtail butterflies in high forest reserves.", image: DanpheImg },
];

export const EIGHT_THOUSANDERS = [
  { rank: 1, name: "Mount Everest (Sagarmatha)", height: "8,848.86 m", region: "Solukhumbu", range: "Mahalangur Himal" },
  { rank: 2, name: "Kanchenjunga", height: "8,586 m", region: "Taplejung", range: "Kanchenjunga Himal" },
  { rank: 3, name: "Lhotse", height: "8,516 m", region: "Solukhumbu", range: "Mahalangur Himal" },
  { rank: 4, name: "Makalu", height: "8,485 m", region: "Sankhuwasabha", range: "Mahalangur Himal" },
  { rank: 5, name: "Cho Oyu", height: "8,188 m", region: "Solukhumbu", range: "Mahalangur Himal" },
  { rank: 6, name: "Dhaulagiri I", height: "8,167 m", region: "Myagdi", range: "Dhaulagiri Himal" },
  { rank: 7, name: "Manaslu", height: "8,163 m", region: "Gorkha", range: "Manaslu Himal" },
  { rank: 8, name: "Annapurna I", height: "8,091 m", region: "Myagdi / Manang", range: "Annapurna Himal" },
];

export const HIMALAYAN_RANGES = [
  { range: "Mahalangur Himal", peaks: "Everest, Lhotse, Makalu, Cho Oyu, Ama Dablam", highest: "Mount Everest – 8,848.86 m", area: "Solukhumbu / Sankhuwasabha" },
  { range: "Kanchenjunga Himal", peaks: "Kanchenjunga, Jannu (Kumbhakarna)", highest: "Kanchenjunga – 8,586 m", area: "Taplejung (Eastern Nepal)" },
  { range: "Annapurna Himal", peaks: "Annapurna I, II, III, IV, Gangapurna, Machhapuchhre", highest: "Annapurna I – 8,091 m", area: "Kaski, Manang, Mustang" },
  { range: "Dhaulagiri Himal", peaks: "Dhaulagiri I, II, III, IV, V", highest: "Dhaulagiri I – 8,167 m", area: "Myagdi / Mustang" },
  { range: "Manaslu Himal", peaks: "Manaslu, Himalchuli, Ngadi Chuli", highest: "Manaslu – 8,163 m", area: "Gorkha / Manang" },
  { range: "Langtang Himal", peaks: "Langtang Lirung, Dorje Lakpa, Langshisha Ri", highest: "Langtang Lirung – 7,227 m", area: "Rasuwa / Sindhupalchok" },
  { range: "Ganesh Himal", peaks: "Yangra (Ganesh I), Ganesh II, III", highest: "Yangra – 7,422 m", area: "Gorkha / Dhading / Rasuwa" },
  { range: "Rolwaling Himal", peaks: "Gauri Shankar, Melungtse, Dorje Phagmo", highest: "Melungtse – 7,181 m", area: "Dolakha" },
  { range: "Api–Nampa Himal", peaks: "Api, Nampa, Byas Himal", highest: "Api – 7,132 m", area: "Darchula (Far-West Nepal)" },
  { range: "Kanjiroba Himal", peaks: "Kanjiroba North, Kanjiroba South", highest: "Kanjiroba South – 6,883 m", area: "Dolpa" },
  { range: "Jugal Himal", peaks: "Dorje Lakpa, Gyalzen Peak", highest: "Dorje Lakpa – 6,966 m", area: "Sindhupalchok" },
  { range: "Damodar & Mustang Himal", peaks: "Tilicho Peak, Nilgiri North, Bhrikuti", highest: "Nilgiri North – 7,061 m", area: "Mustang / Manang" },
];

export const DEFAULT_FOODS = [
  { name: "Steamed MoMo", nepali: "मःमः", desc: "Handmade steamed dumplings filled with spiced vegetables or chicken, served with spicy tomato sesame chutney.", region: "Kathmandu & Pokhara" },
  { name: "Dal Bhat Tarkari", nepali: "दाल भात", desc: "Steamed rice served with yellow lentil soup, curried vegetables, Gundruk, and spicy golbheda pickle.", region: "All Nepal (National Staple)" },
  { name: "Newari Samay Baji", nepali: "समय् बजि", desc: "Beaten rice with smoked buffalo Choila, black beans, boiled eggs, and fermented Aila.", region: "Patan & Bhaktapur" },
  { name: "Sel Roti & Achar", nepali: "सेल रोटी", desc: "Traditional ring-shaped fried rice-flour bread eaten during Dashain, Tihar, and morning tea.", region: "All Nepal" },
  { name: "Bhaktapur Juju Dhau", nepali: "जुजु धौ", desc: "King of Curds — thick, sweet, rich buffalo-milk yogurt set in clay pots.", region: "Bhaktapur Durbar Square" },
];

export const DEFAULT_FESTIVALS = [
  { title: "Bada Dashain", kind: "National Festival", body: "Nepal's major 15-day celebration of good over evil with Tika blessings, Jamara, and bamboo swings.", city: "All Nepal", date: "Sept – Oct" },
  { title: "Tihar & Deepawali", kind: "Festival of Lights", body: "5-day light festival honoring dogs, crows, cows, Lakshmi, and Bhai Tika sister-brother bonds.", city: "All Nepal", date: "Oct – Nov" },
  { title: "Fagu Purnima (Holi)", kind: "Spring Festival", body: "Vibrant festival of dry gulal colors, water balloons, and music across Durbar Squares.", city: "Kathmandu & Pokhara", date: "March" },
  { title: "Bisket Jatra", kind: "Heritage Festival", body: "Huge chariot pulling festival in Bhaktapur celebrating the Newari New Year.", city: "Bhaktapur", date: "April" },
];

export const PROVINCE_LINKS = [
  { name: "Koshi", count: "826 recorded places", highlight: "Ilam Tea Gardens & Kanyam" },
  { name: "Madhesh", count: "167 recorded places", highlight: "Janakpurdham & Janaki Mandir" },
  { name: "Bagmati", count: "2,624 recorded places", highlight: "Boudhanath Stupa & Kathmandu" },
  { name: "Gandaki", count: "2,621 recorded places", highlight: "Bandipur & Pokhara Lakes" },
  { name: "Lumbini", count: "679 recorded places", highlight: "Lumbini Sacred Garden & Maya Devi" },
  { name: "Karnali", count: "488 recorded places", highlight: "Rara Lake & National Park" },
  { name: "Sudurpashchim", count: "194 recorded places", highlight: "Khaptad National Park & Shuklaphanta" },
];

const MARQUEE_ITEMS = [
  "🏔️ Home to 8 of the world's 14 highest peaks",
  "🛕 UNESCO World Heritage Sites",
  "🐅 Chitwan wildlife and Bengal tigers",
  "🪂 Pokhara paragliding destination",
  "🎉 120+ ethnic groups and cultures",
  "🍚 Dal Bhat Power, 24 Hour",
];

const NationalSymbols = () => {
  const [showFullModal, setShowFullModal] = useState(false);
  const [activeModalTab, setActiveModalTab] = useState("symbols");

  return (
    <section className="rounded-3xl overflow-hidden mb-8 shadow-xl border border-blue-900/40">
      <div
        className="p-6 md:p-8 text-white space-y-6"
        style={{
          backgroundImage:
            "linear-gradient(135deg,#0B3D91,#2b519e,#F59E0B)",
        }}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="px-3 py-1 rounded-full bg-amber-400 text-slate-950 text-xs font-black uppercase tracking-wider shadow">
              Discover Nepal — Beyond Everest
            </span>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white mt-1.5">
              Nepal's National Identity & Cultural Symbols
            </h2>
            <p className="text-white/80 text-xs sm:text-sm mt-0.5">
              Official emblems, natural heritage, sacred animals, and national symbols.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowFullModal(true)}
              className="px-5 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs sm:text-sm shadow-lg transition-all hover:scale-105 flex items-center gap-2 shrink-0"
            >
              <FiBookOpen size={16} /> See More & Explore All 26 Symbols ➔
            </button>

            <Link
              to="/discover-nepal"
              className="px-4 py-2.5 rounded-2xl bg-white/15 hover:bg-white/25 text-white font-bold text-xs sm:text-sm shadow transition-all flex items-center gap-1.5 shrink-0 border border-white/20"
            >
              <FiCompass size={14} /> Discover Page
            </Link>
          </div>
        </div>

        {/* Inline Grid Preview */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {SUMMARY_SYMBOLS.map(({ image, label, fact }, index) => (
            <motion.div
              key={label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04 }}
              className="bg-white/10 backdrop-blur rounded-2xl p-3.5 text-center border border-white/15 hover:bg-white/20 transition-all cursor-pointer"
              onClick={() => setShowFullModal(true)}
            >
              <img
                src={image}
                alt={label}
                className="w-20 h-20 rounded-full object-cover mx-auto mb-2 bg-white shadow-md border-2 border-white/40"
              />
              <h3 className="text-sm font-extrabold text-white">{label}</h3>
              <p className="text-xs text-white/80 mt-0.5 leading-snug">{fact}</p>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="bg-blue-950 py-3 overflow-hidden border-t border-blue-900/60">
        <div className="marquee-track">
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, i) => (
            <span key={i} className="text-amber-300 font-bold px-8 text-xs whitespace-nowrap">
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* FULL COMPREHENSIVE NATIONAL SYMBOLS & MOUNTAIN ATLAS MODAL */}
      <AnimatePresence>
        {showFullModal && (
          <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-3 sm:p-5 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-slate-950 border border-slate-800 rounded-3xl max-w-5xl w-full p-6 sm:p-8 space-y-6 shadow-2xl text-white max-h-[92vh] flex flex-col"
            >
              {/* Modal Header */}
              <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                <div>
                  <span className="px-3.5 py-1 rounded-full bg-amber-400/20 text-amber-300 text-xs font-black uppercase tracking-wider border border-amber-400/30">
                    Nepal National Identity & Country Profile
                  </span>
                  <h3 className="text-2xl sm:text-3xl font-black text-white mt-1.5">
                    Official 26 National Symbols & 8,000m Mountain Atlas
                  </h3>
                  <p className="text-xs text-slate-300 mt-1">
                    Structured country profile with real images, official symbols, 8,000m peaks, cuisine, and 7 provinces.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowFullModal(false)}
                  className="p-2 rounded-full bg-slate-800 text-slate-400 hover:text-white"
                >
                  <FiX size={20} />
                </button>
              </div>

              {/* Modal Tabs */}
              <div className="flex border-b border-slate-800 overflow-x-auto gap-2 pb-2">
                <button
                  type="button"
                  onClick={() => setActiveModalTab("symbols")}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    activeModalTab === "symbols" ? "bg-amber-400 text-slate-950 font-black shadow" : "bg-slate-900 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  🇳🇵 All 26 National Symbols
                </button>
                <button
                  type="button"
                  onClick={() => setActiveModalTab("mountains")}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    activeModalTab === "mountains" ? "bg-amber-400 text-slate-950 font-black shadow" : "bg-slate-900 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  🏔️ 8,000m Mountains & Ranges
                </button>
                <button
                  type="button"
                  onClick={() => setActiveModalTab("culture")}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    activeModalTab === "culture" ? "bg-amber-400 text-slate-950 font-black shadow" : "bg-slate-900 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  🍲 Food & Cultural Festivals
                </button>
                <button
                  type="button"
                  onClick={() => setActiveModalTab("provinces")}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    activeModalTab === "provinces" ? "bg-amber-400 text-slate-950 font-black shadow" : "bg-slate-900 text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  🗺️ 7 Provinces
                </button>
              </div>

              {/* Modal Content Scroll Area */}
              <div className="flex-1 overflow-y-auto pr-1 space-y-6 text-xs">
                
                {/* TAB 1: ALL 26 NATIONAL SYMBOLS */}
                {activeModalTab === "symbols" && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {ALL_26_NATIONAL_SYMBOLS.map((s) => (
                      <div
                        key={s.id}
                        className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2.5 flex flex-col justify-between hover:border-amber-400/50 transition-all shadow-md"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            {s.image ? (
                              <img src={s.image} alt={s.title} className="w-12 h-12 rounded-full object-cover border-2 border-amber-400/60 shadow" />
                            ) : (
                              <span className="text-3xl p-2 rounded-2xl bg-slate-800 border border-slate-700">{s.icon}</span>
                            )}
                            <span className="text-[10px] font-bold text-amber-300 bg-amber-950/80 border border-amber-800/60 px-2 py-0.5 rounded-full">
                              {s.nepali}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] uppercase font-bold text-slate-400 block">{s.category}</span>
                            <h4 className="font-extrabold text-sm text-white">{s.title}</h4>
                          </div>
                          <p className="text-slate-300 leading-relaxed text-[11px]">{s.value}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* TAB 2: 8,000M MOUNTAINS & HIMALAYAN RANGES */}
                {activeModalTab === "mountains" && (
                  <div className="space-y-6">
                    {/* 8,000m Table */}
                    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
                      <div className="flex justify-between items-center">
                        <h4 className="text-base font-black text-amber-300">🏔️ Nepal's 8 Mountains Above 8,000 Meters</h4>
                        <span className="text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded-full font-bold border border-emerald-800">
                          8 of 14 Highest Peaks on Earth
                        </span>
                      </div>
                      <div className="overflow-x-auto rounded-xl border border-slate-800">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-950 text-amber-300 uppercase font-black tracking-wider text-[10px]">
                            <tr>
                              <th className="p-2.5">Rank</th>
                              <th className="p-2.5">Mountain Peak</th>
                              <th className="p-2.5">Height (m)</th>
                              <th className="p-2.5">Himalayan Section</th>
                              <th className="p-2.5">District / Region</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800 bg-slate-900 text-slate-200">
                            {EIGHT_THOUSANDERS.map((m) => (
                              <tr key={m.rank} className="hover:bg-slate-800/80">
                                <td className="p-2.5 font-black text-amber-400">#{m.rank}</td>
                                <td className="p-2.5 font-bold text-white">{m.name}</td>
                                <td className="p-2.5 font-black text-emerald-400 font-mono">{m.height}</td>
                                <td className="p-2.5 text-slate-300">{m.range}</td>
                                <td className="p-2.5 text-slate-400">{m.region}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Major Himalayan Sections */}
                    <div className="space-y-3">
                      <h4 className="text-sm font-black text-white">Major Himalayan Sections of Nepal</h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {HIMALAYAN_RANGES.map((r, i) => (
                          <div key={i} className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
                            <p className="font-black text-amber-300 text-xs">{r.range}</p>
                            <p className="text-emerald-400 font-bold text-[11px]">Highest: {r.highest}</p>
                            <p className="text-slate-300 text-[11px]"><b>Peaks:</b> {r.peaks}</p>
                            <p className="text-slate-400 text-[10px]">📍 {r.area}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 3: FOOD, FESTIVALS & WILDLIFE */}
                {activeModalTab === "culture" && (
                  <div className="space-y-6">
                    {/* Festivals */}
                    <div className="space-y-3">
                      <h4 className="text-sm font-black text-amber-300">🎉 Vibrant Cultural Festivals</h4>
                      <div className="grid sm:grid-cols-2 gap-3">
                        {DEFAULT_FESTIVALS.map((fest, idx) => (
                          <div key={idx} className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-1.5">
                            <div className="flex justify-between items-start">
                              <h5 className="font-black text-white text-sm">{fest.title}</h5>
                              <span className="text-[10px] bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded font-bold">
                                {fest.date}
                              </span>
                            </div>
                            <p className="text-slate-300 text-xs leading-relaxed">{fest.body}</p>
                            <p className="text-[10px] font-bold text-emerald-400 pt-1">📍 {fest.city}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Culinary */}
                    <div className="space-y-3 pt-3 border-t border-slate-800">
                      <h4 className="text-sm font-black text-amber-300">🍲 Authentic Nepali Culinary Heritage</h4>
                      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {DEFAULT_FOODS.map((food, i) => (
                          <div key={i} className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1.5">
                            <span className="text-[10px] font-black uppercase text-amber-400">{food.nepali}</span>
                            <h5 className="font-extrabold text-white text-xs">{food.name}</h5>
                            <p className="text-[10px] text-slate-400">📍 {food.region}</p>
                            <p className="text-slate-300 text-[11px] leading-relaxed">{food.desc}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 4: 7 PROVINCES */}
                {activeModalTab === "provinces" && (
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {PROVINCE_LINKS.map((p) => (
                      <Link
                        key={p.name}
                        to={`/destinations?q=${encodeURIComponent(p.name)}`}
                        className="p-4 rounded-2xl bg-slate-900 border border-slate-800 hover:border-amber-400/50 transition-all space-y-1 block"
                      >
                        <h4 className="font-black text-white text-sm">{p.name} Province</h4>
                        <p className="text-emerald-400 font-bold text-xs">{p.count}</p>
                        <p className="text-slate-400 text-[11px]">Key Highlight: {p.highlight}</p>
                      </Link>
                    ))}
                  </div>
                )}

              </div>

              {/* Modal Footer */}
              <div className="flex justify-between items-center pt-4 border-t border-slate-800">
                <Link
                  to="/discover-nepal"
                  onClick={() => setShowFullModal(false)}
                  className="text-amber-400 hover:underline font-bold text-xs flex items-center gap-1"
                >
                  Open Full Dedicated Discover Nepal Page ➔
                </Link>
                <button
                  type="button"
                  onClick={() => setShowFullModal(false)}
                  className="px-6 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black text-xs shadow"
                >
                  Close Showcase
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </section>
  );
};

export default NationalSymbols;
