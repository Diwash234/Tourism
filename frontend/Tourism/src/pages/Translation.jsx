import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { FiRefreshCw, FiVolume2, FiMic, FiMicOff, FiWifiOff } from "react-icons/fi"

import translationApi from "../api/translationApi"
import useToast from "../hooks/useToast"

const LANGUAGES = [
  // Global languages
  { name: "English", code: "en" },
  { name: "Nepali", code: "ne" },
  { name: "Hindi", code: "hi" },
  { name: "Chinese", code: "zh" },
  { name: "French", code: "fr" },
  { name: "Spanish", code: "es" },
  { name: "German", code: "de" },
  { name: "Arabic", code: "ar" },
  { name: "Japanese", code: "ja" },
  { name: "Korean", code: "ko" },
  { name: "Russian", code: "ru" },
  { name: "Portuguese", code: "pt" },
  { name: "Italian", code: "it" },
  { name: "Thai", code: "th" },
  { name: "Vietnamese", code: "vi" },
  { name: "Indonesian", code: "id" },

  // NEW: Nepal regional languages. Note the backend /translate/ endpoint
  // proxies to a general-purpose translation service — verify these
  // ISO-ish codes are actually supported before shipping; some minority
  // Himalayan languages (Newari, Sherpa) have inconsistent support
  // across translation providers and may silently fall back to English.
  { name: "Newari (Nepal Bhasa)", code: "new" },
  { name: "Sherpa", code: "xsr" },
  { name: "Tharu", code: "thl" },
  { name: "Maithili", code: "mai" },
  { name: "Bhojpuri", code: "bho" },
  { name: "Tamang", code: "tmg" },
  { name: "Gurung", code: "gvr" },
  { name: "Magar", code: "mgp" },
  { name: "Doteli", code: "dty" },
]

// NEW: offline phrase cards — these work with zero network/backend call,
// exactly per the spec ("offline phrase cards"). Nepali translations are
// hardcoded here rather than round-tripped through the translation API
// so they're available even with no connectivity, which is the whole
// point of a travel phrasebook in the mountains.
const COMMON_PHRASES = [
  { en: "Hello", ne: "नमस्ते", pron: "Namaste" },
  { en: "Thank you", ne: "धन्यवाद", pron: "Dhanyabad" },
  { en: "How much does this cost?", ne: "यो कति पर्छ?", pron: "Yo kati parcha?" },
  { en: "Where is the bathroom?", ne: "शौचालय कहाँ छ?", pron: "Shauchalaya kaha chha?" },
  { en: "I need help", ne: "मलाई मद्दत चाहियो", pron: "Malai maddat chahiyo" },
  { en: "Is this water safe to drink?", ne: "यो पानी पिउन मिल्छ?", pron: "Yo pani piuna milcha?" },
  { en: "How far is it?", ne: "यो कति टाढा छ?", pron: "Yo kati tadha chha?" },
  { en: "Call a doctor", ne: "डाक्टर बोलाउनुहोस्", pron: "Doctor bolaunuhos" },
]

