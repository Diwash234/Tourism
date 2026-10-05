import fs from 'node:fs';

const urls = JSON.parse(fs.readFileSync('scripts/_endpoints.json', 'utf8'));
const py = fs.readFileSync('../../Tourism/tourist/urls.py', 'utf8');

// backend registered prefixes from router.register + path(...)
const prefixes = new Set();
for (const m of py.matchAll(/router\.register\(\s*["']([^"']+)["']/g)) prefixes.add(m[1].replace(/\/+$/, ''));
const paths = [];
for (const m of py.matchAll(/path\(\s*["']([^"']*)["']/g)) paths.push(m[1]);
// also extra url modules
const extraFiles = [
  '../../Tourism/Tourism/urls.py',
];
for (const f of extraFiles) {
  if (!fs.existsSync(f)) continue;
  const t = fs.readFileSync(f, 'utf8');
  for (const m of t.matchAll(/path\(\s*["']([^"']*)["']/g)) paths.push(m[1]);
  for (const m of t.matchAll(/include\(\s*["']([^"']+)["']/g)) paths.push('include:' + m[1]);
}
// viewset @action endpoints
const actions = new Set();
for (const m of py.matchAll(/@action\(\s*[^)]*?url_path\s*=\s*["']([^"']+)["']/gs)) actions.add(m[1]);
for (const m of py.matchAll(/@action\(\s*[^)]*?url_path\s*=\s*["']([^"']+)["']/gs)) actions.add(m[1]);
// simple @action(detail=False) with no url_path -> kebab of method name
for (const m of py.matchAll(/@action\(\s*(detail\s*=\s*(True|False)\s*,\s*)?methods\s*=\s*\[[^\]]*?\]\s*,\s*(url_path\s*=\s*["'][^"']+["']\s*)?\)/g)) {}

// static file names present in url modules we did not read
function hasBackend(u) {
  const clean = u.split('?')[0].replace(/^\/+/, '');
  if (clean.includes('{p}')) {
    const segs = clean.split('/').filter(Boolean);
    // find any backend path/router prefix that matches the non-param segments in order
    return prefixes.has(segs.slice(0, segs.length - 1).join('/')) ||
      paths.some((p) => {
        const ps = p.replace(/[<][^>]*[>]/g, ':x').split('/').filter(Boolean);
        const target = segs.slice(0, -1).filter((s) => !s.startsWith('{'));
        return ps.join('/') === target.join('/');
      });
  }
  const c = clean.replace(/\/+$/, '');
  if (prefixes.has(c)) return true;
  if (paths.some((p) => p.replace(/\/+$/, '') === c)) return true;
  // route under a router prefix: {router}/{action}
  const segs = c.split('/').filter(Boolean);
  for (let i = 0; i < segs.length; i++) {
    const pre = segs.slice(0, i).join('/');
    if (prefixes.has(pre)) {
      const rest = segs.slice(i);
      const last = rest[rest.length - 1];
      if (actions.has(last) || rest.length === 1) return true;
    }
  }
  return false;
}

const missing = new Map();
for (const { file, line, verb, url } of urls) {
  if (hasBackend(url)) continue;
  const key = url.replace(/\$\{[^}]*\}/g, '{p}');
  if (!missing.has(key)) missing.set(key, []);
  missing.get(key).push(`${verb} ${file}:${line}`);
}
console.log('== FRONTEND CALLS WITH NO BACKEND URL ==');
for (const [k, v] of [...missing.entries()].sort()) {
  console.log(`${k}   <- ${v.slice(0, 3).join(' | ')}${v.length > 3 ? ` (+${v.length - 3} more)` : ''}`);
}
console.log('\ntotal missing:', missing.size);