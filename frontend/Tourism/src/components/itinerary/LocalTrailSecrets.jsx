import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiCompass,
  FiCoffee,
  FiAlertTriangle,
  FiShield,
  FiHeart,
  FiCopy,
  FiCheck,
  FiSmile,
  FiHelpCircle,
  FiSun,
  FiMapPin
} from "react-icons/fi"
import useToast from "../../hooks/useToast"

const SECRET_CATEGORIES = [
  { id: "all", label: "All Trail Wisdom", icon: "✨" },
  { id: "customs", label: "Teahouse & Dining", icon: "🍲" },
  { id: "animals", label: "Pack Animals & Trail Safety", icon: "🐂" },
  { id: "sacred", label: "Sacred Chortens & Culture", icon: "📿" },
  { id: "food", label: "Regional Food Gems", icon: "🥟" },
  { id: "phrases", label: "Trail Talk & Phrases", icon: "🗣️" },
]

const LOCAL_SECRETS = [
  {
    id: "dal-bhat-power",
    category: "customs",
    title: "The Golden Teahouse Rule: Order Dinner by 5:30 PM",
    subtitle: "How mountain kitchens actually operate",
    badge: "Teahouse Culture",
    content: "Mountain teahouse kitchens run on central wood or dried-dung stoves. The cooking order is strictly first-come, first-served. When you reach your lodge in the afternoon, immediately write down your dinner order in the Didi’s order notebook before taking your boots off. While ordering dinner, give your breakfast time and order for the next morning so the kitchen can bake bread and boil porridge before your early start.",
    insiderTip: "Dal Bhat (दालभात) comes with unlimited second and third helpings of rice, lentil soup, and seasonal curried vegetables! The local motto 'Dal Bhat Power, 24 Hour' is real—it's the best fuel for high elevation climbs.",
  },
  {
    id: "yak-cliffside",
    category: "animals",
    title: "The Inward Cliffside Rule with Yaks & Mules",
    subtitle: "A life-saving rule of the Himalayan trail",
    badge: "Trail Safety",
    content: "When you hear the brass bells of a yak (dzopkyo) or mule caravan coming around a mountain bend, ALWAYS step onto the inward cliff side (the mountain side), NEVER the valley cliff drop-off side. A heavily loaded animal carrying kerosene jugs or climbing gear can easily swing its pannier and knock a hiker off the trail if you are standing on the exposed edge.",
    insiderTip: "Wait patiently until the entire pack train and the trailing drover pass before stepping back into the center of the trail.",
  },
  {
    id: "mani-stones-clockwise",
    category: "sacred",
    title: "Always Walk Clockwise (Pradakshina) Around Mani Stones",
    subtitle: "Centuries of pilgrim reverence",
    badge: "Spiritual Etiquette",
    content: "In Buddhist regions (Khumbu, Mustang, Manang, Langtang), you will encounter long Mani stone walls carved with 'Om Mani Padme Hum' and whitewashed chortens. Always walk to the left of the wall so that the sacred stones stay on your RIGHT side (clockwise / sunwise direction). Never sit on or climb over Mani stones, and always spin prayer wheels with your right hand clockwise.",
    insiderTip: "If you are presented with a white silk blessing scarf (Khata / खादा) by a lama or host, receive it with both hands bowed slightly.",
  },
  {
    id: "hot-showers-wifi",
    category: "customs",
    title: "Hot Showers, Batteries & WiFi Realities",
    subtitle: "What costs extra above 3,500 meters",
    badge: "Trail Economics",
    content: "Room rates in mountain teahouses are subsidized (often only 500–1,000 NPR) on the condition that you eat dinner and breakfast at the lodge. Heating water and generating electricity requires hauled gas or solar panels, so hot bucket/gas showers (NPR 300–600), device charging (NPR 200–500 per power bank), and internet cards (Everest Link / AirJaldi, ~NPR 600–1,000) cost extra.",
    insiderTip: "Carry a 20,000mAh power bank and sleep with it inside your sleeping bag at night. Sub-zero night temperatures drain cold lithium batteries in hours!",
  },
  {
    id: "water-refills",
    category: "customs",
    title: "No Single-Use Plastic in Khumbu & Boiled Water Stations",
    subtitle: "Eco-friendly hydration in the Himalayas",
    badge: "Eco Travel",
    content: "Single-use disposable plastic mineral water bottles are legally banned in the Everest/Khumbu region to prevent plastic waste from choking alpine glaciers. Instead, carry two 1-liter reusable wide-mouth bottles (Nalgene style). You can purchase safe boiled drinking water at teahouses or use water purification drops (Aquatabs / chlorine dioxide) or a SteriPEN UV purifier.",
    insiderTip: "Filling your Nalgene bottle with hot boiled water before bed gives you an amazing sleeping-bag foot warmer for the freezing night, and perfectly safe drinking water the next morning!",
  },
  {
    id: "regional-food-khumbu",
    category: "food",
    title: "Sherpa Comfort Food: Riki Kur & Syamkpa",
    subtitle: "High-altitude nutrition from the Solukhumbu heartland",
    badge: "Solukhumbu Cuisine",
    content: "Beyond Dal Bhat, the Sherpa highland diet is rich in root potatoes and warming stews. Try 'Riki Kur' (रिकिकुर)—thick, crispy hand-grated potato pancakes served with melted yak butter and spicy dzo-milk cottage cheese dip. On cold stormy evenings, order 'Syamkpa' (Sherpa Stew)—a rich, hearty broth loaded with handmade wheat dumplings, potatoes, dried wild greens, and mountain herbs.",
    insiderTip: "Stop by the German Bakery in Namche Bazaar (3,440m) for warm apple strudel and fresh espresso before heading higher up the valley.",
  },
  {
    id: "regional-food-mustang",
    category: "food",
    title: "Mustang Apples, Marpha Brandy & Seabuckthorn",
    subtitle: "Rain-shadow flavors along the Kali Gandaki",
    badge: "Mustang Delicacy",
    content: "The trans-Himalayan valley of Lower Mustang is world-renowned for its crisp mountain apples. In Marpha village, taste artisanal dried apple slices, fresh spiced apple crumble, and locally distilled Marpha Apple Brandy. Don't miss 'Seabuckthorn Juice' (Gingko / Himalayan Berry)—a bright orange, tart, vitamin-C packed wild berry beverage harvested from thorny riverbed shrubs.",
    insiderTip: "In Jomsom and Kagbeni, ask for 'Kodo ko Dhindo' (organic buckwheat polenta) paired with local mountain goat curry and fermented mustard greens (gundruk).",
  },
]