const Translation = () => {
  const [sourceText, setSourceText] = useState("")
  const [targetLang, setTargetLang] = useState("ne")
  const [translatedText, setTranslatedText] = useState("")
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [voiceSupported, setVoiceSupported] = useState(true)
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  const recognitionRef = useRef(null)
  const { showToast } = useToast()

  // NEW: voice input via the browser's Web Speech API. No backend
  // involvement — SpeechRecognition runs entirely client-side (though it
  // does need network access itself in Chrome, since recognition is
  // cloud-based there). Safari/Firefox support is inconsistent, hence
  // the feature-detection below rather than assuming it exists.
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setVoiceSupported(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setSourceText((prev) => (prev ? `${prev} ${transcript}` : transcript))
    }
    recognition.onerror = () => {
      showToast("Couldn't hear that — try again", "error")
      setIsListening(false)
    }
    recognition.onend = () => setIsListening(false)

    recognitionRef.current = recognition

    return () => recognition.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const goOnline = () => setIsOffline(false)
    const goOffline = () => setIsOffline(true)
    window.addEventListener("online", goOnline)
    window.addEventListener("offline", goOffline)
    return () => {
      window.removeEventListener("online", goOnline)
      window.removeEventListener("offline", goOffline)
    }
  }, [])

  const toggleListening = () => {
    if (!recognitionRef.current) return
    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      // Speech recognition language should roughly match what the
      // traveler is speaking, not the target language they're
      // translating INTO — default to the browser's language.
      recognitionRef.current.lang = navigator.language || "en-US"
      recognitionRef.current.start()
      setIsListening(true)
    }
  }

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      showToast("Please enter text to translate", "error")
      return
    }
    if (isOffline) {
      showToast("You're offline — live translation needs a connection. Try the phrase cards below instead.", "error")
      return
    }

    try {
      setLoading(true)
      setTranslatedText("")

      const response = await translationApi.translateText({
        text: sourceText,
        target_language: targetLang,
        target_lang: targetLang,
        source_language: "auto",
      })

      const data = response.data
      setTranslatedText(data.translated_text || data.translation || data.result || "")
    } catch (error) {
      console.log("Translation error:", error.response?.data || error.message)
      showToast("Translation failed", "error")
    } finally {
      setLoading(false)
    }
  }

  const speakText = (text, lang = "ne-NP") => {
    if (!window.speechSynthesis || !text) return
    const speech = new SpeechSynthesisUtterance(text)
    speech.lang = lang
    window.speechSynthesis.speak(speech)
  }

  return (
    <div className="container-app py-10">
      <div className="flex items-center justify-between flex-wrap gap-3 mb-2">
        <h1 className="section-title mb-0">🌎 AI Language Translator</h1>
        {isOffline && (
          <span className="flex items-center gap-1.5 text-xs font-semibold text-nepalred-500 bg-nepalred-50 px-3 py-1.5 rounded-full">
            <FiWifiOff size={12} /> Offline — phrase cards still work
          </span>
        )}
      </div>

      <p className="text-gray-500 text-sm mb-8">
        Translate travel information, directions and conversations into different languages.
      </p>

      <div className="grid lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-base p-6 space-y-6 lg:col-span-2"
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">Enter Text</label>
              {voiceSupported ? (
                <button
                  type="button"
                  onClick={toggleListening}
                  title={isListening ? "Stop listening" : "Speak instead of typing"}
                  className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                    isListening
                      ? "bg-nepalred-500 text-white pulse-soft"
                      : "bg-himalaya-50 text-himalaya-600 hover:bg-himalaya-100"
                  }`}
                >
                  {isListening ? <FiMicOff size={13} /> : <FiMic size={13} />}
                  {isListening ? "Listening..." : "Voice Input"}
                </button>
              ) : (
                <span className="text-xs text-gray-400" title="Your browser doesn't support the Web Speech API">
                  Voice input not supported in this browser
                </span>
              )}
            </div>

            <textarea
              rows={6}
              className="input-field w-full"
              placeholder="Type, or tap Voice Input to speak..."
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Translate To</label>
            <select
              className="input-field w-full"
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
            >
              {LANGUAGES.map((language) => (
                <option key={language.code} value={language.code}>
                  {language.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleTranslate}
            disabled={loading}
            className="btn-primary flex items-center justify-center gap-2 w-full"
          >
            <FiRefreshCw className={loading ? "animate-spin" : ""} />
            {loading ? "Translating..." : "Translate"}
          </button>

          {translatedText && (
            <div className="bg-himalaya-50 border border-himalaya-100 rounded-xl p-5">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-semibold">Translation Result</h3>
                <button
                  onClick={() => speakText(translatedText, targetLang)}
                  className="p-2 rounded-full hover:bg-white transition-colors"
                  title="Listen (pronunciation guide)"
                >
                  <FiVolume2 />
                </button>
              </div>
              <p className="text-lg">{translatedText}</p>
            </div>
          )}
        </motion.div>

        {/* NEW: offline common tourist phrases */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card-base p-6 space-y-1 h-fit"
        >
          <h3 className="font-semibold mb-1">Common Tourist Phrases</h3>
          <p className="text-xs text-gray-400 mb-4">Works offline — no translation call needed.</p>

          <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
            {COMMON_PHRASES.map((phrase) => (
              <div key={phrase.en} className="border-b border-gray-100 pb-3 last:border-0">
                <p className="text-sm font-medium text-dark">{phrase.en}</p>
                <div className="flex items-center justify-between mt-1">
                  <div>
                    <p className="text-sm text-himalaya-600">{phrase.ne}</p>
                    <p className="text-xs text-gray-400 italic">{phrase.pron}</p>
                  </div>
                  <button
                    onClick={() => speakText(phrase.ne, "ne-NP")}
                    className="p-1.5 rounded-full hover:bg-gray-100 shrink-0"
                    title="Hear pronunciation"
                  >
                    <FiVolume2 size={14} className="text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default Translation