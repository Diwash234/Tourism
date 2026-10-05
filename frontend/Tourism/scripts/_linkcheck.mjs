import fs from 'node:fs';
import path from 'node:path';
const ROOT = path.resolve('src');
const files = [];
(function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,e.name);if(e.isDirectory())walk(p);else if(/\.(jsx?|tsx?)$/.test(e.name))files.push(p);}})(ROOT);
const read=f=>fs.readFileSync(f,'utf8');
const rel=f=>path.relative(ROOT,f).replace(/\\/g,'/');

// 1. collect declared routes from App.jsx
const app = read(path.join(ROOT,'App.jsx'));
const routes = [...app.matchAll(/path="([^"]*)"/g)].map(m=>m[1]).filter(Boolean);
const norm = (r) => r.replace(/\/:[^/]+/g, '/:p').replace(/\/+$/,'').replace(/^\*$/,'') ;
const routeSet = new Set(routes.map(r=>norm(r)));
const dynamic = routes.filter(r=>r.includes(':')||r==='*').map(norm);

// match a link to a route pattern
function matchRoute(link){
  const l = norm(link.split('?')[0].split('#')[0]);
  if (routeSet.has(l)) return true;
  for (const r of dynamic) {
    const rp = r.split('/').filter(Boolean);
    const lp = l.split('/').filter(Boolean);
    if (rp.length !== lp.length) continue;
    let ok = true;
    for (let i=0;i<rp.length;i++){ if(rp[i].startsWith(':')) continue; if(rp[i]!==lp[i]){ok=false;break;} }
    if (ok) return true;
  }
  return false;
}

const bad = [];
const linkRe = /(?:to|href)\s*=\s*(?:\{\s*)?[`'"]([^`'"]+)[`'"]/g;
for (const f of files) {
  if (rel(f)==='App.jsx') continue;
  const t = read(f);
  let m;
  while ((m = linkRe.exec(t))) {
    const link = m[1];
    if (!link.startsWith('/')) continue;
    if (/^\/(assets|icons|images|pwa|media)\//.test(link)) continue;
    if (!matchRoute(link)) {
      const line = t.slice(0, m.index).split('\n').length;
      bad.push(`${rel(f)}:${line}  -> ${link}`);
    }
  }
}
console.log('== NAV/LINK DEAD ENDS (no matching route) ==');
console.log(bad.join('\n'));
console.log('\ntotal:', bad.length);
fs.writeFileSync('scripts/_linkcheck.json', JSON.stringify([...new Set(bad.map(b=>b.split('-> ')[1].trim()))].sort(),null,2));