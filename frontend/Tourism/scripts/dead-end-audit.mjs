/**
 * Dead-end audit.
 *
 * Answers three questions that keep regressing in this codebase:
 *
 *   1. Do all nav/in-page links resolve to a real React route?  (dead 404 menus)
 *   2. Do all axios calls resolve to a real Django URL?          (dead buttons)
 *   3. Which modules are never imported by anything?            (dead code)
 *
 * (2) needs the *resolved* Django URLconf, not a grep of urls.py, because
 * DRF routers and @action decorators generate most of the real surface.
 * The dump is produced on demand by Tourism/scripts/dump_urls.py and cached
 * outside the repo so it is never committed.
 *
 * Usage:  node scripts/dead-end-audit.mjs [--verbose] [--no-endpoints]
 * Exit code is always 0; this is a report, not a gate.
 */
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync } from 'node:child_process'

const ROOT = path.resolve('src')            // <repo>/frontend/Tourism/src
const REPO = path.resolve(ROOT, '..', '..', '..') // <repo>
const DUMP_SCRIPT = path.join(REPO, 'Tourism', 'scripts', 'dump_urls.py')
const BACKEND_URLS = path.join(os.tmpdir(), 'tourism-resolved-urls.json')
const verbose = process.argv.includes('--verbose')
const skipEndpoints = process.argv.includes('--no-endpoints')

const read = (f) => fs.readFileSync(f, 'utf8')
const rel = (f) => path.relative(ROOT, f).replace(/\\/g, '/')

// Dead code inside comments and string-only docs is not dead code. Blank out
// comments (preserving line numbers so reported line refs stay correct) before
// scanning for calls and links.
function stripComments(src) {
  let out = ''
  let i = 0
  const n = src.length
  while (i < n) {
    const two = src.slice(i, i + 2)
    if (two === '//') {
      while (i < n && src[i] !== '\n') { out += ' '; i++ }
    } else if (two === '/*') {
      const end = src.indexOf('*/', i + 2)
      const stop = end === -1 ? n : end + 2
      for (; i < stop; i++) out += src[i] === '\n' ? '\n' : ' '
    } else {
      out += src[i]
      i++
    }
  }
  return out
}

const files = []
;(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name)
    if (entry.isDirectory()) walk(p)
    else if (/\.jsx?$/.test(entry.name)) files.push(p)
  }
})(ROOT)

const corpus = files.map((f) => {
  const raw = read(f)
  return { f, raw, t: stripComments(raw) }
})

// ---------------------------------------------------------------- 1. routes
const app = read(path.join(ROOT, 'App.jsx')) // routes live in real code, keep as-is
const declaredRoutes = [...app.matchAll(/path="([^"]+)"/g)].map((m) => m[1]).filter(Boolean)
const normalize = (r) => r.replace(/\/:[^/]+/g, '/:p').replace(/\/+$/, '').replace(/^\*$/, '')
const routeSet = new Set(declaredRoutes.map(normalize))
const dynamicRoutes = declaredRoutes.map(normalize).filter((r) => r.includes(':') || r === '*')

function routeMatches(link) {
  const l = normalize(link.split('?')[0].split('#')[0])
  if (routeSet.has(l)) return true
  return dynamicRoutes.some((r) => {
    const rp = r.split('/').filter(Boolean)
    const lp = l.split('/').filter(Boolean)
    if (rp.length !== lp.length) return false
    return rp.every((seg, i) => seg.startsWith(':') || seg === lp[i])
  })
}

