# Frontend Audit Report — Phase 1 (Inspect Only, No Code Modified)

Tree audited: `arena/01a07999-tourism` @ `d2a71ca`. All numbers below come from scans run against this tree.

## 1. Executive Summary

The frontend is a large (56,962 LOC), functionally rich React SPA with a mature CMS layer: 25/77 pages consume
`usePublicConfig`, all major public content pages are CMS-wired with proven save→publish→public-API chains
(see `docs/CMS_AUDIT.md`). Health is good overall. The material gaps: (1) raw-HTML CMS rendering without a
frontend sanitizer, (2) zero route-level code splitting (one 2.49 MB bundle), (3) 18/38 `<img>` tags missing
`alt`, (4) no per-route SEO metadata, (5) a handful of remaining hardcoded headers (Gallery, Risk).

## 2. Architecture

```
React 18 + React Router (77 routes in src/App.jsx)
  → Layouts (MainLayout/DashboardLayout + Navbar/Footer/MobileBottomNav)
  → 77 pages + 176 components
  → API layer (axios + axiosClient with JWT refresh; tokens in localStorage)
  → Django REST (/api/v1/…) + CMS public config (usePublicConfig) + ML service (:8001)
Vite build · TailwindCSS · framer-motion/gsap · leaflet maps · chart.js · react-hook-form
Testing: Django 259 backend tests + jsdom e2e runner (77 checks). ESLint (react-hooks + purity rules).
```

## 3. Page Inventory

77 route files under `src/pages` (matches `docs/PAGE_INVENTORY.md`). Categories: public content (Home/Landing,
DiscoverNepal, HowItWorks, Gallery, Contact, Privacy, Terms, Budget, Hotels…), tool pages (Navigation HUD,
BudgetEstimator, Nearby, Compare, ExploreMap, Itinerary), account pages (Profile, Settings, History, Favorites,
MySubmissions), admin/staff dashboards, auth pages.

## 4. CMS Audit

- 25/77 pages read `usePublicConfig`; every public content page header + Home's 16 sections + collections are CMS-backed (proven E2E in prior arcs and `docs/CMS_AUDIT.md`).
- Landing's `PROVINCES/FEATURES/FAQ_ITEMS` constants are **fallbacks** — DB values take priority when seeded (correct pattern).
- **Gaps found**: Gallery page header still hardcoded (chips are CMS, header is not — prior claim of "Gallery header done" was wrong); `Risk.jsx` header hardcoded.

## 5. Hardcoded Content Audit (significant items)

| Item | Files | Class |
|---|---|---|
| Gallery + Risk PageHeaders | 2 | CMS (should migrate) |
| Contact numbers (1144, +977…) | 18 files | Mixed: emergency rosters are DB-backed where rendered from API; duplicated literals in static copy = Needs Decision |
| Account-page headers (Profile, Settings, History, Favorites, Itinerary, MySubmissions, RiskAlertDashboard) | 7 | UI chrome — keep code |
| Flow pages (ThankYou, SubmitPlace, SubmitService) | 3 | Needs Decision (low traffic) |
| Tool constants (LANGUAGES, KINDS, severity, filters) | many | App logic — keep code |

## 6. Problem Table

| ID | Area | Problem | Category | Priority | Fix | CMS? |
|---|---|---|---|---|---|---|
| P001 | CMSBlock.jsx (L95,301,395), CMSIntro.jsx (L58) | Raw CMS HTML via `dangerouslySetInnerHTML` with **no DOMPurify** (only SafeHtml.jsx sanitizes); backend `_strip_scripts` is the only defense | Security | **HIGH** | Wrap in existing `SafeHtml`/DOMPurify | NO |
| P002 | App.jsx | No `React.lazy`; single 2.49 MB JS bundle for 77 routes | Performance | **HIGH** | Route-level code splitting | NO |
| P003 | Gallery.jsx L217 | Page header hardcoded | CMS gap | HIGH | Wire `gallery/page-intro` (row exists) | YES |
| P004 | Risk.jsx L113 | Public safety page header hardcoded | CMS gap | HIGH | Wire intro section | YES |
| P005 | 18 of 38 `<img>` in pages | Missing `alt` text | Accessibility | MEDIUM | Add alt (CMS alt where image is CMS) | Partial |
| P006 | All routes except 1 | No per-route `document.title`/meta; only static index.html meta | SEO | MEDIUM | Helmet-lite hook reading ManagedPage meta | YES |
| P007 | SmartImage, ImageGallery, SmartImages, 3 admin pages | 9 eslint errors: synchronous setState in effects (cascading renders) | Code quality | MEDIUM | Restructure effects | NO |
| P008 | 18 files | Contact/phone literals duplicated in static copy | Content | MEDIUM | Centralize via footer/branding CMS | YES |
| P009 | src-wide | 402 eslint warnings (unused vars, deps) | Code quality | LOW | `--fix` + cleanup | NO |
| P010 | ThankYou/SubmitPlace/SubmitService | Hardcoded headers | Needs Decision | LOW | Migrate if editorial desired | YES |

