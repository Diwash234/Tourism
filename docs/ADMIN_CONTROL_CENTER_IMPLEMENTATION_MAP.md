# Admin Control Center — Existing-System Implementation Map

Audit date: 2026-08-19

This audit is the required Phase 1 gate. The platform remains one React/Vite → Django REST/SQLite → FastAPI ML system. Existing models and APIs are extended; no parallel authentication, destination database, image pipeline, or ML service will be created.

## Existing architecture and required extension

| Domain | Existing source of truth | Existing UI/API | Required safe extension |
|---|---|---|---|
| Authentication | `tourist.User`, JWT, AuthContext | User/Admin/Staff login portals, `AdminRoute`, `StaffRoute` | Keep JWT/session; add module/action permissions enforced by DRF and mirrored in staff navigation |
| Roles | User role enum plus Django `is_staff/is_superuser` | Admin/staff/local guards | Map existing roles to granular capabilities; prevent self-elevation |
| Staff work | `admin_panel.HotelAssignment`, `AdminTask` | `/staff`, assignments/tasks APIs | Permission profile and module-scoped work queues; preserve assignments/tasks |
| Destinations | `Destination` | Destination ViewSet, admin destination APIs, User Dashboard | Continue same table/API; modern searchable CRUD and content configuration |
| Images | `DestinationImage`, image service/pipeline | Images/discover/refresh/set-cover APIs, admin pipeline | Reuse APIs; media selector, local uploads, ordering, provenance and safe delete |
| Hotels | `Hotel`, `Booking`, `HotelReview` | Hotel APIs, booking pages, Django Admin | Searchable hotel/booking/review management using existing rows |
| Categories | `Category` | Category ViewSet and Django Admin | Modern CRUD; changes continue through existing destination APIs |
| Safety | Alert, RiskIncident, CurrentHazard, RiskObservation | Risk/emergency APIs and pages | Role-scoped CRUD and source/verification workflow |
| Budgets | Budget, BudgetEstimation, TravelExpenseFeedback | Budget APIs, feedback forms, ML pipeline | Validated staff entry → approval → DB/CSV export → explicit training |
| Feedback | UserFeedback, FeedbackEvidence | Public feedback and admin list/reply | Conversation messages/status/assignment without replacing current records |
| Notifications | Notification, DeviceToken | User notifications | Emit admin/staff events through existing notification system |
| Audit | `audit.AuditLog`, `audit.ErrorEvent`; DestinationAuditLog | Diagnostics Center, audit APIs | Record CMS/config old/new values and CRUD actions |
| Admin UI | Large `AdminDashboard` with overview, users, queues, images, ML | `/admin` under existing protected layout | Dedicated Admin shell/sidebar/navbar; split lazy management modules while retaining APIs |
| Staff UI | StaffDashboard field expense/risk | `/staff` | Dedicated restricted shell; menu generated from backend capabilities |
| Django Admin | Extensive ModelAdmin registrations | `/admin/` backend and `/django-admin/` preview proxy | Preserve as superuser/developer interface |
| Current React data explorer | `AdminDataExplorerView` and `DataExplorerPanel` | Searchable 26-resource read view; destination editor and upload | Add backend pagination/filter/sort and safe CRUD actions incrementally |
| Site config | Public config currently only exposes safe API config | `configApi.getPublicConfig()` | Add structured site/page/section/navigation/branding configuration with defaults |
| i18n | Lightweight dictionaries (en/ne/hi), Language table, translation API | Language switcher and Settings | Preserve three complete UI languages; dynamic content translations remain in DestinationTranslation/CMS translations |
| ML | Existing FastAPI recommendation/budget/risk/route/translation | Django proxy and admin training registry | Preserve contracts; only approved exports enter training |

## New foundational models required (Phase 5)

These should be introduced by reversible Django migrations with defaults matching the existing UI:

- `SiteSetting`: validated key, structured value, scope, active, updated_by.
- `ManagedPage`: existing route identifier, title/meta, enabled; cannot create unsafe arbitrary React routes.
- `ContentSection`: page/key/title/subtitle/body/media/CTA/order/visibility/layout variant/status.
- `ManagedNavigationItem`: navbar/sidebar location, validated route, label, icon allowlist, parent, order, role visibility.
- `MediaAsset`: existing storage/external URL references, provenance, usage metadata; does not move large image datasets into SQLite.
- `StaffCapabilityProfile`: one-to-one existing User, structured allowed module/actions, district restriction, assigned_by.
- `FeedbackMessage`: thread messages attached to existing UserFeedback.

