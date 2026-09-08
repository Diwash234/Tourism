// CI helper: summarize the Playwright JSON report from the layout/overlap
// suite, surface it in the job summary, and post/update a single pinned
// comment on the open PR for this branch (GitHub's raw log endpoints are
// frequently unreachable from restricted networks, so the PR comment is
// the reliable channel for these results).
//
// Usage: node scripts/ci-layout-report.mjs
// Env:   LAYOUT_JSON (default test-results.json), GH_TOKEN, GITHUB_SHA
import { readFileSync, existsSync, writeFileSync, appendFileSync } from "node:fs"
import { execFileSync } from "node:child_process"

const jsonPath = process.env.LAYOUT_JSON || "test-results.json"
const marker = "<!-- layout-e2e-report -->"

function sh(args, opts = {}) {
  return execFileSync("gh", args, { encoding: "utf8", ...opts }).trim()
}

if (!existsSync(jsonPath)) {
  console.log("No Playwright JSON report found at", jsonPath)
  writeFileSync(".layout-failed", "no-report")
  process.exit(0)
}

const report = JSON.parse(readFileSync(jsonPath, "utf8"))
const failed = []
let passed = 0
const walk = (suites) => {
  for (const s of suites || []) {
    for (const spec of s.specs || []) {
      if (spec.ok) passed += 1
      else {
        const last = spec.tests?.[0]?.results?.at(-1)
        const err = (last?.error?.message || "unknown error").split("\n")[0].slice(0, 180)
        failed.push(`- \`${spec.title}\` — ${err}`)
      }
    }
    walk(s.suites)
  }
}
walk(report.suites)

const sha = (process.env.GITHUB_SHA || "local").slice(0, 7)
const statusLine = failed.length === 0
  ? `✅ **Layout e2e: ${passed} passed, 0 failed** (${sha})`
  : `❌ **Layout e2e: ${passed} passed, ${failed.length} failed** (${sha})`
const body = [
  marker,
  "### Layout / overlap e2e report",
  statusLine,
  failed.length ? "<details open><summary>Failed tests</summary>\n\n" + failed.join("\n") + "\n</details>" : "",
].filter(Boolean).join("\n\n")

if (failed.length) writeFileSync(".layout-failed", String(failed.length))
if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, "\n" + body + "\n")
console.log(statusLine)
for (const line of failed) console.log(line)

if (!process.env.GH_TOKEN) { console.log("GH_TOKEN not set — skipping PR comment"); process.exit(0) }

let prNumber = ""
try {
  prNumber = sh(["pr", "list", "--state", "open", "--json", "number", "-q", ".[0].number"])
} catch { /* no PR for this branch */ }
if (!prNumber) { console.log("No open PR for this branch — skipping comment"); process.exit(0) }

const repo = sh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
const list = sh(["api", `repos/${repo}/issues/${prNumber}/comments?per_page=100`])
const existing = JSON.parse(list).find((c) => (c.body || "").includes(marker))
if (existing) {
  sh(["api", "-X", "PATCH", `repos/${repo}/issues/comments/${existing.id}`, "-f", `body=${body}`], { stdio: "pipe" })
  console.log(`Updated PR #${prNumber} comment ${existing.id}`)
} else {
  sh(["pr", "comment", prNumber, "--body", body])
  console.log(`Posted PR #${prNumber} comment`)
}
