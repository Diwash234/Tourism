import { useState } from "react"
import { FiVolume2, FiCopy, FiGlobe } from "react-icons/fi"
import useToast from "../../hooks/useToast"

const PHRASES = [
  { en: "Hello / Welcome", ne: "नमस्ते (Namaste)", new: "ज्वजलपा (Jwajalapa)", sherpa: "ताशी देलेक (Tashi Delek)" },
  { en: "Thank you very much", ne: "धेरै धेरै धन्यवाद (Dhanyabad)", new: "सुभाय् (Subhaye)", sherpa: "थुजेछे (Thujechhe)" },
  { en: "How are you?", ne: "तपाईंलाई कस्तो छ? (Kasto chha?)", new: "छिन्त गुली बांला?", sherpa: "कन्जो क्युबा नोक?" },
  { en: "The food is delicious", ne: "खाना मिठो छ (Mitho chha)", new: "भ्वँय सा बांला", sherpa: "शेज्याक शिम्बू नोक" },
  { en: "Please help me", ne: "मलाई सहयोग गर्नुस् (Sahayog garnus)", new: "मदति यानादिसं", sherpa: "ङाला रोम्ब्याक नाङ" },
]

export default function Phrasebook({ dialect = "ne" }) {
  const { showToast } = useToast()

  const speak = (txt) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(txt.split("(")[0])
      window.speechSynthesis.speak(u)
      showToast("Playing pronunciation 🔊", "info")
    }
  }

  return (
    <div className="space-y-3">
      {PHRASES.map((p, i) => (
        <div key={i} className="card-base p-4 rounded-2xl border border-purple-100 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs text-gray-500">{p.en}</p>
            <p className="text-base font-bold text-purple-950 mt-0.5">{p[dialect] || p.ne}</p>
          </div>
          <div className="flex gap-1.5">
            <button onClick={() => speak(p[dialect] || p.ne)} className="p-2 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700">
              <FiVolume2 size={16} />
            </button>
            <button onClick={() => { navigator.clipboard.writeText(p[dialect] || p.ne); showToast("Copied! 📋", "success"); }} className="p-2 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700">
              <FiCopy size={16} />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
