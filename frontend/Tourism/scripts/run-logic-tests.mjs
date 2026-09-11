// Frontend regression tests for pure logic modules (audit REQ-038).
// Bundles the real source files with esbuild and asserts behavior — no mocks,
// no re-implementations. Run with: npm test
import { build } from "esbuild"
import { writeFileSync, readFileSync } from "node:fs"
import { pathToFileURL } from "node:url"

const outfile = "node_modules/.logic-tests.mjs"

await build({
  entryPoints: ["scripts/logic-tests-entry.js"],
  bundle: true,
  format: "esm",
  outfile,
  platform: "node",
  logLevel: "error",
  external: ["react", "react-dom"],
  // Vite injects import.meta.env at dev/build time; provide a stub for Node.
  define: { "import.meta.env": "{}" },
})

const mod = await import(pathToFileURL(outfile).href)

let failures = 0
const check = (name, cond) => {
  if (cond) console.log(`  ✓ ${name}`)
  else {
    failures++
    console.error(`  ✗ ${name}`)
  }
}

console.log("NAV_LINKS fallback (utils/constants.js):")
check("contains 'Emergency Services' top label", mod.NAV_LINKS.some((l) => l.label === "Emergency Services"))
check("no legacy 'Safety' top label", !mod.NAV_LINKS.some((l) => l.label === "Safety"))

console.log("adminSectionHref (components/admin/adminNavigation.js):")
const href = mod.adminSectionHref("cms", { resource: "pages" })
check("builds /admin URL with query", href.startsWith("/admin") && href.includes("resource=pages"))

console.log("tailwind.config.js tokens (source scan):")
const tw = readFileSync("tailwind.config.js", "utf8")
  .split("\n")
  .filter((line) => !line.trim().startsWith("//"))
  .join("\n")