Admin/CMSPanel `dangerouslySetInnerHTML` (×2) is admin-preview-only → lower risk, still wrap (P001 scope).
Breadcrumbs JSON-LD `dangerouslySetInnerHTML` is `JSON.stringify` output → safe.

## 7. UI/UX · 8. Responsive

MobileBottomNav + responsive Tailwind classes throughout; 5 `<table>` usages vs 12 `overflow-x-auto` wrappers
(tables generally handled). **Not verifiable here**: true visual/mobile viewport testing (no browser automation
in sandbox) — flagged as UNCHECKED, not as "passing".

## 9. Accessibility

18 missing-alt images (P005). Focus states: Tailwind defaults present; heading hierarchy not machine-audited.

## 10. Performance

Confirmed: P002 (no splitting, 2.49 MB). Images: remote Unsplash URLs with size params; SmartImage component
exists with lazy patterns. Potential: chart.js/gsap/leaflet could be dynamically imported.

## 11. Code Quality

Largest files: AdminDashboard 2,708 LOC; CMSPanel 1,676; Itinerary 1,528; Translation 1,526; Navigation 1,429.
Candidates for splitting (maintainability, not style). ESLint: 0 errors in CMS-touched files; 9 pre-existing
errors (P007); 402 warnings.

## 12. API/Data

56/77 pages have loading states; 67/77 use try/catch; 29 pages have explicit empty states — remaining ~27
pages should be checked for blank-render on empty data (MEDIUM, per-page review needed).

## 13. SEO — P006. ## 14. Security — P001 + JWT in localStorage (standard for this stack; httpOnly cookies
would be stronger — backend decision). No secrets found in frontend source (scanned).

## 15. CMS Migration Plan

Phase 3 candidates only: P003, P004, P006 (meta from ManagedPage rows), P008 (centralize contact copy),
P010 (if desired). Everything else stays code per the content/logic boundary.

## 16. Recommended Fix Order

Phase 1 Critical: none (no data-loss/security-critical blockers found) · Phase 2 High: P001, P002 ·
Phase 3 CMS: P003, P004, P006, P008 · Phase 4 UX/Responsive: viewport test pass · Phase 5 A11y: P005 ·
Phase 6 Perf: bundle analysis · Phase 7 Quality: P007, P009 · Phase 8: full suite re-run.

## 17. Final Numbers (exact, from scans)

```
Pages audited: 77 · Components: 176 · JSX files: 269 · LOC: 56,962 · Routes: 77
CMS-consuming pages: 25 · CMS E2E-proven elements: see docs/CMS_AUDIT.md (all PASS)
Hardcoded headers remaining: 12 pages (2 = CMS gap P003/P004; 7 = UI chrome; 3 = needs decision)
Critical: 0 · High: 4 (P001–P004) · Medium: 4 (P005–P008) · Low: 2 (P009–P010)
Accessibility: 18 missing-alt images · Performance: 1 confirmed (bundle) + 2 potential
Security: 1 frontend (P001) · ESLint: 9 pre-existing errors, 402 warnings
Backend tests: 259/259 · E2E: 77/77 (last run @ cbb599f..d2a71ca)
Visual/responsive viewport testing: NOT RUN (no browser automation available) — flagged unchecked
```

## Resolution Log (updated as fixes landed)

- P001 FIXED: all raw CMS HTML renders routed through SafeHtml/DOMPurify (CMSBlock ×3, CMSIntro, CMSPanel ×2).
- P002 FIXED: 66 routes lazy-loaded + Suspense; vendor-react/vendor-motion manual chunks; main entry 2.49 MB → 392 KB.
- P003/P004 FIXED: Gallery + Risk headers CMS-wired, E2E proven.
- P005 CLOSED: re-measured with tag-aware scan — 0 real missing-alt images (original count was a single-line-grep artifact).
- P006 FIXED: RouteSEO consumes seo_title/meta_description/og_image from the public config API.
- P007 FIXED: 9 → 0 ESLint errors (2 dead broken files deleted, SmartImage render-adjust, 3 documented debounce disables).
- P008 RESOLVED BY EVIDENCE: brand contact already centralized in branding CMS (footer+Contact read branding.contact_email); contact_email editability E2E-proven; emergency numbers intentionally code-side (safety).
- P009 FIXED: warnings 394 → 55. Remaining: 53 exhaustive-deps (spread across 30+ files, each needs case-by-case behavior judgment — intentionally not batch-edited) + 2 react-hooks/incompatible-library (React Compiler skips Register/ResetPassword; informational, no runtime impact).
- P010 FIXED: ThankYou/SubmitPlace/SubmitService headers CMS-wired, E2E proven.
