import { useState } from "react"
import { FiRefreshCw, FiGlobe, FiCopy } from "react-icons/fi"
import { motion } from "framer-motion"
import translationApi from "../api/translationApi"
import useToast from "../hooks/useToast"
import { NEPAL_LANGUAGES, INTERNATIONAL_LANGUAGES } from "../utils/constants"

const QUICK_PHRASES = [
  "Where is the nearest hospital?",
  "How much does this cost?",
  "Can you help me, please?",
  "Where is the bus station?",
  "Is this water safe to drink?",
  "I am lost, please help.",
]

const Translation = () => {
  const [sourceText, setSourceText] = useState("")
  const [targetLang, setTargetLang] = useState(NEPAL_LANGUAGES[0])
  const [result, setResult] = useState("")
  const [loading, setLoading] = useState(false)
  const { showToast } = useToast()

  const handleTranslate = async (text = sourceText) => {
    if (!text.trim()) return
    setSourceText(text)
    setLoading(true)
    try {
      const { data } = await translationApi.translateText({
        text,
        target: targetLang.code,
      })
      setResult(data.translatedText || "")
    } catch {
      showToast("Translation service unavailable. Please try again shortly.", "error")
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (!result) return
    navigator.clipboard?.writeText(result)
    showToast("Copied to clipboard", "success")
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold flex items-center gap-2 mb-1">
        <FiGlobe className="text-primary-500" /> Translate
      </h1>
      <p className="text-gray-500 text-sm mb-6">
        Communicate with locals in Nepal's regional languages, or translate into major
        international languages for international visitors.
      </p>

      <div className="card-base p-6 space-y-5">
        <textarea
          rows={4}
          className="input-field"
          placeholder="Type text to translate..."
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
        />

        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">Quick phrases for travelers</p>
          <div className="flex flex-wrap gap-2">
            {QUICK_PHRASES.map((phrase) => (
              <button
                key={phrase}
                onClick={() => handleTranslate(phrase)}
                className="text-xs border border-gray-200 rounded-full px-3 py-1.5 hover:bg-gray-50 hover:border-primary-300 transition"
              >
                {phrase}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">Nepali regional languages</p>
          <div className="flex flex-wrap gap-2">
            {NEPAL_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setTargetLang(lang)}
                className={`text-sm rounded-xl px-3 py-2 border transition ${
                  targetLang.code === lang.code
                    ? "bg-primary-500 text-white border-primary-500"
                    : "border-gray-200 hover:border-primary-300 text-gray-700"
                }`}
              >
                {lang.label} <span className="opacity-70">· {lang.native}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">International languages</p>
          <div className="flex flex-wrap gap-2">
            {INTERNATIONAL_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setTargetLang(lang)}
                className={`text-sm rounded-xl px-3 py-2 border transition ${
                  targetLang.code === lang.code
                    ? "bg-secondary-500 text-white border-secondary-500"
                    : "border-gray-200 hover:border-secondary-500 text-gray-700"
                }`}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            Translating into <span className="font-semibold text-dark">{targetLang.label}</span>
          </p>
          <button onClick={() => handleTranslate()} className="btn-primary flex items-center gap-2" disabled={loading}>
            <FiRefreshCw className={loading ? "animate-spin" : ""} />
            {loading ? "Translating..." : "Translate"}
          </button>
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-50 rounded-xl p-4 text-sm text-dark border border-gray-100 flex items-start justify-between gap-3"
          >
            <span>{result}</span>
            <button onClick={handleCopy} className="text-gray-400 hover:text-primary-500 shrink-0">
              <FiCopy />
            </button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default Translation