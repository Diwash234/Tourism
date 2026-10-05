import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve('src');
const files = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (/\.(jsx?|tsx?)$/.test(e.name)) files.push(p);
  }
})(ROOT);

const read = (f) => fs.readFileSync(f, 'utf8');
const rel = (f) => path.relative(ROOT, f).replace(/\\/g, '/');
const corpus = files.map((f) => ({ f, t: read(f) }));

// ---------- 1. Unused component files ----------
const componentFiles = corpus.filter(({ f }) =>
  /(^|\/)components\//.test(rel(f)) || /(^|\/)pages\//.test(rel(f)));
const unusedComponents = [];
for (const { f } of componentFiles) {
  const base = path.basename(f);
  const stem = base.replace(/\.jsx?$/, '');
  if (stem === 'index') continue;
  let used = false;
  for (const { f: g, t } of corpus) {
    if (g === f) continue;
    // direct relative import of this file
    const relFromSrc = path.relative(path.dirname(f), g).replace(/\\/g, '/').replace(/\.jsx?$/, '');
    const variants = new Set([
      './' + relFromSrc, '../' + relFromSrc, relFromSrc,
    ]);
    for (const v of variants) {
      if (new RegExp(`from\\s*['"]\\.?\\.?/?[^'"]*${v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}['"]`).test(t)) { used = true; break; }
    }
    if (used) break;
    // dynamic/lazy import by path
    if (t.includes(stem) && new RegExp(`import\\s*\\([^)]*${stem}`).test(t)) { used = true; break; }
    // referenced in route config by path string
    if (new RegExp(`['"][^'"]*${stem}['"]`).test(t) && /\.(jsx?|tsx?)$/.test(stem) === false) {
      // plain mention - only count if looks like a path
      if (new RegExp(`['"][^'"]*/${stem}['"]`).test(t)) { used = true; break; }
    }
  }
  if (!used) unusedComponents.push(rel(f));
}

// ---------- 2. Unused exported functions in api/ + services/ + utils/ + hooks/ ----------
const libFiles = corpus.filter(({ f }) => /(^|\/)(api|services|utils|hooks)\//.test(rel(f)));
const deadExports = [];
for (const { f, t } of libFiles) {
  const names = new Set();
  const re = /export\s+(?:async\s+)?(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)/g;
  let m;
  while ((m = re.exec(t))) names.add(m[1]);
  const re2 = /export\s*\{([^}]+)\}/g;
  while ((m = re2.exec(t))) {
    for (const part of m[1].split(',')) {
      const n = part.trim().split(/\s+as\s+/).pop().trim();
      if (n && /^[A-Za-z_$][\w$]*$/.test(n)) names.add(n);
    }
  }
  const allText = corpus.map((c) => c.t).join('\n');
  for (const n of names) {
    // count occurrences of the identifier across the whole src tree
    const hits = (allText.match(new RegExp(`\\b${n}\\b`, 'g')) || []).length;
    // 1 hit == only its own definition; 2 == def + one usage (could be the import+def)
    if (hits <= 2) deadExports.push(`${rel(f)} :: ${n} (${hits} refs)`);
  }
}

// ---------- 3. Buttons / anchors with no behaviour ----------
const deadButtons = [];
for (const { f, t } of corpus) {
  const lines = t.split('\n');
  lines.forEach((line, i) => {
    const isBtn = /<button\b/.test(line);
    const isAnchor = /<a\b/.test(line);
    if (!isBtn && !isAnchor) return;
    // gather full tag (may span lines) - simple window join
    const win = lines.slice(i, i + 12).join('\n');
    const end = win.indexOf('>');
    const tag = end === -1 ? win : win.slice(0, end + 1);
    const hasBehaviour =
      /onClick|onSubmit|type=["']submit["']|onChange|onMouse|onKey|href=|to=|onPress/.test(tag);
    if (!hasBehaviour) {
      deadButtons.push(`${rel(f)}:${i + 1}  ${line.trim().slice(0, 140)}`);
    }
  });
}

// ---------- 4. Stub / placeholder implementations ----------
const stubs = [];
const stubRe = /(TODO|FIXME|XXX|HACK)\b|not implemented|NotImplemented|coming soon|Coming soon|stub/i;
for (const { f, t } of corpus) {
  t.split('\n').forEach((line, i) => {
    if (stubRe.test(line) && line.trim().length > 3) stubs.push(`${rel(f)}:${i + 1}  ${line.trim().slice(0, 160)}`);
  });
}

const out = {
  stats: { files: files.length },
  unusedComponents,
  deadExports,
  deadButtons,
  stubs,
};
fs.writeFileSync('scripts/_deadscan.json', JSON.stringify(out, null, 2));
console.log('files scanned:', files.length);
console.log('\n== UNUSED COMPONENT/PAGE FILES (%d) ==', unusedComponents.length);
console.log(unusedComponents.join('\n'));
console.log('\n== LOW-REF EXPORTS (%d) ==', deadExports.length);
console.log(deadExports.join('\n'));
console.log('\n== BUTTONS/A WITHOUT HANDLER (%d) ==', deadButtons.length);
console.log(deadButtons.join('\n'));
console.log('\n== STUB MARKERS (%d) ==', stubs.length);
console.log(stubs.slice(0, 120).join('\n'));