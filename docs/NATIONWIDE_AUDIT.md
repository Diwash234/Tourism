# Post-V3 Nationwide Verification Report

Verified on `arena/01a07999-tourism`. Every number from live DB queries / HTTP calls, not estimates.

## A. Repository State
Commit `3d938ce`→(this arc) · clean tree · 76 migrations applied · services: API/UI/ML all 200.

## B. Geographic Coverage (real counts)

| Province | Destinations | Nearby test | Search test |
|---|---|---|---|
| Bagmati | 2,997 | PASS (District Police Office KTM, 0.0 km) | PASS (bhaktapur: 30) |
| Gandaki | 2,819 | PASS (Pokhara, 0.0 km) | PASS (pokhara: 30) |
| Koshi | 1,133 | PASS (Ilam Police Station, 0.34 km) | PASS (ilam: 30) |
| Lumbini | 736 | PASS (Lumbini Royal Garden, 0.02 km) | PASS (lumbini: 30) |
| Karnali | 501 | PASS (Rara Karnali Eco Stay, 0.0 km) | PASS (rara: hits) |
| Sudurpashchim | 205 | PASS (balbalika picnic side, 2.29 km) | PASS (khaptad: 8) |
| Madhesh | 190 | PASS (Mithila Grand Resort, 0.04 km) | PASS (janakpur: 30) |

Totals: 8,586 destinations · 1,653 hotels · 393 hospitals · 641 police · Restaurant table: 0 rows
(restaurants live in OSM services + destination categories — reported as a data gap, not faked).

**Districts: 77/77 covered** after adding documented 2018 administrative-rename aliases
(Rukum East→Eastern Rukum, Nawalparasi West→Parasi, etc.) to the canonical map.

## C. Data Quality (actual counts)

- Missing coordinates: 128 · Outside Nepal bbox: 3 (one had **Finland** coordinates)
- Approved junk rows found: '3-10', 'Destination', 'Clothing/Gear Cost (USD)' → **rejected** (reversible status change, IDs preserved, not deleted)
- 2 E2E-harness artifacts already rejected/archived
- Duplicate name+coord rows: **142** (dedupe workflow = remaining item)
- Municipality mappings: 1 verified, 133 candidates pending admin review
- Province-less records: 0 remaining (the "4" were the junk rows above)

## D. Functional Verification (live API, this arc)

- **Nearby: 7/7 provinces PASS** — genuine local records, typed DB ids (dest-/ht-/pol-), sensible distances
- **Search: fixed a real nationwide bug** — `search_places()` applied the radius filter against a
  Pokhara default reference even with no GPS, so text search was silently Pokhara-centric
  ("lumbini" → 0 despite 46 active records). Radius now applied **only when GPS supplied**.
  Live: lumbini/khaptad/ilam/janakpur/bhaktapur all return real results. 2 regression tests added.
- **Performance (median of 5)**: nearby 4 ms · search 3.6 ms · destinations 71 ms · public config 68 ms
  — far inside the <500 ms targets.

## E. Remaining (honest)

1. **Data gaps (need import, not invention)**: Restaurant table empty; 128 records missing coordinates;
   142 duplicate candidates; 133 municipality candidates awaiting admin verification; service coverage
   thin in Madhesh/Sudurpashchim (190/205 destinations vs 2,997 Bagmati).
2. **Code items**: 53 exhaustive-deps warnings (deferred with reason); visual viewport pass (no browser automation).
3. Routes: road routing via provider abstraction with estimated ETAs (label enforced); trekking routes
   are itinerary/destination content, not a separate route entity (documented limitation).

## Verdict

- **Architecture coverage: READY** (nationwide hierarchy, canonical tables, admin CRUD)
- **Functional coverage: READY** (nearby/search/itinerary-FK/navigation proven in all 7 provinces; search bug fixed this arc)
- **Data coverage: PARTIALLY READY** (all provinces populated; depth uneven; restaurant/dedupe/municipality
  verification gaps require data imports via the built workflows)

Overall: **PARTIALLY READY — launch-viable for the covered dataset; data-depth gaps listed above.**
