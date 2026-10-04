const { JSDOM } = require("jsdom")
const path = require("path")
let failures = 0
const check = (n, ok, d) => { console.log(`${ok ? "PASS" : "FAIL"}  ${n}${!ok && d ? "  -> " + d : ""}`); if (!ok) failures++ }
const dom = new JSDOM("<!doctype html><html><body><main id='app'></main></body></html>", { url: "http://localhost/", pretendToBeVisual: true })
const { window } = dom
for (const k of ["AbortController", "AbortSignal", "window", "document", "navigator", "localStorage", "sessionStorage", "Node", "NodeFilter", "MutationObserver", "Element", "HTMLElement", "Event", "location", "history", "getComputedStyle", "requestAnimationFrame"]) {
  try { Object.defineProperty(global, k, { value: window[k], configurable: true, writable: true }) } catch { /* ignore */ }
}
const entry = require(path.resolve(__dirname, "../tests-i18n/bundle.cjs"))
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const app = window.document.getElementById("app")
const longBanner = "Explore nearby destinations and verified local services. ".repeat(9)
app.innerHTML = `<h1>Welcome to Pashupatinath Temple</h1><p>Open daily from sunrise to sunset.</p><p id="long-banner">${longBanner}</p><select><option>Choose a destination</option></select><img alt="View of the Himalayas"><span>4,603</span><code>npm run build</code><div data-no-translate>Do Not Touch</div><input placeholder="Search for a quiet monastery">`

;(async () => {
  entry.setLang("ne"); await sleep(600)
  const h1 = app.querySelector("h1").textContent, p = app.querySelector("p").textContent
  check("heading (not in the dictionary) is translated", h1 === "NE[Welcome to Pashupatinath Temple]", h1)
  check("paragraph is translated", p === "NE[Open daily from sunrise to sunset.]", p)
  check("banner text up to the API limit is translated", app.querySelector("#long-banner").textContent === `NE[${longBanner}]`)
  check("select option labels are translated", app.querySelector("option").textContent === "NE[Choose a destination]")
  check("image alternative text is translated", app.querySelector("img").getAttribute("alt") === "NE[View of the Himalayas]")
  check("pure number is left alone", app.querySelector("span").textContent === "4,603")
  check("code is left alone", app.querySelector("code").textContent === "npm run build")
  check("data-no-translate is respected", app.querySelector("[data-no-translate]").textContent === "Do Not Touch")
  check("placeholder is translated", app.querySelector("input").getAttribute("placeholder") === "NE[Search for a quiet monastery]", app.querySelector("input").getAttribute("placeholder"))
  check("all strings went in ONE batch request", entry.requests.length === 1 && entry.requests[0].texts.length >= 3, JSON.stringify(entry.requests.map((r) => r.texts.length)))

  // content added later (route change / pagination) gets translated too
  const added = window.document.createElement("p"); added.textContent = "Page two result: Rara Lake"; app.appendChild(added)
  await sleep(600)
  check("content added after the switch is translated", added.textContent === "NE[Page two result: Rara Lake]", added.textContent)

  // React-style in-place text change
  const textNode = added.firstChild; textNode.nodeValue = "Page three result: Phewa Lake"; await sleep(600)
  check("in-place text update is translated", added.textContent === "NE[Page three result: Phewa Lake]", added.textContent)

  // cache: switching away and back does not re-request
  const before = entry.requests.length
  entry.setLang("en"); await sleep(200)
  check("switching back to English restores the original text", h1 !== app.querySelector("h1").textContent && app.querySelector("h1").textContent === "Welcome to Pashupatinath Temple", app.querySelector("h1").textContent)
  check("placeholder restored", app.querySelector("input").getAttribute("placeholder") === "Search for a quiet monastery")
  entry.setLang("ne"); await sleep(500)
  check("switching back to Nepali reuses the cache (no new requests)", entry.requests.length === before, `new=${entry.requests.length - before}`)
  check("…and shows the translation again", app.querySelector("h1").textContent === "NE[Welcome to Pashupatinath Temple]")

  // outage: page keeps English, no crash, no request storm
  entry.resetForTests(); entry.setLang("en"); await sleep(100)
  window.sessionStorage.clear(); entry.setFailing(true)
  const n0 = entry.requests.length
  entry.setLang("ne"); await sleep(700)
  check("provider outage leaves English text in place", app.querySelector("h1").textContent === "Welcome to Pashupatinath Temple", app.querySelector("h1").textContent)
  check("outage does not trigger a request storm", entry.requests.length - n0 <= 2, `requests=${entry.requests.length - n0}`)
  console.log(failures ? `\n${failures} FAILED` : "\nAll language checks passed")
  process.exit(failures ? 1 : 0)
})().catch((e) => { console.error("harness error:", e); process.exit(2) })
