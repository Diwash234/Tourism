import fs from 'node:fs';
import path from 'node:path';
const ROOT = path.resolve('src');

const targets = [
  'pages/Adminagencies.jsx', 'pages/Analytics.jsx', 'pages/BookingManagement.jsx',
  'pages/Feedback.jsx', 'pages/GuideDirectory.jsx', 'pages/HelpSupport.jsx',
  'pages/ImageGallery.jsx', 'pages/ItineraryBuilder.jsx', 'pages/ItineraryPlanner.jsx',
  'pages/JobBoard.jsx', 'pages/Marketplace.jsx', 'pages/Payment.jsx',
  'pages/Risk.jsx', 'pages/SafetyCenter.jsx', 'pages/SearchResults.jsx',
  'pages/SmartImages.jsx', 'pages/TripPlanner.jsx', 'pages/Districts.jsx',
  'pages/destinations/DestinationGallery.jsx',
  'pages/admin/DestinationMediaManager.jsx', 'pages/admin/PlaceApprovals.jsx',
  'pages/admin/UserManagement.jsx',
];

for (const t of targets) {
  const f = path.join(ROOT, t);
  if (!fs.existsSync(f)) { console.log(`### ${t}  -- MISSING`); continue; }
  const src = fs.readFileSync(f, 'utf8');
  const lines = src.split('\n');
  const imports = [...src.matchAll(/^import\s+(?:([\w*\s{},]+?)\s+from\s+)?["']([^"']+)["']/gm)]
    .map((m) => `${(m[1] || '').trim() || '(side-effect)'} <- ${m[2]}`);
  const exports = [...src.matchAll(/export\s+(default\s+)?(function|const|class)\s+([\w$]+)/g)]
    .map((m) => `${m[2]} ${m[3]}${m[1] ? ' [default]' : ''}`);
  // local (non npm, non relative) imports that may not resolve
  const localImports = [...src.matchAll(/from\s+["'](\.[^"']+)["']/g)].map((m) => m[1]);
  const broken = localImports.filter((rel) => {
    const base = path.resolve(path.dirname(f), rel);
    const cands = [base, base + '.jsx', base + '.js', path.join(base, 'index.jsx'), path.join(base, 'index.js')];
    return !cands.some((c) => fs.existsSync(c));
  });
  const endpoints = [...new Set([...src.matchAll(/[`'"]((?:GET|POST)?\s*)?(\/(?:admin|api|auth|destinations|reviews|marketplace|hotels|bookings|payments?|tours?|trips?|risk|users?|staff|guides?|jobs?|packages?|upload|images?|alerts?|blog|news|events?|reports?|analytics|notifications?|favorites?|booking)[^`'"]*)[`'"]/g)].map((m) => m[2]))];
  // buttons with no handler
  let dead = 0;
  lines.forEach((l, i) => {
    if (!/<button\b/.test(l)) return;
    const win = lines.slice(i, i + 10).join('\n');
    const end = win.indexOf('>');
    const tag = end === -1 ? win : win.slice(0, end);
    if (!/onClick|onSubmit|type=["']submit["']|onChange|onMouse/.test(tag)) dead++;
  });
  console.log(`### ${t}  (${lines.length} lines)`);
  console.log(`    exports: ${exports.join(', ') || 'NONE'}`);
  if (broken.length) console.log(`    !! UNRESOLVED IMPORTS: ${broken.join(', ')}`);
  if (dead) console.log(`    ! buttons with no handler: ${dead}`);
  console.log(`    endpoints: ${endpoints.slice(0, 14).join(' ')}`);
  console.log(`    imports: ${imports.slice(0, 12).join(' | ')}`);
  console.log('');
}