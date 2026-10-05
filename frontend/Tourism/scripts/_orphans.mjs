import fs from 'node:fs';
import path from 'node:path';
const ROOT = path.resolve('src');
const files = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (/\.jsx?$/.test(e.name)) files.push(p);
  }
})(ROOT);
const rel = (f) => path.relative(ROOT, f).replace(/\\/g, '/');
const corpus = files.map((f) => ({ f, t: fs.readFileSync(f, 'utf8') }));

// strict: is the module ever imported by path?
const orphans = [];
for (const { f } of corpus) {
  if (!/^(components|pages)\//.test(rel(f))) continue;
  const stem = path.basename(f).replace(/\.jsx?$/, '');
  if (stem === 'index') continue;
  let used = false;
  for (const { f: g, t } of corpus) {
    if (g === f) continue;
    // any import/lazy specifier ending in /<stem> (with or without extension)
    const re = new RegExp(`import\\s*\\(?(?:[^'"]*from\\s*)?['"][^'"]*\\/${stem}(?:\\.jsx?)?['"]`);
    if (re.test(t)) { used = true; break; }
  }
  if (!used) orphans.push(rel(f));
}
console.log('== MODULES NEVER IMPORTED ANYWHERE (' + orphans.length + ') ==');
console.log(orphans.join('\n'));