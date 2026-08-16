/**
 * Lightweight i18n for the SPA.
 *
 * Why not react-i18next? Adding a dependency for three languages and a few
 * hundred UI strings is overkill. This module provides a tiny reactive
 * store with t() interpolation, language persistence in localStorage AND
 * a cookie (so the Django backend can read it for server-rendered/API
 * translations), and an extensible dictionary. To add a language, append
 * its block to LANGS and register it in ALL_LANGS.
 */
import { useEffect, useState } from "react"

const STORAGE_KEY = "tourism_lang"
const COOKIE_KEY = "django_language"

export const ALL_LANGS = [
  { code: "en", label: "English", native: "English", flag: "🇬🇧", dir: "ltr" },
  { code: "ne", label: "Nepali", native: "नेपाली", flag: "🇳🇵", dir: "ltr" },
  { code: "hi", label: "Hindi", native: "हिन्दी", flag: "🇮🇳", dir: "ltr" },
]

const en = {
  // nav / layout
  "nav.search": "Search destinations, hotels, emergency, budget...",
  "nav.login": "Login",
  "nav.signup": "Sign Up",
  "nav.logout": "Logout",
  "nav.profile": "Profile",
  "nav.menu": "Menu",
  // sidebar groups
  "sidebar.explore": "Explore & Discover",
  "sidebar.planning": "Planning & Safety",
  "sidebar.account": "My Account",
  "sidebar.portals": "Portals & Control",
  "sidebar.destinations": "Destinations",
  "sidebar.gallery": "Visual Photo Gallery",
  "sidebar.compare": "Compare Places",
  "sidebar.discover": "Discover Nepal",
  "sidebar.packages": "Travel Packages",
  "sidebar.submit": "Submit Place",
  "sidebar.explore_map": "Explore by Province",
  "sidebar.recommendations": "AI Recommendations",
  "sidebar.navigation": "Navigation",
  "sidebar.hotels": "Hotels & Lodges",
  "sidebar.budget": "Budget Estimator",
  "sidebar.trip_planner": "Trip Planner",
  "sidebar.expenditure": "Expenditure History",
  "sidebar.itinerary": "Itinerary Planner",
  "sidebar.risk": "Risk Sentinel",
  "sidebar.safety": "Family Live Safety",
  "sidebar.emergency": "Emergency Hub",
  "sidebar.phrasebook": "Nepal Phrasebook",
  "sidebar.translation": "Live Translation",
  "sidebar.chatbot": "Himal AI Assistant",
  "sidebar.dashboard": "My Dashboard",
  "sidebar.favorites": "Saved Favorites",
  "sidebar.bookings": "My Bookings",
  "sidebar.submissions": "My Submissions",
  "sidebar.history": "Visit History",
  "sidebar.admin": "Admin Central",
  "sidebar.staff": "Staff Operations",
  "sidebar.local": "Local Guide Portal",
  "sidebar.settings": "Settings",
  "sidebar.personal_details": "Personal Details",
  // auth
  "auth.traveller_signin": "Traveller Sign In",
  "auth.staff_signin": "Staff Sign In",
  "auth.admin_signin": "Staff Sign In",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.signin": "Sign In",
  "auth.create_account": "Create your account",
  "auth.full_name": "Full name",
  "auth.phone": "Phone (optional, for SMS verification)",
  "auth.confirm_password": "Confirm password",
  "auth.forgot": "Forgot password?",
  "auth.no_account": "New to Nepal Tourism?",
  "auth.has_account": "Already have an account?",
  "auth.staff_notice": "This area is for authorised tourism staff. Accounts are created by an administrator.",
  "auth.admin_notice": "Restricted area. Super-admin accounts are created on the server with `python manage.py createsuperuser`.",
  "auth.staff_login": "Staff login",
  "auth.admin_login": "Admin login",
  "auth.traveller_login": "Traveller login",
  // common
  "common.loading": "Loading...",
  "common.error": "Something went wrong",
  "common.save": "Save",
  "common.cancel": "Cancel",
  "common.close": "Close",
  "common.search": "Search",
  "common.next": "Next",
  "common.previous": "Previous",
  "common.view_all": "View all",
  "common.learn_more": "Learn more",
  "common.explore_now": "Explore Now",
  "common.from": "From",
  "common.per_night": "/night",
  "common.km": "km",
  "common.recommended": "Recommended",
  // landing / home
  "home.hero_title": "Discover the Himalayas, plan smart, travel safe.",
  "home.hero_subtitle": "6,900+ destinations across 7 provinces — real photos, accurate distances, AI budgets and live navigation.",
  "home.hero_cta": "Start exploring",
  "home.featured": "Featured provinces",
  // emergency
  "emergency.title": "Emergency Hub",
  "emergency.hospitals": "Hospitals",
  "emergency.police": "Police",
  "emergency.call": "Call",
  "emergency.directions": "Directions",
  // budget
  "budget.title": "Budget Estimator",
  "budget.total": "Estimated Total Cost",
  "budget.days": "Days",
  "budget.travelers": "Travellers",
  "budget.destination": "Destination",
  "budget.style": "Travel style",
  "budget.estimate": "Estimate Budget",
  "budget.dataset_badge": "Based on real Nepal travel-cost dataset",
  "budget.currency": "Display currency",
  // settings
  "settings.title": "Settings",
  "settings.language": "Language",
  "settings.currency": "Currency",
  "settings.notifications": "Notifications",
  "settings.saved": "Preferences saved!",
  // gallery
  "gallery.title": "Nepal Photo Gallery",
  // compare
  "compare.title": "Compare Destinations",
}

