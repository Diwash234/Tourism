import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiGlobe, FiVolume2, FiCopy, FiPlus, FiSearch, FiCheck,
  FiBookOpen, FiCompass, FiShield, FiCoffee, FiHeart, FiSmile
} from "react-icons/fi"
import useToast from "../hooks/useToast"

const DIALECTS = [
  { id: "ne", name: "Nepali (नेपाली)", script: "नेपाली", region: "National / Nationwide" },
  { id: "new", name: "Newari (नेपाल भाषा)", script: "नेपाल भाषा", region: "Kathmandu Valley" },
  { id: "sherpa", name: "Sherpa (शेर्पा)", script: "ཤར་པའི་སྐད།", region: "Everest / Solukhumbu" },
  { id: "mai", name: "Maithili (मैथिली)", script: "मैथिली", region: "Janakpur / Mithila" },
  { id: "tamang", name: "Tamang (तामाङ)", script: "तामाङ", region: "Langtang / Central Hills" },
  { id: "gurung", name: "Gurung (तमु क्यी)", script: "तमु", region: "Annapurna / Pokhara" },
]

const INITIAL_PHRASES = [
  {
    category: "Greetings",
    icon: FiSmile,
    english: "Hello / Greetings",
    ne: "नमस्ते (Namaste / Namaskar)",
    new: "ज्वजलपा (Jwajalapa)",
    sherpa: "ताशी देलेक (Tashi Delek)",
    mai: "प्रणाम (Pranam)",
    tamang: "फ्याफुल्ला (Fyafulla)",
    gurung: "फ्याफुल्ला (Phyafulla)",
  },
  {
    category: "Greetings",
    icon: FiHeart,
    english: "Thank you very much",
    ne: "धेरै धेरै धन्यवाद (Dherai Dherai Dhanyabad)",
    new: "सुभाय् (Subhaye)",
    sherpa: "थुजेछे (Thujechhe)",
    mai: "धन्यवाद (Dhanyabad)",
    tamang: "तुजेछे (Tujechhe)",
    gurung: "थुजेछे (Thujechhe)",
  },
  {
    category: "Greetings",
    icon: FiSmile,
    english: "How are you?",
    ne: "तपाईंलाई कस्तो छ? (Tapailai kasto chha?)",
    new: "छिन्त गुली बांला? (Chhinta guli baala?)",
    sherpa: "कन्जो क्युबा नोक? (Khanjo khorba nok?)",
    mai: "अहाँक की हाल अछि? (Ahanke ki haal achhi?)",
    tamang: "खामेङ्बा? (Khamengba?)",
    gurung: "तोबा मु? (Toba mu?)",
  },
  {
    category: "Directions",
    icon: FiCompass,
    english: "Where is the way to the temple/trail?",
    ne: "मन्दिर जाने बाटो कता छ? (Mandir jane bato kata chha?)",
    new: "द्यः छें वनेगु लं गन खः? (Dyo chhen wanegu lam gana kha?)",
    sherpa: "ल्हाखाङ ग्यु लैम खाबा यिन? (Lhakhang gyu lam khaba yin?)",
    mai: "मंदिर जायक रास्ता कतय अछि? (Mandir jayak rasta katay achhi?)",
    tamang: "ग्योइङ ङ्याम्बा ग्याम खाबा मुला? (Gyoing nyamba gyam khaba mula?)",
    gurung: "क्योइँ मोबा ग्याँ खबा मु? (Kyoing moba gyan khaba mu?)",
  },
  {
    category: "Directions",
    icon: FiCompass,
    english: "Turn left / Turn right",
    ne: "देब्रे घुम्नुस् / दाहिने घुम्नुस् (Debre ghumnos / Dahine ghumnos)",
    new: "खव पाखे / जवा पाखे (Khawa pakhe / Jawa pakhe)",
    sherpa: "योङ्बा / याङ्बा (Yongba / Yangba)",
    mai: "बायाँ घुमू / दायाँ घुमू (Baya ghumu / Daya ghumu)",
    tamang: "देब्रे / दाहिने (Debre / Dahine)",
    gurung: "खवे / जवे (Khawe / Jawe)",
  },
  {
    category: "Food",
    icon: FiCoffee,
    english: "The food is delicious!",
    ne: "खाना साह्रै मिठो छ! (Khana sahrai mitho chha!)",
    new: "भ्वँय सा बांला! (Bhway sa baala!)",
    sherpa: "शेज्याक शिम्बू नोक! (Shejyak shimbu nok!)",
    mai: "भोजन बहुत नीक अछि! (Bhojan bahut neek achhi!)",
    tamang: "कबाक ङ्यार्बा मुला! (Khabak nyarba mula!)",
    gurung: "क्योबे स्याबा मु! (Kyobe syaba mu!)",
  },
  {
    category: "Shopping",
    icon: FiBookOpen,
    english: "How much does this cost?",
    ne: "यसको कति पर्छ? (Yesko kati parchha?)",
    new: "थुकिया ग्वःधँ तु? (Thukiya gwo-dho tu?)",
    sherpa: "दिरी गोङ्बा खाचुक यिन? (Diri gongba khachuk yin?)",
    mai: "एकर कतेक दाम अछि? (Ekar katek daam achhi?)",
    tamang: "चुगी खादे च्योङ्ला? (Chugi khade cyongla?)",
    gurung: "चुई कदे पराला? (Chui kade parala?)",
  },
  {
    category: "Emergency",
    icon: FiShield,
    english: "Please help me! Where is the hospital?",
    ne: "कृपया मलाई सहयोग गर्नुस्! अस्पताल कहाँ छ? (Kripaya malai sahyog garnus! Aspatal kaha chha?)",
    new: "मदति यानादिसं! अस्पताः गन दु? (Madati yaanadisu! Aspataa gana du?)",
    sherpa: "ङाला रोम्ब्याक नाङ! मेन्खाङ खाबा यिन? (Ngala rombyak nang! Menkhang khaba yin?)",
    mai: "कृपा कए हमर मदद करू! अस्पताल कतय अछि? (Kripa kae hamar madad karu! Aspatal katay achhi?)",
    tamang: "ङादा रोम्बा लान्जी! मेन्दोङ खाबा मुला? (Ngada romba lanji! Mendong khaba mula?)",
    gurung: "ङालाई मदद लाउ! अस्पताला खबा मु? (Ngalai madad lau! Aspatala khaba mu?)",
  },
]

