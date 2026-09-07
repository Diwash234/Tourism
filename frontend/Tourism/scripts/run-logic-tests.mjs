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

console.log("Pagination (components/common/Pagination.jsx source scan):")
const pg = readFileSync("src/components/common/Pagination.jsx", "utf8")
check("has direct jump input", pg.includes('placeholder="Jump to…"'))
check("validates numeric input", pg.includes("/^\\d+$/"))
check("shows Page X of Y", pg.includes("Page {currentPage} of {totalPages}"))

if (failures) {
  console.error(`\n${failures} test(s) FAILED`)
  process.exit(1)
}
console.log("\nAll frontend logic tests passed.")