const ne = {
  "nav.search": "गन्तव्य, होटल, आपतकालीन, बजट खोज्नुहोस्...",
  "nav.login": "लगइन",
  "nav.signup": "साइन अप",
  "nav.logout": "लगआउट",
  "nav.profile": "प्रोफाइल",
  "nav.menu": "मेनु",
  "sidebar.explore": "अन्वेषण गर्नुहोस्",
  "sidebar.planning": "योजना र सुरक्षा",
  "sidebar.account": "मेरो खाता",
  "sidebar.portals": "पोर्टल र नियन्त्रण",
  "sidebar.destinations": "गन्तव्यहरू",
  "sidebar.gallery": "तस्बिर ग्यालेरी",
  "sidebar.compare": "स्थान तुलना गर्नुहोस्",
  "sidebar.discover": "नेपाल पत्ता लगाउनुहोस्",
  "sidebar.packages": "यात्रा प्याकेजहरू",
  "sidebar.submit": "स्थान पेश गर्नुहोस्",
  "sidebar.explore_map": "प्रदेश अनुसार अन्वेषण",
  "sidebar.recommendations": "एआई सिफारिसहरू",
  "sidebar.navigation": "नेभिगेसन",
  "sidebar.hotels": "होटल र लज",
  "sidebar.budget": "बजट अनुमान",
  "sidebar.trip_planner": "यात्रा योजनाकार",
  "sidebar.expenditure": "खर्च इतिहास",
  "sidebar.itinerary": "यात्रा कार्यक्रम",
  "sidebar.risk": "जोखिम सेन्टिनेल",
  "sidebar.safety": "पारिवारिक सुरक्षा",
  "sidebar.emergency": "आपतकालीन केन्द्र",
  "sidebar.phrasebook": "नेपाली वाक्यांशपुस्तक",
  "sidebar.translation": "प्रत्यक्ष अनुवाद",
  "sidebar.chatbot": "हिमाल एआई सहायक",
  "sidebar.dashboard": "मेरो ड्यासबोर्ड",
  "sidebar.favorites": "रुचाइएका",
  "sidebar.bookings": "मेरा बुकिङहरू",
  "sidebar.submissions": "मेरा पेस्कीहरू",
  "sidebar.history": "भ्रमण इतिहास",
  "sidebar.admin": "प्रशासन",
  "sidebar.staff": "कर्मचारी",
  "sidebar.local": "स्थानीय गाइड पोर्टल",
  "sidebar.settings": "सेटिङहरू",
  "sidebar.personal_details": "व्यक्तिगत विवरण",
  "auth.traveller_signin": "यात्रु साइन इन",
  "auth.staff_signin": "कर्मचारी साइन इन",
  "auth.admin_signin": "प्रशासक साइन इन",
  "auth.email": "इमेल",
  "auth.password": "पासवर्ड",
  "auth.signin": "साइन इन",
  "auth.create_account": "खाता खोल्नुहोस्",
  "auth.full_name": "पूरा नाम",
  "auth.phone": "फोन (वैकल्पिक)",
  "auth.confirm_password": "पासवर्ड पुष्टि गर्नुहोस्",
  "auth.forgot": "पासवर्ड बिर्सनुभयो?",
  "auth.no_account": "नयाँ हुनुहुन्छ?",
  "auth.has_account": "पहिले नै खाता छ?",
  "auth.staff_notice": "यो क्षेत्र अधिकृत कर्मचारीका लागि मात्र हो।",
  "auth.admin_notice": "प्रतिबन्धित क्षेत्र। सुपर-प्रशासक खाता सर्भरमा बनाइन्छ।",
  "auth.staff_login": "कर्मचारी लगइन",
  "auth.admin_login": "प्रशासक लगइन",
  "auth.traveller_login": "यात्रु लगइन",
  "common.loading": "लोड हुँदैछ...",
  "common.error": "केही गलती भयो",
  "common.save": "सुरक्षित गर्नुहोस्",
  "common.cancel": "रद्द गर्नुहोस्",
  "common.close": "बन्द गर्नुहोस्",
  "common.search": "खोज्नुहोस्",
  "common.next": "अर्को",
  "common.previous": "अघिल्लो",
  "common.view_all": "सबै हेर्नुहोस्",
  "common.learn_more": "थप जान्नुहोस्",
  "common.explore_now": "अहिले अन्वेषण गर्नुहोस्",
  "common.from": "बाट",
  "common.per_night": "/रात",
  "common.km": "किमी",
  "common.recommended": "सिफारिस गरिएको",
  "home.hero_title": "हिमालय पत्ता लगाउनुहोस्, स्मार्ट योजना बनाउनुहोस्, सुरक्षित यात्रा गर्नुहोस्।",
  "home.hero_subtitle": "७ वटै प्रदेशमा ६,९००+ गन्तव्य — वास्तविक तस्बिर, सही दूरी, एआई बजट र प्रत्यक्ष नेभिगेसन।",
  "home.hero_cta": "अन्वेषण सुरु गर्नुहोस्",
  "home.featured": "विशेष प्रदेशहरू",
  "emergency.title": "आपतकालीन केन्द्र",
  "emergency.hospitals": "अस्पताल",
  "emergency.police": "प्रहरी",
  "emergency.call": "कल गर्नुहोस्",
  "emergency.directions": "दिशानिर्देश",
  "budget.title": "बजट अनुमान",
  "budget.total": "अनुमानित कुल लागत",
  "budget.days": "दिन",
  "budget.travelers": "यात्रुहरू",
  "budget.destination": "गन्तव्य",
  "budget.style": "यात्रा शैली",
  "budget.estimate": "बजट अनुमान गर्नुहोस्",
  "budget.dataset_badge": "वास्तविक नेपाल यात्रा लागत डेटामा आधारित",
  "budget.currency": "मुद्रा",
  "settings.title": "सेटिङहरू",
  "settings.language": "भाषा",
  "settings.currency": "मुद्रा",
  "settings.notifications": "सूचनाहरू",
  "settings.saved": "प्राथमिकताहरू सुरक्षित भयो!",
  "gallery.title": "नेपाल तस्बिर ग्यालेरी",
  "compare.title": "गन्तव्य तुलना गर्नुहोस्",
}

