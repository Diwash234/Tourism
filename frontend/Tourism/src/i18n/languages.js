/**
 * Language definitions for the i18n system.
 * 28 languages with RTL support for Arabic, Urdu, Hebrew, and Persian.
 */

export const DEFAULT_LANGUAGE = "en"
export const STORAGE_KEY = "tourism_lang"

// Languages that use right-to-left text direction
export const RTL_LANGUAGES = ["ar", "ur", "he", "fa", "ps", "sd", "yi"]

// All 28 supported languages with metadata
export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English", native: "English", dir: "ltr" },
  { code: "ne", label: "Nepali", native: "नेपाली", dir: "ltr" },
  { code: "hi", label: "Hindi", native: "हिन्दी", dir: "ltr" },
  { code: "zh", label: "Chinese", native: "中文", dir: "ltr" },
  { code: "es", label: "Spanish", native: "Español", dir: "ltr" },
  { code: "fr", label: "French", native: "Français", dir: "ltr" },
  { code: "de", label: "German", native: "Deutsch", dir: "ltr" },
  { code: "ja", label: "Japanese", native: "日本語", dir: "ltr" },
  { code: "ko", label: "Korean", native: "한국어", dir: "ltr" },
  { code: "ar", label: "Arabic", native: "العربية", dir: "rtl" },
  { code: "pt", label: "Portuguese", native: "Português", dir: "ltr" },
  { code: "ru", label: "Russian", native: "Русский", dir: "ltr" },
  { code: "it", label: "Italian", native: "Italiano", dir: "ltr" },
  { code: "nl", label: "Dutch", native: "Nederlands", dir: "ltr" },
  { code: "tr", label: "Turkish", native: "Türkçe", dir: "ltr" },
  { code: "th", label: "Thai", native: "ไทย", dir: "ltr" },
  { code: "vi", label: "Vietnamese", native: "Tiếng Việt", dir: "ltr" },
  { code: "id", label: "Indonesian", native: "Bahasa Indonesia", dir: "ltr" },
  { code: "ms", label: "Malay", native: "Bahasa Melayu", dir: "ltr" },
  { code: "tl", label: "Filipino", native: "Filipino", dir: "ltr" },
  { code: "bn", label: "Bengali", native: "বাংলা", dir: "ltr" },
  { code: "ta", label: "Tamil", native: "தமிழ்", dir: "ltr" },
  { code: "te", label: "Telugu", native: "తెలుగు", dir: "ltr" },
  { code: "mr", label: "Marathi", native: "मराठी", dir: "ltr" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી", dir: "ltr" },
  { code: "ur", label: "Urdu", native: "اردو", dir: "rtl" },
  { code: "he", label: "Hebrew", native: "עברית", dir: "rtl" },
  { code: "fa", label: "Persian", native: "فارسی", dir: "rtl" },
]