const CATEGORIES = ["All", "Greetings", "Directions", "Food", "Shopping", "Emergency"]

const Language = () => {
  const { showToast } = useToast()
  const [selectedDialect, setSelectedDialect] = useState("ne")
  const [activeCategory, setActiveCategory] = useState("All")
  const [searchQuery, setSearchQuery] = useState("")
  const [phrases, setPhrases] = useState(INITIAL_PHRASES)

  const [showAddModal, setShowAddModal] = useState(false)
  const [newPhrase, setNewPhrase] = useState({
    category: "Greetings",
    english: "",
    ne: "",
    new: "",
    sherpa: "",
    mai: "",
  })

  const speakText = (text) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text.split("(")[0])
      utterance.rate = 0.85
      utterance.pitch = 1.0
      window.speechSynthesis.speak(utterance)
      showToast("Playing pronunciation 🔊", "info")
    } else {
      showToast("Speech audio not supported on this browser", "info")
    }
  }

  const copyPhrase = (text) => {
    navigator.clipboard.writeText(text)
    showToast("Copied phrase to clipboard! 📋", "success")
  }

  const handleAddPhrase = (e) => {
    e.preventDefault()
    if (!newPhrase.english || !newPhrase.ne) {
      return showToast("English and Nepali translations are required", "error")
    }

    const item = {
      category: newPhrase.category,
      icon: FiSmile,
      english: newPhrase.english,
      ne: newPhrase.ne,
      new: newPhrase.new || newPhrase.ne,
      sherpa: newPhrase.sherpa || newPhrase.ne,
      mai: newPhrase.mai || newPhrase.ne,
      tamang: newPhrase.ne,
      gurung: newPhrase.ne,
    }

    setPhrases([item, ...phrases])
    showToast("New phrase added to your Nepal Phrasebook! 🎉", "success")
    setShowAddModal(false)
    setNewPhrase({ category: "Greetings", english: "", ne: "", new: "", sherpa: "", mai: "" })
  }

  const filteredPhrases = phrases.filter((p) => {
    const matchesCat = activeCategory === "All" || p.category === activeCategory
    const q = searchQuery.toLowerCase()
    const matchesQuery =
      p.english.toLowerCase().includes(q) ||
      p.ne?.toLowerCase().includes(q) ||
      p.new?.toLowerCase().includes(q) ||
      p.sherpa?.toLowerCase().includes(q) ||
      p.mai?.toLowerCase().includes(q)
    return matchesCat && matchesQuery
  })

  return (
    <div className="container-app py-8 space-y-8 animate-fadeIn">
      {/* Header banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-[#1D5146] text-xs font-bold uppercase tracking-wider">
            Multi-Dialect Cultural Phrasebook
          </span>
          <h1 className="text-3xl font-extrabold text-gray-900 mt-2 flex items-center gap-2">
            <FiGlobe className="text-[#102A2E]" /> Languages of Nepal & Local Dialects
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Learn authentic local phrases in Nepali, Newari, Sherpa, Maithili, Tamang, and Gurung with instant pronunciation audio.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold text-sm flex items-center gap-2 shadow-lg shadow-amber-400/20 transition-all shrink-0"
        >
          <FiPlus size={16} /> Add New Word / Phrase
        </button>
      </div>

      {/* Dialect Selector Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {DIALECTS.map((d) => (
          <button
            key={d.id}
            onClick={() => setSelectedDialect(d.id)}
            className={`p-3.5 rounded-2xl border text-left transition-all ${
              selectedDialect === d.id
                ? "bg-[#1D5146] text-white border-purple-800 shadow-lg shadow-[#102A2E]/20 scale-105"
                : "bg-white border-gray-200 hover:border-[#2E6B5A] text-gray-800"
            }`}
          >
            <p className="font-bold text-xs">{d.name}</p>
            <p className={`text-[10px] mt-1 ${selectedDialect === d.id ? "text-amber-300" : "text-gray-400"}`}>
              {d.region}
            </p>
          </button>
        ))}
      </div>

      {/* Category filters & Search bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex overflow-x-auto gap-2 w-full sm:w-auto pb-1 no-scrollbar">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                activeCategory === cat
                  ? "bg-[#102A2E] text-white shadow-md"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search words or phrases..."
            className="input-field pl-10 text-xs py-2"
          />
        </div>
      </div>

      {/* Phrase Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredPhrases.map((phrase, idx) => {
          const currentTranslation = phrase[selectedDialect] || phrase.ne
          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.04 }}
              className="card-base p-5 shadow-lg border border-[#E5E0D5] rounded-2xl flex flex-col justify-between hover:shadow-xl transition-shadow bg-gradient-to-br from-white to-purple-50/30"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-[#1D5146]">
                    {phrase.category}
                  </span>
                  <span className="text-[10px] font-semibold text-gray-400 uppercase">
                    {DIALECTS.find((d) => d.id === selectedDialect)?.name.split(" ")[0]}
                  </span>
                </div>

                <h3 className="text-sm font-semibold text-gray-500 mb-2">
                  {phrase.english}
                </h3>

                <p className="text-lg font-bold text-purple-950 leading-relaxed">
                  {currentTranslation}
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-[#E5E0D5] mt-4">
                <button
                  onClick={() => speakText(currentTranslation)}
                  className="p-2 rounded-xl bg-[#F7F8F5] hover:bg-emerald-100 text-[#102A2E] transition-colors"
                  title="Listen Pronunciation"
                >
                  <FiVolume2 size={16} />
                </button>
                <button
                  onClick={() => copyPhrase(currentTranslation)}
                  className="p-2 rounded-xl bg-[#F7F8F5] hover:bg-emerald-100 text-[#102A2E] transition-colors"
                  title="Copy Phrase"
                >
                  <FiCopy size={16} />
                </button>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* MODAL: ADD CUSTOM PHRASE */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-5 border border-[#E5E0D5]"
            >
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="text-lg font-bold text-gray-900">Add New Word / Cultural Phrase</h3>
                <button onClick={() => setShowAddModal(false)} className="text-gray-400 hover:text-gray-600">
                  ✕
                </button>
              </div>

              <form onSubmit={handleAddPhrase} className="space-y-4 text-xs">
                <div>
                  <label className="font-semibold text-gray-700">Category</label>
                  <select
                    className="input-field mt-1 text-sm"
                    value={newPhrase.category}
                    onChange={(e) => setNewPhrase({ ...newPhrase, category: e.target.value })}
                  >
                    {CATEGORIES.filter(c => c !== "All").map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-gray-700">English Meaning *</label>
                  <input
                    required
                    placeholder="e.g. Can you guide me to the sunrise viewpoint?"
                    className="input-field mt-1 text-sm"
                    value={newPhrase.english}
                    onChange={(e) => setNewPhrase({ ...newPhrase, english: e.target.value })}
                  />
                </div>

                <div>
                  <label className="font-semibold text-gray-700">Nepali Translation *</label>
                  <input
                    required
                    placeholder="e.g. के मलाई सुर्योदय हेर्ने ठाउँसम्म डोहोर्याउन सक्नुहुन्छ?"
                    className="input-field mt-1 text-sm"
                    value={newPhrase.ne}
                    onChange={(e) => setNewPhrase({ ...newPhrase, ne: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-gray-700">Newari (Optional)</label>
                    <input
                      placeholder="Newari phrase..."
                      className="input-field mt-1 text-sm"
                      value={newPhrase.new}
                      onChange={(e) => setNewPhrase({ ...newPhrase, new: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-gray-700">Sherpa (Optional)</label>
                    <input
                      placeholder="Sherpa phrase..."
                      className="input-field mt-1 text-sm"
                      value={newPhrase.sherpa}
                      onChange={(e) => setNewPhrase({ ...newPhrase, sherpa: e.target.value })}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary px-5 py-2 text-xs font-bold bg-[#102A2E] hover:bg-[#1D5146] text-white rounded-xl shadow-lg shadow-[#102A2E]/20"
                  >
                    Save to Phrasebook
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default Language
