# Frontend Route Audit (Phase 1)

Generated from `frontend/Tourism/src/App.jsx` (70 `<Route>` definitions).
Status notes reflect verified code state on `arena/01a07999-tourism`.

Legend: **Auth** = requires login to be useful (backend still enforces), **API** = primary Django/ML endpoints, **State** = functional / redirect / duplicate.

## Aggregates
- Total `<Route>` definitions: **70**
- Redirects: **1** (`/trip-planner` → `/itinerary`)
- Duplicate *path* definitions: **0** (verified with `sort | uniq -d`)
- Removed competing implementations: **1** (`pages/TripPlanner.jsx`, merged into `Itinerary.jsx`)
- Alias pairs kept intentionally (same component, two URLs): `/safety`+`/family-safety`, `/knowledge-base`+`/how-it-works`, `/destinations/compare`+`/compare`, `/login`+`/login/user`, `/trip`+`/trip/:reference?`

## Route matrix
| Path | Component | Purpose | Primary API | Auth | State |
|---|---|---|---|---|---|
| `/` | Landing | Home / hero / featured | config/public, destinations | no | functional |
| `/login`, `/login/user` | UserLogin | Tourist auth | auth/token | no | functional |
| `/staff/login`, `/admin/login` | Staff/AdminLogin | Role auth | auth/token | no | functional |
| `/register` | Register | Signup + email verify | users/register | no | functional |
| `/forgot-password` | ForgotPassword | Reset | auth reset | no | functional |
| `/auth/callback/:provider` | OAuthCallback | OAuth (verified working) | oauth | no | functional |
| `/destinations` | DestinationList | Search/filter/list | destinations | no | functional |
| `/destinations/:slug` | DestinationDetails | Detail + gallery + hotels + risk | destinations, ml/risk | no | functional |
| `/compare`, `/destinations/compare` | CompareDestinations | Compare | destinations | no | functional (alias) |
| `/gallery` | Gallery | Photo grid | destinations images | no | functional |
| `/itinerary` | Itinerary | Canonical planner (merged) | ml/itinerary, ml/itinerary/modify | opt | functional |
| `/trip-planner` | Navigate | Redirect → `/itinerary` | — | — | redirect |
| `/packages`, `/packages/:slug` | Packages/Detail | Published packages | marketplace | no | functional |
| `/checkout` | Checkout | Booking **request** (no payment) | marketplace orders | yes | functional, labelled |
| `/trip`, `/trip/:reference?` | TripStatus | Booking status | marketplace orders | opt | functional |
| `/hotels` | Hotels | Hotel list | hotels | no | functional |
| `/hotels/search` | HotelSearch | Hotel search | hotels, ml/hotel | no | functional |
| `/emergency` | Emergency | Hospitals/police/SOS | emergency, safety | no | functional |
| `/family-safety`, `/safety` | FamilySafety | Links + tracking + SOS (30s poll) | safety/family-links | yes | functional, labelled |
| `/safety/shared/:token` | SharedTripView | Shared trip view | shared trips | no | functional |
| `/navigation` | Navigation | Road routes | ml/routes | no | functional |
| `/recommendation` | Recommendation | AI recs | ml/recommendation | opt | functional |
| `/chatbot` | Chatbot | Assistant | chatbot, ml | opt | functional |
| `/budget-estimator` | BudgetEstimator | Budget ML | ml/budget | no | functional |
| `/dashboard` | Dashboard | Traveler home | many | yes | functional |
| `/profile`, `/personal-details` | Profile/PersonalDetails | Account | users | yes | functional |
| `/verify-phone` | VerifyPhone | OTP | sms verify | yes | functional |
| `/favorites` | Favorites | Saved | favorites | yes | functional |
| `/history` | History | Visit history | history | yes | functional |
| `/expenditure` | Expenditure | Expense tracker | expenses | yes | functional |
| `/my-submissions` | MySubmissions | User submissions | submissions | yes | functional |
| `/destinations/submit` | SubmitPlacePage | Community place submit | submissions | yes | functional |
| `/submit-service` | SubmitServicePage | Service submit | submissions | yes | functional |
| `/partner` | PartnerDesk | Partner onboarding | marketplace partners | yes | functional |
| `/collaborate` | Collaborate | Partner info | — | no | functional |
| `/staff`, `/staff/*` | StaffDashboard | Staff console (many tabs) | admin_panel | staff | functional |
| `/local/dashboard` | LocalDashboard | Local admin | admin | staff | functional |
| `/admin/hotel-assignments` | HotelAssignments | Assign hotels | admin_panel | super | functional |
| `/admin/tasks` | AdminTasks | Staff tasks | admin_panel | staff | functional |
| `/admin/diagnostics` | DiagnosticsCenter | Error log + health | audit | staff | functional |
| `/settings`, `/language` | Settings/Language | Prefs + i18n | config, users | yes | functional |
| `/about`,`/contact`,`/support`,`/privacy`,`/terms`,`/how-it-works`,`/knowledge-base`,`/thank-you` | Static/info | CMS-managed copy | config/public | no | functional |
| `/discover-nepal`, `/explore-map` | Discover/Map | Discovery + map | destinations | no | functional |
| `*` | NotFound | 404 | — | no | functional |

## Notes / findings
- The former duplicate planner is gone; `/trip-planner` redirects so all existing
  links keep working. The canonical `/itinerary` now also carries the merged
  AI-refine bar, cost notepad, and `?dest=` focus chip.
- "Live" tracking/SOS is honestly labelled as 30s polling with a last-updated
  timestamp (no fake realtime claim).
- Booking is a request/inquiry system; the UI says so and the operator
  confirm/cancel flow notifies the traveler (`views_marketplace.py`).