const deadLinks = []
const linkRe = /(?:to|href)\s*=\s*(?:\{\s*)?[`'"]([^`'"]+)[`'"]/g
for (const { f, t } of corpus) {
  if (rel(f) === 'App.jsx') continue
  let m
  while ((m = linkRe.exec(t))) {
    const link = m[1]
    if (!link.startsWith('/')) continue
    if (/^\/(assets|icons|images|pwa|media)\//.test(link)) continue
    // template-built paths can't be resolved statically
    if (link.includes('${')) continue
    if (!routeMatches(link)) {
      deadLinks.push(`${rel(f)} -> ${link}`)
    }
  }
}

// -------------------------------------------------------------- 2. endpoints
function loadResolvedUrls() {
  if (fs.existsSync(DUMP_SCRIPT)) {
    try {
      const out = execFileSync('python', [DUMP_SCRIPT], {
        cwd: path.join(REPO, 'Tourism'),
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
      })
      fs.writeFileSync(BACKEND_URLS, out, 'utf8')
      return JSON.parse(out)
    } catch (err) {
      console.log(`! could not resolve Django URLs (${String(err.stderr || err.message).trim().split('\n')[0]})`)
      return null
    }
  }
  console.log(`! ${DUMP_SCRIPT} not found — cannot check API endpoints`)
  return null
}

let deadEndpoints = []
if (!skipEndpoints) {
  const backend = loadResolvedUrls()
  if (backend) {
  const patterns = []
  for (const p of [...backend.static, ...backend.dynamic]) {
    // Django interleaves ^...$ anchors at each include() boundary; strip only
    // those (^ right after a separator, $ right before one) because ^ and $
    // are meaningful inside the character classes we generate.
    const cleaned = p
      .replace(/(^|\/)\^/g, '$1')
      .replace(/\$(?=\/|$)/g, '')
      .replace(/\\\.\(\?:\[a-z0-9\]\+\)\/\?/g, '')
    try {
      patterns.push(new RegExp('^' + cleaned.replace(/\[\^\/[^]]*\]\+/g, 'W') + '/?$'))
    } catch {
      /* unparseable regex route — skip */
    }
  }
  const skip = /^(static|media|admin\/static|favicon)/
  const matchesBackend = (probe) => {
    const c = probe.replace(/^\/+/, '')
    if (!c || skip.test(c)) return true
    // axios baseURL is /api/v1
    return patterns.some((r) => r.test(c) || r.test('api/v1/' + c))
  }

  const callRe = /\b(api|apiClient|axios|axiosClient|client|adminApi|[a-zA-Z]+Api)\s*(?:\.\s*(get|post|put|patch|delete)\s*)?\(\s*[`'"]([^`'"]+)[`'"]/g
  for (const { f, t } of corpus) {
    let m
    while ((m = callRe.exec(t))) {
      const url = m[3]
      if (!url.startsWith('/')) continue
      const probe = url
        .split('?')[0]
        .replace(/\$\{[^}]*\}/g, 'W')
        .replace(/:[A-Za-z_]\w*/g, 'W')
      if (matchesBackend(probe)) continue
      deadEndpoints.push(`${rel(f)}: ${url.replace(/\$\{[^}]*\}/g, '{p}')}`)
    }
  }
  deadEndpoints = [...new Set(deadEndpoints)].sort()
  }
}

// ---------------------------------------------------------------- 3. orphans
const orphans = []
for (const { f } of corpus) {
  if (!/^(components|pages)\//.test(rel(f))) continue
  const stem = path.basename(f).replace(/\.jsx?$/, '')
  if (stem === 'index') continue
  const importRe = new RegExp(`import\\s*\\(?(?:[^'"]*from\\s*)?['"][^'"]*\\/${stem}(?:\\.jsx?)?['"]`)
  const used = corpus.some(({ f: g, t }) => g !== f && importRe.test(t))
  if (!used) orphans.push(rel(f))
}

// ------------------------------------------------------------------- report
console.log(`scanned ${files.length} modules under src/\n`)
console.log(`DEAD LINKS (no matching route): ${deadLinks.length}`)
deadLinks.forEach((l) => console.log('   ' + l))
console.log(`\nDEAD API CALLS (no resolvable backend route): ${deadEndpoints.length}`)
deadEndpoints.forEach((l) => console.log('   ' + l))
console.log(`\nNEVER-IMPORTED MODULES: ${orphans.length}`)
orphans.forEach((l) => console.log('   ' + l))
if (!verbose && orphans.length > 40) {
  console.log(`\n(${orphans.length - 40} more never-imported modules hidden; pass --verbose to list all)`)
}