const hi = {
  "nav.search": "गंतव्य, होटल, आपातकाल, बजट खोजें...",
  "nav.login": "लॉगिन",
  "nav.signup": "साइन अप",
  "nav.logout": "लॉगआउट",
  "nav.profile": "प्रोफ़ाइल",
  "nav.menu": "मेन्यू",
  "sidebar.explore": "खोज और खोजें",
  "sidebar.planning": "योजना और सुरक्षा",
  "sidebar.account": "मेरा खाता",
  "sidebar.portals": "पोर्टल और नियंत्रण",
  "sidebar.destinations": "गंतव्य",
  "sidebar.gallery": "फोटो गैलरी",
  "sidebar.compare": "स्थान तुलना करें",
  "sidebar.discover": "नेपाल खोजें",
  "sidebar.packages": "यात्रा पैकेज",
  "sidebar.submit": "स्थान जोड़ें",
  "sidebar.explore_map": "प्रांत के अनुसार खोजें",
  "sidebar.recommendations": "एआई सिफारिशें",
  "sidebar.navigation": "नेविगेशन",
  "sidebar.hotels": "होटल और लॉज",
  "sidebar.budget": "बजट अनुमान",
  "sidebar.trip_planner": "यात्रा योजनाकार",
  "sidebar.expenditure": "व्यय इतिहास",
  "sidebar.itinerary": "यात्रा कार्यक्रम",
  "sidebar.risk": "जोखिम प्रहरी",
  "sidebar.safety": "पारिवारिक सुरक्षा",
  "sidebar.emergency": "आपातकालीन केंद्र",
  "sidebar.phrasebook": "नेपाली वाक्यांश पुस्तक",
  "sidebar.translation": "लाइव अनुवाद",
  "sidebar.chatbot": "हिमाल एआई सहायक",
  "sidebar.dashboard": "मेरा डैशबोर्ड",
  "sidebar.favorites": "सहेजे गए",
  "sidebar.bookings": "मेरी बुकिंग",
  "sidebar.submissions": "मेरे सबमिशन",
  "sidebar.history": "यात्रा इतिहास",
  "sidebar.admin": "प्रशासन",
  "sidebar.staff": "स्टाफ़",
  "sidebar.local": "स्थानीय गाइड पोर्टल",
  "sidebar.settings": "सेटिंग्स",
  "sidebar.personal_details": "व्यक्तिगत विवरण",
  "auth.traveller_signin": "यात्री साइन इन",
  "auth.staff_signin": "स्टाफ़ साइन इन",
  "auth.admin_signin": "प्रशासक साइन इन",
  "auth.email": "ईमेल",
  "auth.password": "पासवर्ड",
  "auth.signin": "साइन इन",
  "auth.create_account": "अपना खाता बनाएं",
  "auth.full_name": "पूरा नाम",
  "auth.phone": "फ़ोन (वैकल्पिक)",
  "auth.confirm_password": "पासवर्ड की पुष्टि करें",
  "auth.forgot": "पासवर्ड भूल गए?",
  "auth.no_account": "नए हैं?",
  "auth.has_account": "पहले से खाता है?",
  "auth.staff_notice": "यह क्षेत्र अधिकृत स्टाफ़ के लिए है।",
  "auth.admin_notice": "प्रतिबंधित क्षेत्र। सुपर-प्रशासक खाता सर्वर पर बनाया जाता है।",
  "auth.staff_login": "स्टाफ़ लॉगिन",
  "auth.admin_login": "प्रशासक लॉगिन",
  "auth.traveller_login": "यात्री लॉगिन",
  "common.loading": "लोड हो रहा है...",
  "common.error": "कुछ गलती हुई",
  "common.save": "सहेजें",
  "common.cancel": "रद्द करें",
  "common.close": "बंद करें",
  "common.search": "खोजें",
  "common.next": "अगला",
  "common.previous": "पिछला",
  "common.view_all": "सभी देखें",
  "common.learn_more": "और जानें",
  "common.explore_now": "अभी खोजें",
  "common.from": "से",
  "common.per_night": "/रात",
  "common.km": "किमी",
  "common.recommended": "अनुशंसित",
  "home.hero_title": "हिमालय खोजें, स्मार्ट योजना बनाएं, सुरक्षित यात्रा करें।",
  "home.hero_subtitle": "७ प्रांतों में ६,९००+ गंतव्य — असली तस्वीरें, सटीक दूरी, एआई बजट और लाइव नेविगेशन।",
  "home.hero_cta": "खोज शुरू करें",
  "home.featured": "विशेष प्रांत",
  "emergency.title": "आपातकालीन केंद्र",
  "emergency.hospitals": "अस्पताल",
  "emergency.police": "पुलिस",
  "emergency.call": "कॉल करें",
  "emergency.directions": "दिशा-निर्देश",
  "budget.title": "बजट अनुमान",
  "budget.total": "अनुमानित कुल लागत",
  "budget.days": "दिन",
  "budget.travelers": "यात्री",
  "budget.destination": "गंतव्य",
  "budget.style": "यात्रा शैली",
  "budget.estimate": "बजट अनुमान लगाएं",
  "budget.dataset_badge": "वास्तविक नेपाल यात्रा लागत डेटा पर आधारित",
  "budget.currency": "मुद्रा",
  "settings.title": "सेटिंग्स",
  "settings.language": "भाषा",
  "settings.currency": "मुद्रा",
  "settings.notifications": "सूचनाएं",
  "settings.saved": "प्राथमिकताएं सहेजी गईं!",
  "gallery.title": "नेपाल फोटो गैलरी",
  "compare.title": "गंतव्य तुलना करें",
}

