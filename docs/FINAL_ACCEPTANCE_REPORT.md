# Digital Nepal Tourism Platform — Final Automated Acceptance Report

Date: 2026-08-20

## Scope validated

- Traveller authentication, profiles, favourites, reviews, bookings, notifications and saved plans
- Admin and capability-scoped staff authorization
- District and hotel object assignment boundaries
- Destination, image, CMS, media, dataset, hotel, restaurant, transportation and travel-plan management
- Review, feedback, safety and risk moderation
- User deactivation/anonymization and protected retention
- Notification preferences, delivery queue and retries
- Public CMS configuration and translations
- ML HTTP degradation and bundled GraphML routing fallback

## Automated results

### Django

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Result after the navigation, CMS catalog and media-management regression pass: **177 tests passed**. No unapplied model changes and no Django runtime check failures.

The three legacy routing assertions that expected HTTP 503 when the external ML service was offline were corrected to verify the intended bundled GraphML fallback: HTTP 200, `bundled_nepal_graphml`, and real route points.

### Production transport security

```bash
DEBUG=False SECRET_KEY='<long production secret>' python manage.py check --deploy
```

Result: no Django `security.W*` warnings. Production defaults enable HTTPS redirect, secure session/CSRF cookies, HSTS, content-type nosniff, proxy SSL detection and frame denial. Development keeps preview-compatible settings while `DEBUG=True`.

DRF schema generation still emits documentation-only type-inference warnings for legacy APIViews without explicit response serializers. These do not indicate runtime or authorization failures.

### React

```bash
npm run build
```

Result after the fixed navigation and media-management UI pass: production build passed with **758 modules**. Vite reports advisory bundle-size/code-splitting warnings; no compilation failure occurred.

`npm run lint` could not execute because the repository does not install an ESLint binary in the current dependency lock. The production compiler successfully parsed all JSX modules.

### ML and routing

```bash
python ml_service/test_routes.py
python ml_service/test_recommendation.py
python -m compileall -q ml_service Tourism/tourist Tourism/booking Tourism/admin_panel
```

Results:

- Graph route, exact-place route, nearby-place and itinerary smoke checks passed.
- Recommendation engine smoke check passed after installing the committed `ml_service/requirements.txt` dependencies.
- Python compilation passed.

## Expected test-environment degradation

The suite intentionally verifies graceful unavailable states for unconfigured/downstream services. Logs can therefore contain expected warnings for:

- OpenWeather without a configured key
- Overpass network/TLS unavailability
- External ML budget/safety service unavailability
- Missing official DHM/BIPAD feed URLs

No official warning, provider delivery, road metric or safety record is fabricated when these integrations are unavailable.

## Hotel media audit

The active SQLite dataset contains 1,552 hotels. None currently has a verified hotel-specific cover (`cover_image` or `external_image_url`), but every hotel is linked to a destination with displayable destination media. The API and React UI now expose this distinction explicitly:

- `image_is_hotel_specific=true` only for actual hotel media.
- `image_source=destination_context` for the current 1,552 contextual fallbacks.
- Context images are visibly labelled **Destination area photo**.
- Broken remote images advance to a bundled destination-specific image and then to an explicit unavailable state; they no longer remain as broken image elements.
- Admins can assign a verified HTTPS hotel image from Hotels & Bookings, and the hotel-specific image immediately takes priority everywhere.

Audit result: **1,552/1,552 active hotels have a displayable, honestly labelled media response; 0 are falsely claimed as hotel-specific.** Real hotel-specific photos still require verified source collection or administrator uploads and are not fabricated.

## Manual checks still required before a real public launch

Automated tests cannot replace deployment-specific review. Before launch, operators should still perform:

1. Browser screen-reader and keyboard review with representative users.
2. Real SMTP, Twilio and FCM provider acceptance tests using non-production recipients.
3. Official DHM/BIPAD connector validation with authorized feed credentials.
4. Load testing against production-sized infrastructure and database services.
5. Backup restoration and incident-response drills.
6. Legal/privacy review of configured retention windows.
7. Real-device mobile testing and final visual approval.

These are operational launch checks, not missing application modules.

## Admin navigation, CMS catalog and media follow-up

- Admin priority actions are now in a fixed top navigation; all 27 management sections are grouped in a fixed, collapsible sidebar instead of a horizontal overflow strip.
- Admin, Staff and Traveller shells have distinct feature-specific navigation. Navbar and sidebars remain fixed while content scrolls.
- Admin and Staff workspaces use white surfaces and Nepal-green accents.
- The database-driven CMS catalog contains 28 pages, 35 sections and 53 navigation records. These are editable through friendly form controls, with advanced JSON retained only as an optional tool.
- The Central Media Library exposes all 19,328 image records through server pagination. It now supports validated computer uploads, external HTTPS media, source/license metadata, working move-up/move-down ordering, cover selection and moderation.
- Hotels & Bookings exposes all 1,552 active hotels through pagination and supports hotel cover uploads or verified external image URLs.
- The React `/admin/login` route is no longer intercepted by the Django Admin development proxy; traditional Django Admin remains available through `/django-admin/` in the frontend proxy and `/admin/` on the backend.

### Runtime UI smoke validation

A headless Chromium smoke flow logged into the real React Admin portal, opened the CMS and Central Media Library, and scrolled the workspace. It confirmed 28 editable CMS pages, 19,328 paginated media records, fixed header positioning, and no React page exceptions. The reported `destroy is not defined`/`destroy is not a function` issue was traced to async loaders passed directly to `useEffect`, whose returned Promises were treated as cleanup functions in React Strict Mode. All affected effects now use non-returning wrappers.
