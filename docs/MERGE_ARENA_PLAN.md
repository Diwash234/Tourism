# Merge plan: `origin/arena/01a0ed99-tourism` → `main`

Status: **deferred** (2026-10-02). All reported product bugs are fixed and pushed;
this merge is branch-parity housekeeping and could not run while a parallel
working session held uncommitted changes in files the merge overwrites.

## Preconditions

The merge refuses to start while any arena-touched file has local changes.
Compute the current blocker set:

```powershell
$dirty  = git status --porcelain | ForEach-Object { $_.Substring(3) }
$arena  = git diff --name-only main...origin/arena/01a0ed99-tourism
$arena | Where-Object { $dirty -contains $_ }   # must print nothing
```

Never stash or discard the other session's files to force the merge.

## Execute

```powershell
git fetch origin
git merge origin/arena/01a0ed99-tourism
```

## Conflict resolution (file by file)

| File | Resolution | Why |
|---|---|---|
| `docker/entrypoint.sh` | **ours** | serve-first boot order (`99bcc74`) is the verified Render fix; arena's side is the pre-fix streamlining |
| `render.yaml` | **ours** | `$PORT` contract + `START_ML_SERVICE=1`; arena's side removes both |
| `frontend/Tourism/src/api/axiosClient.js` | **ours** | `PUBLIC_READ_PREFIXES` (auth-free public GETs) is newer than arena's version; arena also drops `/auth/register/` from `isAuthRoute` |
| `frontend/Tourism/src/hooks/useGeolocation.js` | **ours** | main has the 5-min cache + IP fallback + legacy field contract + memoized `position`; arena's side strips cache/IP (regression for all 15 consumers) |
| `frontend/Tourism/src/pages/destinations/DestinationDetails.jsx` | **ours** | carries the distance-from-you card, origin labels, auto-GPS |
| `Tourism/Tourism/settings.py` | **ours** | SSL-redirect test exemption, middleware stack, WhiteNoise config; re-adopt an arena setting only if `manage.py check` fails without it |
| `Tourism/tourist/serializers.py` | **ours**, graft if needed | arena rewrote ~1.5k lines against an old base; keep main, then graft symbols that `manage.py check` reports missing |
| `Tourism/tourist/views_admin.py` | **ours + graft new views** | arena adds admin endpoints (multi-source image search etc.) that its auto-merged frontend panels call — append only the new view classes if their routes 404/ImportError |
| `Tourism/tourist/tests_regression.py` | combine | keep all main tests, add arena's new test classes |

## Silent (non-conflict) regressions to undo immediately

Arena changed these files and main did not, so git applies them **without
conflict** — but arena's side removes main-era behavior:

1. **`Tourism/Tourism/urls.py`** — arena's version deletes the project-layer
   auth login/logout guard routes, `audit`/`system_health` includes, detailed
   health, dashboard/public stats, search autocomplete/faceted routes and the
   `api/v1/` include. Restore main's file during the merge:
   ```powershell
   git checkout HEAD -- Tourism/Tourism/urls.py
   ```
2. **`Tourism/Dockerfile`** — arena re-adds this file; the root `Dockerfile` is
   canonical (`render.yaml` → `dockerfilePath: ./Dockerfile`). Remove it:
   ```powershell
   git rm -f Tourism/Dockerfile
   ```

## Migrations

Main head: `0094_merge_20260930_1412`, `0095_render_schema_sync`,
`0096_gps_columns_and_hotel_website`, `0097_alter_destinationimage_external_url`.
Arena adds `0094_merge_migration_leaves`, `0095_alter_hotel_website`,
`0096_seed_cms_global_sections_and_content`, `0098_merge_20261002_0233`,
`0099_hotel_coordinate_retrieved_at_and_more`.

Duplicate numbers with distinct filenames coexist, but verify leaf state:

```powershell
venv\Scripts\python.exe manage.py makemigrations --check --dry-run
venv\Scripts\python.exe manage.py check
```

If multiple leaves remain, add `0100_merge_arena_main.py` replacing the two
remaining leaves. Test-DB creation (any test run) exercises `migrate`.

## Gates before pushing

```powershell
# backend
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py test tourist.tests.DistrictItineraryTests tourist.tests.OfflineItineraryAllCitiesTests tourist.tests_regression.ReconcileCatalogueCommandTests tourist.tests_curated_plans -v 1
# frontend
cd frontend\Tourism; npm run build    # must exit 0
```

Then `git push origin main`. If a gate fails on a missing arena symbol, graft
that symbol only (see table) — do not take whole arena files.

## Do NOT merge

- `verified_tourism_data.json` / `downloads/*.sqlite3.gz` churn from the
  `integrate` branch — those commits ship whole-dataset snapshots, not fixes.
  Main already exposes `coordinate_accuracy` (models.py), so `1755150` is
  superseded. `fetch_destination_photos.py` (commit `1f0f0ed`) does not exist
  on main — its fix has no target here.
- Arena's `7a7c2a6`/`f41a191` as standalone cherry-picks: their migrations were
  later rewritten by `de4a4db` on the branch, so picking them alone introduces
  superseded `0094/0095` files.

## Verification already completed (this round)

- Itinerary exclusions (fallback + ML side): 14/14 tests pass.
- CJK-name visibility guard + recommendation/search regressions: 36/36 pass.
- `publicly_visible` guard verified against live DB: `兰巴拉` and
  `더 노스 페이스 인` hidden; `मकालु 马卡鲁峰` (Makalu) kept.
- Frontend build exit 0 after distance/route changes.
- Pushed: `1f0b626` (distances, itinerary purity, recommendation),
  `28fb8c5` (CJK guard).
