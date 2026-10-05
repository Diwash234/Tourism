import fs from 'node:fs';

const urls = JSON.parse(fs.readFileSync('scripts/_endpoints.json', 'utf8'));
const backend = JSON.parse(fs.readFileSync('C:/Users/ADMIN/Desktop/Chatbot/Tourism/_urls.json', 'utf8'));
const patterns = [];
for (const p of [...backend.static, ...backend.dynamic]) {
  // strip the DRF format-suffix and trailing-slash variants Django appends
  // Django interleaves ^...$ anchors at every include() boundary. Strip only
  // those (a ^ right after a separator, a $ right before one), because ^ and $
  // are also meaningful inside the character classes we generate.
  const cleaned = p
    .replace(/(^|\/)\^/g, '$1')
    .replace(/\$(?=\/|$)/g, '')
    .replace(/\\\.\(\?:\[a-z0-9\]\+\)\/\?/g, '')
    .replace(/\\\.\(\?:\*\)\/\?/g, '');
  try {
    // collapse every single-segment wildcard to the literal probe char "W" so
    // frontend `${id}` slots and Django <int:pk> converters line up
    const re = new RegExp(
      '^' + cleaned.replace(/\[\^\/\]\+/g, 'W').replace(/\[\^\/\.\]\+/g, 'W') + '/?$'
    );
    patterns.push(re);
  } catch {}
}
const skip = /^(static|media|admin\/static|favicon)/;

// ignore noise: DRF format suffixes, static/media, schema
function matches(clean) {
  const c = clean.replace(/^\/+/, '');
  if (!c) return true;
  if (skip.test(c)) return true;
  // axios baseURL is /api/v1, so every relative call is mounted there
  return patterns.some((r) => r.test(c)) || patterns.some((r) => r.test('api/v1/' + c));
}

const missing = new Map();
for (const { file, line, verb, url } of urls) {
  // turn `${id}` / `:id` / `?x=${y}` template slots into a single-segment wildcard
  const probe = url
    .split('?')[0]
    .replace(/\$\{[^}]*\}/g, 'W')
    .replace(/:[A-Za-z_]\w*/g, 'W');
  if (matches(probe)) continue;
  const key = url.replace(/\$\{[^}]*\}/g, '{p}');
  if (!missing.has(key)) missing.set(key, []);
  missing.get(key).push(`${verb} ${file}:${line}`);
}
console.log('== FRONTEND CALLS WITH NO RESOLVABLE BACKEND ROUTE ==');
for (const [k, v] of [...missing.entries()].sort()) {
  console.log(`${k}\n    ${v.slice(0, 6).join('\n    ')}${v.length > 6 ? `\n    ... (+${v.length - 6} more)` : ''}`);
}
console.log('\ntotal:', missing.size, 'of', new Set(urls.map((u) => u.url)).size, 'distinct urls');