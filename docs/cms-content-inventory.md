# CMS-Controlled Content Inventory

_Generated 2026-09-08 from live code scan + database. Every row is admin-editable from_ **Admin → CMS Studio** _(pages/sections resources) and served to the public site through `/api/v1/config/public/`._

**Managed pages in database: 49** · **Content sections: 91**

| Route | Page key | Title | Frontend CMS hooks | Sections in DB |
|---|---|---|---|---|
| `/` | `home` | Nepal Yatra | `pages/Landing.jsx` (pageCMS) | 14 |
| `/about` | `about` | About Us | `pages/About.jsx` (pageCMS) | 1 |
| `/admin` | `admin-console` | Admin Console | title/SEO/meta only | 1 |
| `/budget-estimator` | `budget-estimator` | Budget Estimator | `pages/BudgetEstimator.jsx` (CMSPageIntro) | 1 |
| `/chatbot` | `chatbot` | Himal AI Assistant | `Chatbot.jsx` (CMSPageIntro) | 1 |
| `/checkout` | `checkout` | Booking Checkout | `pages/Checkout.jsx` (CMSPageIntro) | 1 |
| `/collaborate` | `collaborate` | Collaborate With Us | `pages/Collaborate.jsx` (CMSPageIntro) | 1 |
| `/compare` | `compare` | Compare Destinations | `pages/CompareDestinations.jsx` (CMSPageIntro) | 1 |
| `/contact` | `contact` | Contact Us | `pages/Contact.jsx` (CMSPageIntro) | 1 |
| `/dashboard` | `dashboard` | Traveller Dashboard | title/SEO/meta only | 15 |
| `/destinations` | `destinations` | Destinations | `pages/destinations/DestinationList.jsx` (pageCMS) | 5 |
| `/destinations/:slug` | `destination-detail` | Destination detail | `pages/destinations/DestinationDetails.jsx` (pageCMS) | 5 |
| `/destinations/submit` | `submit-place` | Submit a Place | `pages/SubmitPlacePage.jsx` (CMSPageIntro) | 1 |
| `/discover-nepal` | `discover-nepal` | Discover Nepal | `pages/DiscoverNepal.jsx` (CMSPageIntro) | 1 |
| `/emergency` | `emergency` | Emergency Hub | `components/cms/CMSPageIntro.jsx` (CMSPageIntro), `pages/Emergency.jsx` (CMSPageIntro) | 2 |
| `/expenditure` | `expenditure` | Travel Expenditure | `pages/Expenditure.jsx` (CMSPageIntro) | 1 |
| `/explore-map` | `explore-map` | Explore by Province | `pages/ExploreNepalMap.jsx` (CMSPageIntro) | 1 |
| `/family-safety` | `family-safety` | Family Safety | `pages/FamilySafety.jsx` (CMSPageIntro) | 1 |
| `/favorites` | `favorites` | Saved Favorites | `pages/Favorites.jsx` (CMSPageIntro) | 1 |
| `/footer` | `footer` | Site footer | `components/layout/Footer.jsx` (pageCMS) | 5 |
| `/gallery` | `gallery` | Visual Gallery | `pages/Gallery.jsx` (pageCMS) | 1 |
| `/history` | `history` | Visit History | `pages/History.jsx` (CMSPageIntro) | 1 |
| `/hotels` | `hotels` | Hotels and Lodges | `pages/Hotels.jsx` (pageCMS) | 2 |
| `/hotels/search` | `hotel-search` | Hotel Search | `pages/HotelSearch.jsx` (CMSPageIntro) | 1 |
| `/how-it-works` | `how-it-works` | How Nepal Yatra Works | `pages/HowItWorks.jsx` (CMSPageIntro) | 1 |
| `/itinerary` | `itinerary` | Itinerary Planner | `pages/Itinerary.jsx` (CMSPageIntro) | 1 |
| `/language` | `phrasebook` | Nepal Phrasebook | `pages/Language.jsx` (CMSPageIntro) | 1 |
| `/my-bookings` | `bookings` | My Bookings | `MyBookings.jsx` (CMSPageIntro) | 1 |
| `/my-submissions` | `my-submissions` | My Submissions | `pages/MySubmissions.jsx` (CMSPageIntro) | 1 |
| `/navigation` | `navigation` | Route Navigation | `pages/Navigation.jsx` (CMSPageIntro) | 1 |
| `/nearby-places` | `nearby-places` | Nearby Places | `pages/NearbyPlaces.jsx` (CMSPageIntro) | 1 |
| `/notifications` | `notifications` | Notifications | `pages/Notifications.jsx` (CMSPageIntro) | 1 |
| `/packages` | `packages` | Travel Packages | `pages/Packages.jsx` (pageCMS) | 1 |
| `/packages/:slug` | `package-detail` | Package Detail | `pages/PackageDetail.jsx` (CMSPageIntro) | 1 |
| `/partner` | `partner-desk` | Partner Desk | `pages/PartnerDesk.jsx` (CMSPageIntro) | 1 |
| `/personal-details` | `personal-details` | Personal Details | `pages/PersonalDetails.jsx` (CMSPageIntro) | 1 |
| `/privacy` | `privacy-policy` | Privacy Policy | `pages/PrivacyPolicy.jsx` (CMSPageIntro) | 1 |
| `/profile` | `profile` | My Profile | `pages/Profile.jsx` (CMSPageIntro) | 1 |
| `/recommendation` | `recommendation` | AI Recommendations | `pages/Recommendation.jsx` (pageCMS) | 1 |
| `/risk-alerts` | `risk-alerts` | Risk Alerts | `pages/RiskAlertDashboard.jsx` (CMSPageIntro) | 2 |
| `/settings` | `settings` | Settings | `pages/Settings.jsx` (CMSPageIntro) | 1 |
| `/staff` | `staff-desk` | Staff Operations Desk | title/SEO/meta only | 1 |
| `/submit-service` | `submit-service` | Submit a Tourism Service | `pages/SubmitServicePage.jsx` (CMSPageIntro) | 1 |
| `/support` | `customer-support` | Customer Support Centre | `pages/CustomerSupport.jsx` (CMSPageIntro) | 1 |
| `/terms` | `terms-of-service` | Terms of Service | `pages/TermsOfService.jsx` (CMSPageIntro) | 1 |
| `/thank-you` | `thank-you` | Submission Received | `pages/ThankYou.jsx` (CMSPageIntro) | 1 |
| `/translation` | `translation` | Live Translation | `pages/Translation.jsx` (CMSPageIntro) | 1 |
| `/trip` | `shared-trip` | Shared Trip | `pages/SharedTripView.jsx` (CMSPageIntro) | 1 |
| `/trip-planner` | `trip-planner` | Trip Planner | title/SEO/meta only | 1 |

## What admins control per page

- **Every page (all rows above):** page title, SEO title, meta description, OG image, search visibility (robots), enable/disable, draft/scheduled/published workflow, revision history, and the **View live page** button.
- **Pages with an intro hook (`CMSPageIntro`/`pageCMS`):** an editable intro block (title/subtitle/body/media) rendered above the page content — invisible until published, so defaults never change unexpectedly.
- **Dashboard & Landing & Footer:** full section-level control (hero, cards, galleries, text blocks, reorder, conditional visibility windows, form blocks) via the sections resource.
- **Global:** branding (site title, logo, hero images, contact info, social URLs), navigation menus (header/footer locations), translations per page/section.

## Verification chain (proven live)

Admin PATCH `/admin/cms/` → revision recorded → publish → `GET /config/public/` serves it → frontend renders (document.title/meta via MainLayout; sections via usePublicConfig hooks) → row persisted in PostgreSQL/SQLite `tourist_managedpage`/`tourist_contentsection`.