check("darkMode class strategy present", /darkMode:\s*'class'/.test(tw))
check("surface tokens present", /surface:\s*{/.test(tw))
check("brand-hover token present", /hover:\s*'#065f46'/.test(tw))
check("no duplicate bare accent string token", !/accent:\s*'#f59e0b'/.test(tw))

console.log("revisionDiff (utils/revisionDiff.js):")
const d1 = mod.diffSnapshots({ title: "B", body: "x", updated_at: "2" }, { title: "A", body: "x", updated_at: "1" })
check("detects the changed field only", d1.length === 1 && d1[0].field === "title")
check("friendly label for known field", d1[0].label === "Title")
const d2 = mod.diffSnapshots({ seo_title: "New" }, { seo_title: null })
check("detects null -> value", d2.length === 1 && d2[0].from === null && d2[0].to === "New")
const d3 = mod.diffSnapshots({ config: { a: 2 } }, { config: { a: 1 } })
check("detects nested object change", d3.length === 1 && d3[0].field === "config")
const d4 = mod.diffSnapshots({ title: "A" }, { title: "A", id: 5, created_at: "x", updated_at: "y", published_at: "z" })
check("ignores bookkeeping keys", d4.length === 0)
const d5 = mod.diffSnapshots({ blocks: [1, 2, 3] }, { blocks: [1] })
check("detects array length change", d5.length === 1 && d5[0].field === "blocks")
check("formats boolean", mod.formatSnapshotValue(true) === "On" && mod.formatSnapshotValue(false) === "Off")
check("formats empty values", mod.formatSnapshotValue("") === "empty" && mod.formatSnapshotValue(null) === "empty")
check("formats arrays as counts", mod.formatSnapshotValue([1, 2, 3]) === "3 items" && mod.formatSnapshotValue([7]) === "1 item")
check("formats objects without JSON jargon", mod.formatSnapshotValue({ a: 1 }) === "Updated")
check("truncates long strings", mod.formatSnapshotValue("x".repeat(80)).length === 61)
check("humanizes unknown snake_case keys", mod.revisionFieldLabel("layout_variant_x") === "Layout variant x")

console.log("translationHelpers (utils/translationHelpers.js):")
const c1 = mod.cleanTranslationContent({ title: "नमस्ते", body: "  ", cta_text: "", route: "/hack", icon: 42 }, "sections")
check("keeps only whitelisted non-empty fields", JSON.stringify(c1) === JSON.stringify({ title: "नमस्ते" }))
const c2 = mod.cleanTranslationContent({ title: "x", meta_description: "y" }, "pages")
check("page fields allowed", Object.keys(c2).length === 2)
const c3 = mod.cleanTranslationContent({ label: "मेनु" }, "navigation")
check("navigation label allowed", c3.label === "मेनु")
check("key format stable", mod.buildTranslationKey("sections", 7, "ne") === "sections:7:ne")
const rows = [
  { target_resource: "sections", object_id: 1, language_code: "ne", content: { title: "शीर्षक" } },
  { target_resource: "sections", object_id: 2, language_code: "ne", content: { title: "   " } },
  { target_resource: "pages", object_id: 3, language_code: "hi", content: { title: "पृष्ठ" } },
]
const keys = mod.translatedKeySet(rows, "ne")
check("counts only rows with real text in the active language", keys.size === 1 && keys.has("sections:1:ne"))
const cov = mod.translationCoverage(
  [ { type: "sections", id: 1, lang: "ne" }, { type: "sections", id: 2, lang: "ne" }, { type: "pages", id: 3, lang: "ne" } ],
  keys
)
check("coverage done/total", cov.done === 1 && cov.total === 3)
check("field whitelist matches backend", JSON.stringify(mod.TRANSLATION_FIELDS.sections.map((f) => f.name)) === JSON.stringify(["title","subtitle","body","cta_text"]))

console.log("navbarFeatures (utils/navbarFeatures.js):")
const f1 = mod.resolveNavbarFeatures(null)
check("missing setting shows every feature", mod.NAVBAR_FEATURES.every(({ key }) => f1[key] === true))
const f2 = mod.resolveNavbarFeatures({ search: false, theme_toggle: false })
check("explicit false hides that feature only", f2.search === false && f2.theme_toggle === false && f2.language_switcher === true && f2.profile === true && f2.notifications === true)
const f3 = mod.resolveNavbarFeatures("garbage")
check("non-object setting falls back to all shown", mod.NAVBAR_FEATURES.every(({ key }) => f3[key] === true))
check("covers the five brief features", mod.NAVBAR_FEATURES.map((f) => f.key).join(",") === "search,language_switcher,profile,notifications,theme_toggle")

console.log("cookieConsent (utils/cookieConsent.js):")
const cc1 = mod.resolveCookieConsent(null)
check("missing setting shows the notice with default message", cc1.enabled === true && cc1.message === mod.DEFAULT_COOKIE_MESSAGE)
const cc2 = mod.resolveCookieConsent({ enabled: false })
check("explicit false hides the notice", cc2.enabled === false)
const cc3 = mod.resolveCookieConsent({ enabled: true, message: "  Custom wording  " })
check("custom message is trimmed", cc3.message === "Custom wording")
const cc4 = mod.resolveCookieConsent({ message: "   " })
check("blank message falls back to default", cc4.message === mod.DEFAULT_COOKIE_MESSAGE)
const fakeStore = { map: {}, getItem(k) { return this.map[k] ?? null }, setItem(k, v) { this.map[k] = String(v) } }
check("fresh browser has not dismissed", mod.isCookieConsentDismissed(fakeStore) === false)
mod.dismissCookieConsent(fakeStore)
check("accepting persists under the storage key", fakeStore.map[mod.COOKIE_CONSENT_KEY] === "accepted" && mod.isCookieConsentDismissed(fakeStore) === true)
const brokenStore = { getItem() { throw new Error("blocked") }, setItem() { throw new Error("blocked") } }
check("private-mode storage never crashes", mod.isCookieConsentDismissed(brokenStore) === false && mod.dismissCookieConsent(brokenStore) === undefined)

console.log("Pagination (components/common/Pagination.jsx source scan):")
const pg = readFileSync("src/components/common/Pagination.jsx", "utf8")
check("has direct jump input", pg.includes('placeholder="Jump to…"'))
check("validates numeric input", pg.includes("/^\\d+$/"))
check("shows Page X of Y", pg.includes("Page {currentPage} of {totalPages}"))

console.log("Dark-mode compatibility layer (index.css source scan):")
const css = readFileSync("src/index.css", "utf8")
const compat = css.slice(css.indexOf("Global dark-mode compatibility layer"))
check("remaps translucent white panels", /\.bg-white\\\/80/.test(compat))
check("remaps hover states off light surfaces", /\.hover\\:bg-gray-50\)?:hover/.test(compat))
check("remaps divide- hairlines", /\.divide-gray-200\)? > :not/.test(compat))
check(
  "every remap is :where()-wrapped so authored dark: variants win",
  compat.split("\n").filter((l) => /^html\.dark \./.test(l)).length === 0,
)

if (failures) {
  console.error(`\n${failures} test(s) FAILED`)
  process.exit(1)
}
console.log("\nAll frontend logic tests passed.")
