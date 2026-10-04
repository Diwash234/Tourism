/* Drives the REAL DestinationList + Pagination inside jsdom.
   Usage: node scripts/pagination-behavior-test.cjs  (after esbuild bundle) */
const { JSDOM } = require("jsdom")
const path = require("path")
let failures = 0
const check = (name, ok, detail) => { console.log(`${ok ? "PASS" : "FAIL"}  ${name}${!ok && detail ? "  -> " + detail : ""}`); if (!ok) failures++ }

const dom = new JSDOM("<!doctype html><html><body><div id='root'></div></body></html>", { url: "http://localhost/", pretendToBeVisual: true })
const { window } = dom
// Expose every DOM constructor/global the page and framer-motion touch.
const extra = ["AbortController", "AbortSignal", "window", "document", "navigator", "getComputedStyle", "requestAnimationFrame", "cancelAnimationFrame", "localStorage", "sessionStorage", "location", "history"]
for (const k of [...Object.getOwnPropertyNames(window).filter((n) => /^(HTML|SVG|DOM|Mutation|Resize|Intersection)?[A-Z]\w*(Element|Event|Node|List|Observer|Text|Comment|Document|Fragment|Range|Selection|Collection|Rect|Style|Sheet)$/.test(n) || ["Element", "Node", "Event", "CustomEvent", "FormData", "File", "Blob", "FileReader", "Image", "XMLHttpRequest"].includes(n)), ...extra]) {
  if (k === "navigator" || k === "location" || k === "history") { try { Object.defineProperty(global, k, { value: window[k], configurable: true, writable: true }) } catch { /* ignore */ } continue }
  try { Object.defineProperty(global, k, { value: window[k], configurable: true, writable: true }) } catch { /* node-provided */ }
}
window.matchMedia = window.matchMedia || ((q) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }))
window.scrollTo = () => {}
window.IntersectionObserver = window.IntersectionObserver || class { observe() {} unobserve() {} disconnect() {} }
global.IntersectionObserver = window.IntersectionObserver
global.IS_REACT_ACT_ENVIRONMENT = true

const entry = require(path.resolve(__dirname, "../tests-pagination/bundle.cjs"))
const { act } = require("react")
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const settle = async (ms = 150) => { await act(async () => { await sleep(ms) }) }
const lastPage = () => entry.calls.length ? entry.calls[entry.calls.length - 1].page : null
const $ = (sel) => window.document.querySelector(sel)
const click = async (el) => { await act(async () => { el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true })) }); await settle() }
const typeInto = async (input, value) => {
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set
  await act(async () => { setter.call(input, value); input.dispatchEvent(new window.Event("input", { bubbles: true })) })
}
const submit = async (form) => { await act(async () => { form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true })) }); await settle(250) }
const pageBtn = (n) => [...window.document.querySelectorAll("nav[aria-label='Pagination'] button")].find((b) => b.textContent.trim() === String(n))
const rendered = () => [...window.document.querySelectorAll("a[href*='/destinations/']")].length

;(async () => {
  const root = entry.mount(window.document.getElementById("root"))
  await settle(400)
  check("first load requests page 1 with 12 per page", lastPage() === 1 && entry.calls[0].size === 12, JSON.stringify(entry.calls[0]))
  check("pager shows 'Page 1 of 384'", /Page 1 of 384/.test(window.document.body.textContent), window.document.body.textContent.match(/Page \d+ of \d+/)?.[0])

  // While a page is loading, the pager and current cards must stay mounted.
  entry.setLatency(400)
  const pagerNodeBefore = $("button[aria-label='Next page']")
  const cardsBefore = rendered()
  await act(async () => { pagerNodeBefore.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true })) })
  await act(async () => { await sleep(100) })
  check("pager stays mounted while the next page loads (no reload flash)", window.document.body.contains(pagerNodeBefore) && $("button[aria-label='Next page']") === pagerNodeBefore)
  check("current cards stay visible while loading", rendered() === cardsBefore && cardsBefore >= 12, `before=${cardsBefore} during=${rendered()}`)
  check("busy state is exposed to assistive tech", !!window.document.querySelector("[aria-busy='true']"))
  await act(async () => { await sleep(700) })
  entry.setLatency(0)
  await settle()
  check("page 2 arrives after the delay", lastPage() === 2, `last=${lastPage()}`)
  const callsBefore = entry.calls.length
  await click($("button[aria-label='Next page']"))
  check("Next goes on to page 3", lastPage() === 3, `last=${lastPage()}`)
  check("URL carries page=3", /page=3/.test(entry.getLocation()), entry.getLocation())
  check("Next fetched exactly once (no reload loop)", entry.calls.length - callsBefore === 1, `extra calls=${entry.calls.length - callsBefore}`)

  await click(pageBtn(4) || pageBtn(3) || pageBtn(2))
  const afterWindowClick = lastPage()
  check("clicking a numbered page requests that page", [2, 3, 4].includes(afterWindowClick), `last=${afterWindowClick}`)

  await click($("button[aria-label='Previous page']"))
  check("Previous moves back one page", lastPage() === afterWindowClick - 1, `last=${lastPage()}`)

  const input = $("input[placeholder^='Jump']")
  check("jump box exists", !!input)
  await typeInto(input, "50")
  await submit(input.closest("form"))
  check("jump to 50 loads page 50", lastPage() === 50, `last=${lastPage()}, text=${window.document.body.textContent.match(/Page must[^.]*\./)?.[0] || ""}`)
  check("URL carries page=50", /page=50/.test(entry.getLocation()), entry.getLocation())
  check("page 50 still shows 12 destination cards", rendered() >= 12, `links=${rendered()}`)

  await typeInto($("input[placeholder^='Jump']"), "384")
  await submit($("input[placeholder^='Jump']").closest("form"))
  check("jump to last page (384) loads page 384", lastPage() === 384, `last=${lastPage()}`)
  check("pager shows 'Page 384 of 384'", /Page 384 of 384/.test(window.document.body.textContent))
  check("Next is disabled on the last page", $("button[aria-label='Next page']")?.disabled === true)

  await typeInto($("input[placeholder^='Jump']"), "385")
  await submit($("input[placeholder^='Jump']").closest("form"))
  check("jump beyond the last page shows a clear message and keeps page 384", /between 1 and 384/.test(window.document.body.textContent) && lastPage() === 384, `last=${lastPage()}`)

  root.unmount()
  console.log(failures ? `\n${failures} FAILED` : "\nAll pagination checks passed")
  process.exit(failures ? 1 : 0)
})().catch((e) => { console.error("harness error:", e); process.exit(2) })