const TRAIL_PHRASES = [
  {
    english: "Greetings / Hello (with folded hands)",
    nepali: "नमस्ते",
    phonetic: "Namaste",
    context: "Universal greeting for everyone you pass on the trail.",
  },
  {
    english: "Walk slowly / take it easy (altitude wisdom)",
    nepali: "बिस्तारै जानुहोस्",
    phonetic: "Bistārai jānuhos",
    context: "The #1 golden rule of Himalayan trekking.",
  },
  {
    english: "The food is delicious!",
    nepali: "खाना साह्रै मीठो छ!",
    phonetic: "Khānā sāhrai mīṭho chha!",
    context: "Say this to your teahouse Didi or cook—it brings huge smiles.",
  },
  {
    english: "Is this water boiled?",
    nepali: "यो पानी उमालेको हो?",
    phonetic: "Yo pānī umāleko ho?",
    context: "Essential for confirming safe drinking water.",
  },
  {
    english: "I feel dizzy / mountain sickness",
    nepali: "मलाई रिंगटा लाग्यो",
    phonetic: "Malāī ringaṭā lāgyo",
    context: "Crucial phrase to tell your guide or group if AMS symptoms hit.",
  },
  {
    english: "Where is the nearest health post?",
    nepali: "यहाँ नजिकै स्वास्थ्य चौकी कहाँ छ?",
    phonetic: "Yahā̃ najikai swāsthya chaukī kahā̃ chha?",
    context: "Emergency phrase on remote mountain trails.",
  },
  {
    english: "Thank you very much!",
    nepali: "धेरै धेरै धन्यवाद",
    phonetic: "Dherai dherai dhanyabād",
    context: "Polite gratitude for your porter, guide, or tea host.",
  },
  {
    english: "May all beings be peaceful / Tashi Delek (Sherpa/Tibetan)",
    nepali: "ताशी देलेक",
    phonetic: "Tāshī Delek",
    context: "Warm traditional greeting in Buddhist mountain valleys.",
  },
]

