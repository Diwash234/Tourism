# Change log — Claude's changes on top of `origin/main` (8031c0bf)

Line numbers refer to the NEW file (after the change). Generated from `git diff -U0`.
**Totals:** 23 files, 1417 lines added/changed, 71 original lines removed/replaced.

**Not pushed** (no GitHub credential in my sandbox). Apply with `git am all-fixes.patch` (6 commits),
or copy each file from `changed_files/` to the same path in VS Code.

## Commits

```
ce024d02  fix(nearby): label shared town-centre coordinates as area points
d2abfcfe  fix(images): crash on mismatched photos + stop wrong photos on places
09af22d8  fix(pagination): jump-to-page never accepted a number
4c8f6e8f  feat(i18n,pagination): translate page content on language switch; keep the list mounted while paging
035fd19d  feat(nav): street-level turn-by-turn by default (OSRM), named + located steps
3dc6398f  fix(budget): restore BudgetPredictionView (site did not boot) and give every place a labelled dataset baseline
```

## Files

### `Tourism/Tourism/settings.py`  (modified)
- Why: ROUTING_BASE_URL defaults to OSRM (not under tests) -> street-level routes
- Added/changed lines: 643-651  (9 lines)
- Original lines removed/replaced: 1

### `Tourism/navigation/osrm_provider.py`  (modified)
- Why: OSRM steps carry street `name` and turn `location`
- Added/changed lines: 114, 120-124  (6 lines)
- Original lines removed/replaced: 0

### `Tourism/tourist/serializers.py`  (modified)
- Why: CRASH FIX: known_places used before assignment (500 on destinations whose photo names another place). IMAGE GATE: cover + gallery photo must name THIS place; photos reused by 3+ places rejected; camera-style filenames stay visible
- Added/changed lines: 227-368, 378, 2215-2218, 2249  (148 lines)
- Original lines removed/replaced: 3

### `Tourism/tourist/tests_budget_baseline.py`  (NEW FILE)
- Why: NEW: 4 tests for the budget fallback
- Added: whole file (57 lines)

### `Tourism/tourist/tests_cover_integrity.py`  (NEW FILE)
- Why: NEW: 8 tests for the image gate
- Added: whole file (79 lines)

### `Tourism/tourist/tests_nearby_approximate.py`  (NEW FILE)
- Why: NEW: 3 tests for shared-point distance labels
- Added: whole file (47 lines)

### `Tourism/tourist/tests_turn_by_turn.py`  (NEW FILE)
- Why: NEW: turn-by-turn with a mocked engine + honest fallback
- Added: whole file (96 lines)

### `Tourism/tourist/urls.py`  (modified)
- Why: Route /translate/batch/ (upstream ui-strings routes kept)
- Added/changed lines: 6, 318  (2 lines)
- Original lines removed/replaced: 0

### `Tourism/tourist/views.py`  (modified)
- Why: Nearby results: 3+ rows on one point => is_approximate, label '≈ X km (area point)', precise rows sort first
- Added/changed lines: 2508-2515, 2521-2525  (13 lines)
- Original lines removed/replaced: 1

### `Tourism/tourist/views_compat.py`  (modified)
- Why: /navigation/route prefers the street-level route for car/motorcycle; steps get turn + distance_km (old graph route stays as fallback)
- Added/changed lines: 427-500, 769-771  (77 lines)
- Original lines removed/replaced: 1

### `Tourism/tourist/views_ml.py`  (modified)
- Why: BOOT FIX: restored BudgetPredictionView (upstream 3f10e572 deleted it; urls.py crashed at import) + dataset fallback: own row -> district median -> province median -> fees only (area baselines labelled via baseline_scope)
- Added/changed lines: 439-650, 652-685, 687-732, 735, 738-740, 745, 753  (298 lines)
- Original lines removed/replaced: 41

### `Tourism/translation/tests_batch.py`  (NEW FILE)
- Why: NEW: 5 tests for the batch translator
- Added: whole file (47 lines)

### `Tourism/translation/urls.py`  (modified)
- Why: Route /translate/batch/
- Added/changed lines: 7  (1 lines)
- Original lines removed/replaced: 0

### `Tourism/translation/views.py`  (modified)
- Why: NEW TranslateBatchView + cached_translate
- Added/changed lines: 1-6, 13-89  (83 lines)
- Original lines removed/replaced: 1

### `frontend/Tourism/.gitignore`  (modified)
- Why: Ignore generated test bundles
- Added/changed lines: 22-23  (2 lines)
- Original lines removed/replaced: 0

### `frontend/Tourism/scripts/i18n-behavior-test.cjs`  (NEW FILE)
- Why: NEW: browser-style language-switch test
- Added: whole file (53 lines)

### `frontend/Tourism/scripts/pagination-behavior-test.cjs`  (NEW FILE)
- Why: NEW: browser-style pagination test
- Added: whole file (90 lines)

### `frontend/Tourism/src/components/common/Pagination.jsx`  (modified)
- Why: BUG FIX: jump box regex/pattern had a doubled backslash (matched a literal \d) so no number was accepted; + inline error
- Added/changed lines: 6, 13, 31-33, 35-40, 56  (12 lines)
- Original lines removed/replaced: 3

### `frontend/Tourism/src/i18n/dynamicTranslate.js`  (NEW FILE)
- Why: NEW: batching, debounce, cache, outage back-off
- Added: whole file (125 lines)

### `frontend/Tourism/src/i18n/index.js`  (modified)
- Why: DOM bridge translates page content via the batch endpoint; restores English; survives React updates
- Added/changed lines: 11, 1537-1540, 1542-1588, 1593, 1595, 1597-1600, 1602, 1606-1619, 1632, 1634-1638, 1641  (80 lines)
- Original lines removed/replaced: 18

### `frontend/Tourism/src/pages/destinations/DestinationList.jsx`  (modified)
- Why: Skeleton only on first load; page + pager stay mounted (dimmed, aria-busy) while paging
- Added/changed lines: 487-491, 498  (6 lines)
- Original lines removed/replaced: 2

### `frontend/Tourism/tests-i18n/entry.js`  (NEW FILE)
- Why: NEW: test entry (fake batch API)
- Added: whole file (17 lines)

### `frontend/Tourism/tests-pagination/entry.jsx`  (NEW FILE)
- Why: NEW: test entry (fake 4,603-place API)
- Added: whole file (69 lines)
