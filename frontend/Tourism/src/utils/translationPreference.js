const STORAGE_KEY = "translation_provider"

export const TRANSLATION_PROVIDERS = [
  { value: "standard", label: "Standard Translation", desc: "Fast, reliable machine translation (Google Translate / deep-translator). Best for simple phrases." },
  { value: "gemini", label: "Gemini AI", desc: "AI-enhanced, context-aware translation using Google's Gemini model. Better for nuanced or longer text." },
  { value: "groq", label: "Groq AI", desc: "AI-enhanced translation running on Groq's fast inference. Similar quality to Gemini, different provider." },
]

export function getTranslationProvider() {
  return localStorage.getItem(STORAGE_KEY) || "standard"
}

export function setTranslationProvider(value) {
  localStorage.setItem(STORAGE_KEY, value)
}