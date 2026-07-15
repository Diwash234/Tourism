import { useState } from "react"
import { FiRefreshCw } from "react-icons/fi"
import translationApi from "../api/translationApi"
import useToast from "../hooks/useToast"

const LANGUAGES = ["English", "Nepali", "Hindi", "French", "Spanish", "Chinese"]

const Translation = () => {
  const [sourceText, setSourceText] = useState("")
  const [targetLang, setTargetLang] = useState("Nepali")
  const [result, setResult] = useState("")
  const [loading, setLoading] = useState(false)
  const { showToast } = useToast()

  const handleTranslate = async () => {
    if (!sourceText.trim()) return
    setLoading(true)
    try {
      const { data } = await translationApi.translateText({ text: sourceText, target: targetLang })
      setResult(data.translatedText || "")
    } catch {
      showToast("Translation service unavailable", "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Translate</h1>
      <div className="card-base p-6 space-y-4">
        <textarea
          rows={5}
          className="input-field"
          placeholder="Type text to translate..."
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
        />
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)} className="input-field sm:w-56">
            {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
          <button onClick={handleTranslate} className="btn-primary flex items-center gap-2" disabled={loading}>
            <FiRefreshCw className={loading ? "animate-spin" : ""} />
            {loading ? "Translating..." : "Translate"}
          </button>
        </div>
        {result && (
          <div className="bg-gray-50 rounded-xl p-4 text-sm text-dark border border-gray-100">
            {result}
          </div>
        )}
      </div>
    </div>
  )
}

export default Translation