export default function LocalTrailSecrets({ currentRegion = "Himalaya" }) {
  const { showToast } = useToast()
  const [activeTab, setActiveTab] = useState("all")
  const [copiedIndex, setCopiedIndex] = useState(null)

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    showToast(`Copied: "${text}"`, "success")
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const displayedSecrets =
    activeTab === "all"
      ? LOCAL_SECRETS
      : LOCAL_SECRETS.filter((s) => s.category === activeTab)

  return (
    <section className="card-base p-5 sm:p-7 bg-gradient-to-b from-amber-50/40 via-white to-slate-50 border border-amber-200/80 rounded-3xl shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-amber-200/60 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-100 text-amber-900 text-sm font-bold">
              🏔️
            </span>
            <span className="text-[11px] font-black uppercase tracking-wider text-amber-800">
              Sherpa & Local Mountain Insights · स्थानीय पदयात्रा सल्लाह
            </span>
          </div>
          <h3 className="text-xl font-black text-slate-900 mt-1">
            Trail Wisdom & Cultural Etiquette
          </h3>
          <p className="text-xs text-slate-600 mt-0.5">
            Real advice from mountain veterans: teahouse customs, pack animal etiquette, and regional food secrets.
          </p>
        </div>

        <div className="flex items-center gap-1.5 self-start md:self-auto bg-white border border-amber-200 px-3 py-1.5 rounded-2xl text-xs font-bold text-amber-950 shadow-2xs">
          <span>🇳🇵 Written by Local Mountain Leaders</span>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
        {SECRET_CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => setActiveTab(cat.id)}
            className={`px-3 py-1.5 rounded-xl font-bold whitespace-nowrap transition flex items-center gap-1.5 ${
              activeTab === cat.id
                ? "bg-amber-900 text-white shadow-xs"
                : "bg-white border border-slate-200 text-slate-700 hover:bg-amber-50"
            }`}
          >
            <span>{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      {activeTab === "phrases" ? (
        /* Trail Phrasebook View */
        <div className="space-y-4">
          <div className="p-3.5 bg-emerald-50 rounded-2xl border border-emerald-200 text-xs text-emerald-900">
            <p className="font-bold">🗣️ Speak Like a Local Trail Friend:</p>
            <p className="mt-0.5 text-[11px] opacity-90">
              Locals and teahouse families appreciate even a single phrase in Nepali. Tap any phrase to copy it to your clipboard.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            {TRAIL_PHRASES.map((phrase, idx) => (
              <div
                key={idx}
                onClick={() => handleCopy(`${phrase.nepali} (${phrase.phonetic}) - ${phrase.english}`, idx)}
                className="p-3.5 bg-white rounded-2xl border border-slate-200 hover:border-emerald-400 hover:shadow-xs transition cursor-pointer flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-base font-black text-slate-900 font-serif">
                      {phrase.nepali}
                    </span>
                    <button
                      type="button"
                      className="text-slate-400 group-hover:text-emerald-700 transition"
                      aria-label="Copy phrase"
                    >
                      {copiedIndex === idx ? <FiCheck className="text-emerald-600" /> : <FiCopy size={13} />}
                    </button>
                  </div>
                  <p className="text-xs font-bold text-emerald-800 font-mono mt-0.5">
                    {phrase.phonetic}
                  </p>
                  <p className="text-xs text-slate-600 font-medium mt-1">
                    "{phrase.english}"
                  </p>
                </div>
                <p className="text-[10px] text-slate-400 mt-2 italic border-t border-slate-100 pt-1.5">
                  💡 {phrase.context}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Secret Cards Grid */
        <div className="grid sm:grid-cols-2 gap-4">
          {displayedSecrets.map((secret) => (
            <div
              key={secret.id}
              className="p-4 bg-white rounded-2xl border border-slate-200 flex flex-col justify-between hover:shadow-sm transition space-y-3"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-md bg-amber-100 text-amber-900">
                    {secret.badge}
                  </span>
                </div>
                <h4 className="text-sm font-black text-slate-900 leading-snug">
                  {secret.title}
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {secret.content}
                </p>
              </div>

              {secret.insiderTip && (
                <div className="p-2.5 bg-amber-50/70 rounded-xl border border-amber-200/80 text-[11px] text-amber-950 flex items-start gap-1.5">
                  <span className="font-bold shrink-0">💡 Tip:</span>
                  <p className="leading-tight">{secret.insiderTip}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