const DICTS = { en, ne, hi }

// --- reactive store -------------------------------------------------------
let currentLang = detectLang()
const listeners = new Set()

function detectLang() {
  if (typeof window === "undefined") return "en"
  const saved = window.localStorage?.getItem(STORAGE_KEY)
  if (saved && DICTS[saved]) return saved
  const nav = (window.navigator?.language || "en").slice(0, 2)
  return DICTS[nav] ? nav : "en"
}

function persistLang(code) {
  try {
    window.localStorage.setItem(STORAGE_KEY, code)
    // Mirror to a cookie the Django backend reads (LANGUAGE_COOKIE_NAME
    // defaults to django_language). Path=/ so it's sent site-wide.
    document.cookie = `${COOKIE_KEY}=${code}; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`
    document.documentElement.lang = code
    const meta = ALL_LANGS.find((l) => l.code === code)
    document.documentElement.dir = meta?.dir || "ltr"
  } catch {
    /* storage/cookies may be unavailable; ignore */
  }
}

export function setLang(code) {
  if (!DICTS[code] || code === currentLang) return
  currentLang = code
  persistLang(code)
  listeners.forEach((fn) => fn(code))
}

export function getLang() {
  return currentLang
}

/** Translate a key with optional {placeholder} interpolation. */
export function t(key, vars) {
  const dict = DICTS[currentLang] || DICTS.en
  let str = dict[key] ?? DICTS.en[key] ?? key
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      str = str.replace(new RegExp(`\\{${k}\\}`, "g"), String(v))
    }
  }
  return str
}

/** React hook: re-renders on language change and exposes t/setLang/lang. */
export function useI18n() {
  const [lang, set] = useState(currentLang)
  useEffect(() => {
    const fn = (c) => set(c)
    listeners.add(fn)
    return () => listeners.delete(fn)
  }, [])
  return { lang, setLang, t, dir: ALL_LANGS.find((l) => l.code === lang)?.dir || "ltr" }
}

// Apply persisted language as early as possible (no-op on server).
if (typeof window !== "undefined") persistLang(currentLang)
