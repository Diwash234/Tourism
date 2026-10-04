// Page-content translation. The dictionary bridge in i18n/index.js can only
// translate strings that exactly match an English dictionary entry, so on
// every page except the navbar/sidebar (whose labels ARE in the dictionary)
// destination names, descriptions, headings and buttons stayed English. This
// module sends the remaining visible strings to POST /translate/batch/ in small
// debounced batches, caches the answers (memory + sessionStorage), and tells the
// caller when a string has been translated so it can update its text node.
import axiosClient from "../api/axiosClient"

const MAX_BATCH = 40
const MAX_CHARS = 600
const DEBOUNCE_MS = 180
const RETRY_AFTER_MS = 30000
const STORE_PREFIX = "tx_cache_v1:"
const STORE_LIMIT = 1500

const memory = new Map() // `${lang}\u0000${text}` -> translation
const failedUntil = new Map()
const waiting = new Map() // key -> { lang, text, callbacks:Set }
let timer = null
let inFlight = 0
let storeTimer = null
const loadedLangs = new Set()

const keyOf = (lang, text) => `${lang}\u0000${text}`

function loadStore(lang) {
  if (loadedLangs.has(lang)) return
  loadedLangs.add(lang)
  try {
    const raw = window.sessionStorage.getItem(STORE_PREFIX + lang)
    if (!raw) return
    const obj = JSON.parse(raw)
    Object.entries(obj).forEach(([text, translated]) => memory.set(keyOf(lang, text), translated))
  } catch {
    /* storage unavailable or corrupt: start empty */
  }
}

function saveStoreSoon(lang) {
  clearTimeout(storeTimer)
  storeTimer = setTimeout(() => {
    try {
      const out = {}
      const prefix = `${lang}\u0000`
      let n = 0
      for (const [k, v] of memory) {
        if (!k.startsWith(prefix)) continue
        out[k.slice(prefix.length)] = v
        if (++n >= STORE_LIMIT) break
      }
      window.sessionStorage.setItem(STORE_PREFIX + lang, JSON.stringify(out))
    } catch {
      /* quota or privacy mode: the in-memory cache still works */
    }
  }, 500)
}

/** Should this visible string be sent for translation at all? */
export function isTranslatable(text) {
  if (!text || text.length < 2 || text.length > MAX_CHARS) return false
  if (!/[A-Za-z]{2}/.test(text)) return false // numbers, symbols, single letters
  if (/^(https?:\/\/|www\.)/i.test(text) || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) return false
  const letters = text.replace(/[^\p{L}]/gu, "")
  if (!letters) return false
  const nonLatin = letters.replace(/[A-Za-z]/g, "").length
  return nonLatin / letters.length < 0.3 // already (mostly) in another script
}

export function lookup(lang, text) {
  loadStore(lang)
  return memory.get(keyOf(lang, text)) ?? null
}

async function flush() {
  timer = null
  if (inFlight >= 2) { timer = setTimeout(flush, DEBOUNCE_MS); return }
  const entries = [...waiting.entries()].slice(0, MAX_BATCH)
  if (!entries.length) return
  entries.forEach(([k]) => waiting.delete(k))
  const lang = entries[0][1].lang
  const group = entries.filter(([, v]) => v.lang === lang)
  entries.filter(([, v]) => v.lang !== lang).forEach(([k, v]) => waiting.set(k, v))
  inFlight += 1
  try {
    const { data } = await axiosClient.post("/translate/batch/", {
      texts: group.map(([, v]) => v.text),
      target_language: lang,
      source_language: "en",
    })
    const out = Array.isArray(data?.translations) ? data.translations : []
    group.forEach(([k, v], i) => {
      const translated = out[i]
      if (typeof translated === "string" && translated.trim() && translated.trim() !== v.text.trim()) {
        memory.set(k, translated)
        v.callbacks.forEach((cb) => { try { cb(translated) } catch { /* node gone */ } })
      } else {
        failedUntil.set(k, Date.now() + RETRY_AFTER_MS) // untranslatable (a name) or provider down
      }
    })
    saveStoreSoon(lang)
  } catch {
    group.forEach(([k]) => failedUntil.set(k, Date.now() + RETRY_AFTER_MS))
  } finally {
    inFlight -= 1
    if (waiting.size) { clearTimeout(timer); timer = setTimeout(flush, DEBOUNCE_MS) }
  }
}

/** Ask for a translation; `onDone(translated)` is called when it arrives. */
export function request(lang, text, onDone) {
  if (lang === "en" || !isTranslatable(text)) return
  const key = keyOf(lang, text)
  if (memory.has(key)) return
  if ((failedUntil.get(key) || 0) > Date.now()) return
  const slot = waiting.get(key) || { lang, text, callbacks: new Set() }
  slot.callbacks.add(onDone)
  waiting.set(key, slot)
  if (!timer) timer = setTimeout(flush, DEBOUNCE_MS)
}

export function resetForTests() {
  memory.clear(); failedUntil.clear(); waiting.clear(); loadedLangs.clear()
  clearTimeout(timer); timer = null; inFlight = 0
}