## Backend authorization map

| Module | Admin | Staff default | Required backend enforcement |
|---|---:|---:|---|
| Users/roles/system settings | Full | None | Admin/super-admin only |
| Destinations | Full | None until assigned | view/add/change/delete capability + district object checks |
| Images/content | Full | None until assigned | module capability plus provenance validation |
| Budget/dataset | Full | None until assigned | view/add/change/export/train separately |
| Hotels | Full | Assigned hotels only | preserve HotelAssignment object scope |
| Safety | Full | Explicit emergency/safety capability | source verification permissions |
| Feedback | Full | Assigned/read/reply capabilities | queryset scoping and action checks |
| Audit | Full/read | Usually none | immutable logs; acknowledge permission separate |

Frontend hiding is never sufficient; every write API must enforce the same capability.

## Existing functionality that must not be duplicated

- Destination and Category models/ViewSets.
- DestinationImage/image acquisition endpoints.
- JWT/AuthContext and role login portals.
- AdminRoute/StaffRoute guards.
- HotelAssignment/AdminTask.
- AuditLog/ErrorEvent and Diagnostics Center.
- Budget/risk feedback and ML training pipeline.
- Notification model/services.
- Django Admin.

## Phased implementation plan

1. **Audit (this document): complete.**
2. **RBAC:** capability profile, DRF permission, `/me/capabilities`, tests for forbidden writes/escalation.
3. **Admin shell:** dedicated layout/navbar/collapsible management sidebar; existing Admin Dashboard embedded unchanged initially.
4. **Core CRUD:** split Users, Destinations, Categories, Images, Hotels, Bookings, Reviews, Emergency, Feedback and Audit into paginated modules over existing models.
5. **CMS:** site settings/pages/sections/navigation/media with safe schema and default seed migration.
6. **User integration:** central public site-config context with existing hard-coded values as fallback; progressively wire headings/nav/sections.
7. **Budget/dataset:** validated workflows and explicit export/training jobs.
8. **Communication:** messages, assignment, replies and notifications attached to existing feedback.
9. **Staff shell:** capability-filtered modules and existing task/assignment integration.
10. **Regression/security:** existing Django suite, role/API matrix, frontend production build and route checks.

## Current verified completion status (updated 2026-08-20)

- Existing User Dashboard, authentication, destination, budget, risk, routing and ML contracts remain operational.
- Traditional Django Admin is preserved alongside the React Admin Control Center.
- Capability/action RBAC is backend-enforced for users, destinations, images, content, budget, datasets, hotels, restaurants, transportation, travel plans, reviews, safety, feedback, audit and settings.
- District, assigned-hotel, assigned-task and owner object boundaries are tested.
- Staff has capability-generated module workspaces and completion reporting.
- CMS pages, sections, navigation hierarchy, translations, revisions, preview, scheduling, publishing and rollback are database-driven.
- Branding assets, safe theme presets, notification delivery/preferences/retries, datasets, media, reports, retention, anonymization and protected archival are implemented.
- Shared accessible Admin primitives, keyboard skip navigation, focus styles, reduced-motion support and responsive layouts are implemented.
- Full automated acceptance completed with 172 Django tests, frontend production build, ML/routing smoke tests and deployment security checks.
- `DestinationImage` remains the media source of truth rather than introducing the originally proposed duplicate `MediaAsset` table; the Central Media Library safely manages those existing records.
- Deployment-specific provider, official-feed, legal, load, backup-restore and real-device checks remain operational launch responsibilities, as documented in `FINAL_ACCEPTANCE_REPORT.md`.

## Acceptance guardrails

- CMS failure must return existing/default UI content.
- No arbitrary HTML, JavaScript, CSS, icons or routes.
- All config writes are admin-only and audited.
- Staff querysets are capability/object scoped.
- Large lists use server pagination and filtering.
- Deletes follow existing protection/soft-delete semantics.
- Existing public API response shapes remain backward compatible.
