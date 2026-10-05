import fs from 'node:fs';
import path from 'node:path';
const ROOT = path.resolve('src');
const files=[];
(function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,e.name);if(e.isDirectory())walk(p);else if(/\.jsx?$/.test(e.name))files.push(p);}})(ROOT);
const read=f=>fs.readFileSync(f,'utf8');
const rel=f=>path.relative(ROOT,f).replace(/\\/g,'/');
const out=[];
const verbRe=/\b(api|apiClient|axios|axiosClient|client|adminApi|service)\s*(?:\.\s*(get|post|put|patch|delete)\s*)?\(\s*[`'"]([^`'"]+)[`'"]/g;
for(const f of files){
  const t=read(f);
  let m;
  while((m=verbRe.exec(t))){
    const verb=(m[2]||'get').toUpperCase();
    let url=m[3];
    if(!url.startsWith('/'))continue;
    out.push({file:rel(f),line:t.slice(0,m.index).split('\n').length,verb,url});
  }
}
fs.writeFileSync('scripts/_endpoints.json',JSON.stringify(out,null,2));
console.log('captured',out.length,'calls');
const urls=[...new Set(out.map(o=>o.url.replace(/\$\{[^}]*\}/g,'{p}')))].sort();
console.log(urls.join('\n'));