"""
Regression suite for the Nepal Yatra fix pass (audit REQ-038).

Each test pins one previously-fixed behavior so it cannot silently regress:
  1. /destinations/nearby/ accepts latitude/longitude/radius_km (destinationApi.nearby contract)
  2. invalid pagination pages return a clean 404 JSON, not a 500
  3. admin CMS endpoints are backend-authoritative (401 unauthenticated)
  4. public feedback POST persists a real row (feedback E2E)
  5. notification preferences PATCH persists (no fake success possible)
  6. change-password rejects wrong old password and accepts correct one
  7. navbar serves exactly the 5 required top labels with Emergency Services
  8. Plan a Trip dropdown exposes Destinations / Budget / Hotels / Risk Alerts
  9. CMS PATCH -> publish -> public config serves the new content
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .location.search_service import LocationSearchService
from .models import (
    User,
    SiteSetting,
    StaffCapabilityProfile,
    Category,
    Destination,
    Province,
    District,
    Hospital,
    Hotel,
    UserFeedback,
    NotificationPreference,
    ManagedNavigationItem,
    ManagedPage,
    ContentSection,
    NewsletterSignup,
    UserRoute,

    MunicipalityMapping,)


def make_superuser():
    return User.objects.create_user(
        email="regression-admin@test.local",
        password="Regression!Pass123",
        role="SUPER_ADMIN",
        is_superuser=True,
        is_staff=True,
    )


class NearbyEndpointRegressionTests(TestCase):
    def test_nearby_accepts_frontend_param_names(self):
        resp = self.client.get(
            "/api/v1/destinations/nearby/",
            {"latitude": 27.7172, "longitude": 85.3240, "radius_km": 50},
        )
        self.assertEqual(resp.status_code, 200)


class PaginationRegressionTests(TestCase):
    def test_non_numeric_page_is_clean_404(self):
        resp = self.client.get("/api/v1/destinations/", {"page": "abc"})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("detail", resp.json())

    def test_zero_page_is_clean_404(self):
        resp = self.client.get("/api/v1/destinations/", {"page": 0})
        self.assertEqual(resp.status_code, 404)


class AdminAuthRegressionTests(TestCase):
    def test_admin_cms_requires_authentication(self):
        resp = self.client.get("/api/v1/admin/cms/")
        self.assertIn(resp.status_code, (401, 403))


class FeedbackRegressionTests(TestCase):
    def test_public_feedback_post_persists(self):
        resp = self.client.post(
            "/api/v1/feedback",
            {"name": "Reg", "email": "reg@test.local", "subject": "REG-CHECK", "message": "regression"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(UserFeedback.objects.filter(subject="REG-CHECK").exists())


class NotificationPreferenceRegressionTests(TestCase):
    def test_patch_persists_preference(self):
        user = make_superuser()
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.patch(
            "/api/v1/notification-preferences/", {"marketing": True}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        pref = NotificationPreference.objects.get(user=user)
        self.assertTrue(pref.marketing)


class ChangePasswordRegressionTests(TestCase):
    def test_wrong_old_password_rejected(self):
        user = make_superuser()
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "wrong-pass", "new_password": "Brand!New123"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_correct_old_password_changes_it(self):
        user = make_superuser()
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "Regression!Pass123", "new_password": "Brand!New123"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Brand!New123"))


class NavbarStructureRegressionTests(TestCase):
    def test_required_top_labels_served(self):
        resp = self.client.get("/api/v1/config/public/")
        self.assertEqual(resp.status_code, 200)
        nav = resp.json().get("navigation", [])
        tops = [
            n["label"]
            for n in nav
            if n.get("location") == "navbar" and not n.get("parent_id") and n.get("is_active", True)
        ]
        for required in ["Home", "Explore", "Plan a Trip", "Emergency Services", "About"]:
            self.assertIn(required, tops)

    def test_plan_a_trip_children(self):
        resp = self.client.get("/api/v1/config/public/")
        nav = resp.json().get("navigation", [])
        plan = next(
            (n for n in nav if n.get("location") == "navbar" and n.get("label") == "Plan a Trip" and not n.get("parent_id")),
            None,
        )
        self.assertIsNotNone(plan, "Plan a Trip top-level item must exist")
        child_labels = {n["label"] for n in nav if n.get("parent_id") == plan["id"]}
        for required in ["Destinations", "Hotels", "Risk Alerts"]:
            self.assertIn(required, child_labels)
        self.assertTrue(any("Budget" in label for label in child_labels))


class CMSPublishFlowRegressionTests(TestCase):
    def test_patch_publish_public_chain(self):
        admin = make_superuser()
        client = APIClient()
        client.force_authenticate(user=admin)

        page = ManagedPage.objects.create(
            key="regression-page", route="/regression-page", title="Regression", status="published", is_enabled=True
        )
        section = ContentSection.objects.create(
            page=page, key="intro", title="Original", body="", status="published", is_visible=True
        )

        # 1. PATCH persists
        resp = client.patch(
            "/api/v1/admin/cms/",
            {"resource": "sections", "id": section.id, "title": "Regression Updated"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        section.refresh_from_db()
        self.assertEqual(section.title, "Regression Updated")

        # 2. publish + public config serves it
        client.patch(
            "/api/v1/admin/cms/",
            {"resource": "sections", "action": "publish", "id": section.id},
            format="json",
        )
        public = self.client.get("/api/v1/config/public/").json()
        served = next((p for p in public.get("pages", []) if p.get("key") == "regression-page"), None)
        self.assertIsNotNone(served, "published regression page must appear in public config")
        titles = [s.get("title") for s in served.get("sections", [])]
        self.assertIn("Regression Updated", titles)


class TravelerDocumentRegressionTests(TestCase):
    """Pins the Personal Details page chain: /traveler-documents/ CRUD is real,
    persisted, and strictly scoped to the owning user (no fake local saves)."""

    def setUp(self):
        self.alice = User.objects.create_user(email="alice-docs@test.local", password="Docs!Pass123")
        self.bob = User.objects.create_user(email="bob-docs@test.local", password="Docs!Pass123")

    def test_crud_is_scoped_to_owner(self):
        client = APIClient()
        client.force_authenticate(self.alice)
        created = client.post("/api/v1/traveler-documents/", {
            "full_name": "Alice Rai", "relation_tag": "self",
            "id_type": "passport", "id_number": "P123456", "nationality": "Nepali",
        }, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        doc_id = created.data["id"]

        listed = client.get("/api/v1/traveler-documents/")
        self.assertEqual(len(listed.data), 1)

        # Bob sees none of Alice's rows and cannot touch them.
        client.force_authenticate(self.bob)
        self.assertEqual(len(client.get("/api/v1/traveler-documents/").data), 0)
        self.assertEqual(client.patch(f"/api/v1/traveler-documents/{doc_id}/", {"phone": "+9779800000001"}, format="json").status_code, 404)
        self.assertEqual(client.delete(f"/api/v1/traveler-documents/{doc_id}/").status_code, 404)

        # Alice can still update + delete her own row.
        client.force_authenticate(self.alice)
        patched = client.patch(f"/api/v1/traveler-documents/{doc_id}/", {"relation_tag": "relative", "relation": "Spouse"}, format="json")
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.data["relation"], "Spouse")
        self.assertEqual(client.delete(f"/api/v1/traveler-documents/{doc_id}/").status_code, 204)
        self.assertEqual(len(client.get("/api/v1/traveler-documents/").data), 0)

    def test_anonymous_denied(self):
        resp = self.client.get("/api/v1/traveler-documents/")
        self.assertIn(resp.status_code, (401, 403))


class PlaceSubmissionFlowRegressionTests(TestCase):
    """Pins the LocalDashboard / SubmitPlacePage chain: authenticated users can
    POST /destinations/ (multipart) and the submission shows up in
    /destinations/my_submissions/ while staying hidden from the public list."""

    def test_submit_then_my_submissions(self):
        from .models import Category, Destination
        category = Category.objects.create(name="Heritage Test", slug="heritage-test")
        user = User.objects.create_user(email="submitter@test.local", password="Submit!Pass123")

        client = APIClient()
        client.force_authenticate(user)
        created = client.post("/api/v1/destinations/", {
            "name": "Test Local Temple", "category": category.id,
            "city": "Bandipur", "address": "Ward 4, Bandipur",
            "description": "A locally submitted temple for regression coverage.",
        }, format="multipart")
        self.assertEqual(created.status_code, 201, created.content)
        # DestinationWriteSerializer returns id (slug is generated server-side
        # and only exposed by the read serializers) — resolve it via the model.
        slug = Destination.objects.get(id=created.data["id"]).slug

        mine = client.get("/api/v1/destinations/my_submissions/")
        results = mine.data.get("results", mine.data)
        self.assertIn(slug, [r["slug"] for r in results])
        row = next(r for r in results if r["slug"] == slug)
        self.assertEqual(row["status"], Destination.SubmissionStatus.PENDING)

        # Public (anonymous) listing must not expose the pending submission.
        public = APIClient().get("/api/v1/destinations/")
        public_results = public.data.get("results", public.data)
        self.assertNotIn(slug, [r["slug"] for r in public_results])

        # Submitter can delete their own pending submission.
        self.assertEqual(client.delete(f"/api/v1/destinations/{slug}/").status_code, 204)


class RedirectRulesRegressionTests(TestCase):
    """Redirects & URLs (CMS brief §14): admin CRUD + public exposure."""

    def setUp(self):
        self.client_admin = APIClient()
        self.client_admin.force_authenticate(user=make_superuser())

    def test_anonymous_cannot_manage_redirects(self):
        self.assertEqual(APIClient().get("/api/v1/admin/redirects/").status_code, 401)

    def test_redirect_lifecycle_and_public_exposure(self):
        created = self.client_admin.post("/api/v1/admin/redirects/", {
            "old_path": "/old-page", "new_path": "/new-page", "note": "renamed"}, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        rule_id = created.data["data"]["id"]

        public = self.client.get("/api/v1/config/public/")
        rules = public.json().get("redirects", [])
        self.assertIn({"old_path": "/old-page", "new_path": "/new-page", "permanent": True}, rules)

        # Pausing removes it from the public config without deleting it.
        paused = self.client_admin.patch("/api/v1/admin/redirects/", {"id": rule_id, "is_active": False}, format="json")
        self.assertEqual(paused.status_code, 200)
        self.assertNotIn("/old-page", [r["old_path"] for r in self.client.get("/api/v1/config/public/").json()["redirects"]])

        self.assertEqual(self.client_admin.delete(f"/api/v1/admin/redirects/?id={rule_id}").status_code, 200)

    def test_loops_and_duplicates_rejected(self):
        self.client_admin.post("/api/v1/admin/redirects/", {"old_path": "/a", "new_path": "/b"}, format="json")
        loop = self.client_admin.post("/api/v1/admin/redirects/", {"old_path": "/b", "new_path": "/a"}, format="json")
        self.assertEqual(loop.status_code, 400)
        dup = self.client_admin.post("/api/v1/admin/redirects/", {"old_path": "/a", "new_path": "/c"}, format="json")
        self.assertEqual(dup.status_code, 400)
        bad = self.client_admin.post("/api/v1/admin/redirects/", {"old_path": "no-slash", "new_path": "/c"}, format="json")
        self.assertEqual(bad.status_code, 400)


class FooterSettingsRegressionTests(TestCase):
    """Footer (§6): branding contact_address whitelist + newsletter store."""

    def test_branding_accepts_contact_address(self):
        client = APIClient()
        client.force_authenticate(user=make_superuser())
        resp = client.patch("/api/v1/admin/branding/", {"branding": {"contact_address": "Kathmandu, Nepal"}}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.data["branding"]["contact_address"], "Kathmandu, Nepal")
        public = APIClient().get("/api/v1/config/public/").json()
        self.assertEqual(public["settings"]["branding"]["contact_address"], "Kathmandu, Nepal")

    def test_newsletter_signup_dedupes_and_validates(self):
        from tourist.models import NewsletterSignup
        first = APIClient().post("/api/v1/newsletter/subscribe/", {"email": "Hiker@Example.com"}, format="json")
        self.assertEqual(first.status_code, 201, first.content)
        second = APIClient().post("/api/v1/newsletter/subscribe/", {"email": "hiker@example.com"}, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(NewsletterSignup.objects.count(), 1)
        bad = APIClient().post("/api/v1/newsletter/subscribe/", {"email": "not-an-email"}, format="json")
        self.assertEqual(bad.status_code, 400)


class NearbyResultsRegressionTests(TestCase):
    """§23/§24: nearby results derive from the real Destination table —
    nearest-first with distance_km, radius honoured, out-of-range coordinates
    rejected, origin switch changes the cluster, and an admin coordinate edit
    moves a destination between result sets (no separate nearby dataset)."""

    def setUp(self):
        from .models import Category, Destination
        cat = Category.objects.create(name="Nearby Test", slug="nearby-test")

        def place(name, lat, lng):
            return Destination.objects.create(
                name=name, category=cat, latitude=lat, longitude=lng,
                status=Destination.SubmissionStatus.APPROVED, is_active=True,
                description=f"{name} regression fixture.",
            )

        # Kathmandu valley cluster (origin 27.7172, 85.3240)
        self.ktm_center = place("KTM Center Temple", 27.7172, 85.3240)      # 0 km
        self.ktm_near = place("Patan Durbar Test", 27.6710, 85.3160)        # ~5 km
        self.ktm_far = place("Nagarkot Viewpoint Test", 27.7100, 85.5200)   # ~19 km
        # Pokhara cluster (origin 28.2096, 83.9856)
        self.pkr_lakeside = place("Phewa Lakeside Test", 28.2096, 83.9856)  # 0 km
        self.pkr_stupa = place("World Peace Stupa Test", 28.1910, 83.9400)  # ~5 km

    def _nearby(self, lat, lng, radius_km):
        resp = self.client.get("/api/v1/destinations/nearby/", {
            "latitude": lat, "longitude": lng, "radius_km": radius_km,
        })
        self.assertEqual(resp.status_code, 200, resp.content)
        return resp.data["results"]

    def test_origin_switch_returns_different_clusters(self):
        ktm_slugs = [r["slug"] for r in self._nearby(27.7172, 85.3240, 25)]
        self.assertIn(self.ktm_near.slug, ktm_slugs)
        self.assertNotIn(self.pkr_lakeside.slug, ktm_slugs)

        pkr_slugs = [r["slug"] for r in self._nearby(28.2096, 83.9856, 25)]
        self.assertIn(self.pkr_stupa.slug, pkr_slugs)
        self.assertNotIn(self.ktm_near.slug, pkr_slugs)
        self.assertNotEqual(ktm_slugs, pkr_slugs)

    def test_results_sorted_nearest_first_with_distance(self):
        rows = self._nearby(27.7172, 85.3240, 25)
        distances = [float(r["distance_km"]) for r in rows]
        self.assertEqual(distances, sorted(distances))
        names = [r["name"] for r in rows]
        self.assertLess(names.index(self.ktm_center.name), names.index(self.ktm_near.name))
        self.assertLess(names.index(self.ktm_near.name), names.index(self.ktm_far.name))
        for row in rows:
            self.assertTrue(row["slug"], "nearby rows must carry slug for detail links")

    def test_radius_expands_results(self):
        tight_slugs = {r["slug"] for r in self._nearby(27.7172, 85.3240, 10)}
        wide_slugs = {r["slug"] for r in self._nearby(27.7172, 85.3240, 25)}
        self.assertIn(self.ktm_near.slug, tight_slugs)       # ~5 km inside 10 km
        self.assertNotIn(self.ktm_far.slug, tight_slugs)     # ~19 km outside 10 km
        self.assertIn(self.ktm_far.slug, wide_slugs)         # inside 25 km
        self.assertTrue(tight_slugs.issubset(wide_slugs))

    def test_out_of_range_coordinates_rejected(self):
        bad_lat = self.client.get("/api/v1/destinations/nearby/", {
            "latitude": 999, "longitude": 85.324, "radius_km": 25})
        self.assertEqual(bad_lat.status_code, 400, bad_lat.content)
        bad_lng = self.client.get("/api/v1/destinations/nearby/", {
            "latitude": 27.7172, "longitude": -200, "radius_km": 25})
        self.assertEqual(bad_lng.status_code, 400, bad_lng.content)

    def test_admin_coordinate_edit_moves_destination_between_origins(self):
        """§24: the admin edit path writes the same Destination row the nearby
        query reads — moving coords moves the row across result sets."""
        # Sanity: Pokhara origin sees the stupa, Kathmandu origin does not.
        self.assertNotIn(self.pkr_stupa.slug,
                         [r["slug"] for r in self._nearby(27.7172, 85.3240, 25)])

        client = APIClient()
        client.force_authenticate(make_superuser())
        upd = client.put(f"/api/v1/admin/destinations/{self.pkr_stupa.id}", {
            "latitude": "27.7000", "longitude": "85.3300",
        }, format="json")
        self.assertEqual(upd.status_code, 200, upd.content)

        ktm_slugs = [r["slug"] for r in self._nearby(27.7172, 85.3240, 25)]
        self.assertIn(self.pkr_stupa.slug, ktm_slugs)
        self.assertNotIn(self.pkr_stupa.slug,
                         [r["slug"] for r in self._nearby(28.2096, 83.9856, 25)])

    def test_admin_rejects_out_of_range_coordinate_edit(self):
        client = APIClient()
        client.force_authenticate(make_superuser())
        resp = client.put(f"/api/v1/admin/destinations/{self.ktm_near.id}", {
            "latitude": "999", "longitude": "85.3300",
        }, format="json")
        self.assertEqual(resp.status_code, 400, resp.content)


class HotelNearbyRegressionTests(TestCase):
    """Nearby hotels derive from the real Hotel table via /hotels/nearby/ —
    haversine on stored coordinates, nearest-first with distance_km, radius
    honoured, inactive rows hidden, out-of-range coordinates rejected."""

    def setUp(self):
        from .models import Category, Destination, Hotel
        cat = Category.objects.create(name="Hotel Nearby Test", slug="hotel-nearby-test")
        dest = Destination.objects.create(
            name="Lakeside Hub", category=cat, latitude=28.2096, longitude=83.9856,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
            description="Hotel nearby fixture destination.",
        )

        def hotel(name, lat, lng, active=True):
            return Hotel.objects.create(
                destination=dest, name=name, latitude=lat, longitude=lng,
                address="Fixture address", is_active=active,
            )

        self.near_hotel = hotel("Lakeside Inn", 28.2050, 83.9800)         # ~0.8 km
        self.far_hotel = hotel("Mountain View Resort", 28.3000, 84.1000)  # ~15 km
        self.closed_hotel = hotel("Closed Lodge", 28.2100, 83.9900, active=False)

    def _nearby(self, lat, lng, radius_km):
        resp = self.client.get("/api/v1/hotels/nearby/", {
            "latitude": lat, "longitude": lng, "radius_km": radius_km,
        })
        self.assertEqual(resp.status_code, 200, resp.content)
        return resp.data

    def test_hotels_nearby_sorted_with_distance(self):
        data = self._nearby(28.2096, 83.9856, 25)
        names = [r["name"] for r in data["results"]]
        self.assertEqual(names[:2], ["Lakeside Inn", "Mountain View Resort"])
        self.assertIn("facilities", data["results"][0], "HotelCard renders real facilities")
        distances = [r["distance_km"] for r in data["results"]]
        self.assertEqual(distances, sorted(distances))
        self.assertLess(distances[0], 1.0)

    def test_hotels_nearby_excludes_inactive_and_honours_radius(self):
        wide = self._nearby(28.2096, 83.9856, 25)
        self.assertNotIn("Closed Lodge", [r["name"] for r in wide["results"]])
        self.assertEqual(wide["count"], 2)
        tight = self._nearby(28.2096, 83.9856, 5)
        tight_names = [r["name"] for r in tight["results"]]
        self.assertIn("Lakeside Inn", tight_names)
        self.assertNotIn("Mountain View Resort", tight_names)
        self.assertEqual(tight["count"], 1)

    def test_hotels_nearby_rejects_out_of_range_coordinates(self):
        resp = self.client.get("/api/v1/hotels/nearby/", {
            "latitude": 999, "longitude": 83.98, "radius_km": 25})
        self.assertEqual(resp.status_code, 400, resp.content)


class UserDataReportsRegressionTests(TestCase):
    """The Dashboard's My-reports panel GETs /reports/submit/ — that used to
    405 (submit-only view) and the frontend swallowed it. GET now returns the
    caller's own reports; anonymous callers get 401; POST stays the write path."""

    def test_get_requires_authentication(self):
        resp = self.client.get("/api/v1/reports/submit/")
        self.assertEqual(resp.status_code, 401, resp.content)

    def test_get_returns_only_own_reports(self):
        from .models import DataReport
        me = User.objects.create_user(email="reporter@test.local", password="Report!Pass123")
        other = User.objects.create_user(email="bystander@test.local", password="Report!Pass123")
        DataReport.objects.create(user=me, report_type="other", severity="medium", status="new", description="mine")
        DataReport.objects.create(user=other, report_type="other", severity="medium", status="new", description="theirs")

        client = APIClient()
        client.force_authenticate(me)
        resp = client.get("/api/v1/reports/submit/")
        self.assertEqual(resp.status_code, 200, resp.content)
        descriptions = [r["description"] for r in resp.data]
        self.assertEqual(descriptions, ["mine"])

    def test_post_still_creates_report(self):
        resp = self.client.post("/api/v1/reports/submit/", {
            "report_type": "wrong_info", "severity": "low", "description": "regression",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)


class CategoryCrudRegressionTests(TestCase):
    """§22: admin category CRUD rides the slug detail route and stays admin-only.

    CategoryViewSet uses lookup_field="slug", so the admin UI must address
    PATCH/DELETE by slug; a numeric id must NOT resolve (that mismatch was a
    real bug where every category edit/delete 404'd).
    """

    def setUp(self):
        from .models import Category
        self.category = Category.objects.create(name="Lakes", slug="lakes")
        self.api = APIClient()
        self.admin = make_superuser()

    def test_admin_patch_by_slug_persists(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.patch(
            f"/api/v1/categories/{self.category.slug}/",
            {"description": "Alpine lakes"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.description, "Alpine lakes")

    def test_numeric_id_detail_route_is_not_the_contract(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.patch(
            f"/api/v1/categories/{self.category.id}/",
            {"description": "nope"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_admin_create_and_delete_by_slug(self):
        self.api.force_authenticate(self.admin)
        created = self.api.post(
            "/api/v1/categories/",
            {"name": "Monasteries", "slug": "monasteries"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        resp = self.api.delete("/api/v1/categories/monasteries/")
        self.assertEqual(resp.status_code, 204)

    def test_public_read_allowed_public_write_rejected(self):
        self.assertEqual(self.api.get("/api/v1/categories/").status_code, 200)
        resp = self.api.post(
            "/api/v1/categories/", {"name": "Hack", "slug": "hack"}, format="json"
        )
        self.assertEqual(resp.status_code, 401)

    def test_plain_user_write_forbidden(self):
        plain = User.objects.create_user(
            email="plain-cat@test.local", password="Plain!Pass123"
        )
        self.api.force_authenticate(plain)
        resp = self.api.post(
            "/api/v1/categories/", {"name": "Nope", "slug": "nope"}, format="json"
        )
        self.assertEqual(resp.status_code, 403)


class DiscoverNepalCatalogRegressionTests(TestCase):
    """culture/cuisine/festivals groups must surface destinations recorded in
    the category taxonomy even when the long-form text fields and curated
    festival notices are still empty — and "agriculture" must never leak into
    the culture group via substring matching."""

    def setUp(self):
        from .models import Category, Destination
        approved = dict(is_active=True, status=Destination.SubmissionStatus.APPROVED)
        self.museum_cat = Category.objects.create(name="Museums & Galleries", slug="museums")
        self.farm_cat = Category.objects.create(name="Agricultural & Farm Tourism", slug="agriculture")
        self.food_cat = Category.objects.create(name="Food & Culinary Tourism", slug="food-culinary")
        self.festival_cat = Category.objects.create(name="Festivals & Events", slug="festivals")
        Destination.objects.create(name="Test Heritage Museum", slug="test-heritage-museum",
                                   category=self.museum_cat, **approved)
        Destination.objects.create(name="Test Poultry Farm", slug="test-poultry-farm",
                                   category=self.farm_cat, **approved)
        Destination.objects.create(name="Test Momo House", slug="test-momo-house",
                                   category=self.food_cat, **approved)
        Destination.objects.create(name="Test Jatra Festival", slug="test-jatra-festival",
                                   category=self.festival_cat, **approved)

    def test_groups_serve_recorded_destinations(self):
        resp = self.client.get("/api/v1/discover-nepal/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        culture_names = {i["name"] for i in data["culture"]["items"]}
        self.assertIn("Test Heritage Museum", culture_names)
        self.assertNotIn("Test Poultry Farm", culture_names)
        self.assertFalse(data["culture"]["pending"])

        cuisine_names = {i["name"] for i in data["cuisine"]["items"]}
        self.assertIn("Test Momo House", cuisine_names)
        self.assertFalse(data["cuisine"]["pending"])

        festival_titles = {i["title"] for i in data["festivals"]["items"]}
        self.assertIn("Test Jatra Festival", festival_titles)
        self.assertFalse(data["festivals"]["pending"])


class AdminDestinationCrudRegressionTests(TestCase):
    """§33: routine destination create/archive must stay inside the custom
    admin API — no raw Django admin, no mass-assignment 500s, soft archive
    that retains related records."""

    def setUp(self):
        from .models import Destination, DestinationAuditLog
        self.Destination = Destination
        self.DestinationAuditLog = DestinationAuditLog
        self.api = APIClient()
        self.admin = make_superuser()

    def test_create_requires_name(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.post("/api/v1/admin/destinations", {"city": "Pokhara"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("name", resp.json()["detail"].lower())
        self.assertFalse(self.Destination.objects.filter(city="Pokhara", name="").exists())

    def test_create_whitelists_fields_and_audits(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.post("/api/v1/admin/destinations", {
            "name": "Harness Viewpoint",
            "district": "Kaski",
            "province": "Gandaki",
            "latitude": "28.2",
            "longitude": "83.9",
            "status": "hacked",      # not creatable -> ignored
            "views_count": 9999,     # not creatable -> ignored
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        dest = self.Destination.objects.get(id=resp.json()["id"])
        self.assertEqual(dest.name, "Harness Viewpoint")
        self.assertTrue(dest.slug)
        self.assertNotEqual(dest.status, "hacked")
        self.assertNotEqual(dest.views_count, 9999)
        self.assertTrue(self.DestinationAuditLog.objects.filter(destination=dest).exists())

    def test_create_rejects_bad_number_without_creating(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.post(
            "/api/v1/admin/destinations",
            {"name": "Bad Coords", "latitude": "abc"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(self.Destination.objects.filter(name="Bad Coords").exists())

    def test_archive_soft_deletes_and_keeps_relations(self):
        from .models import Review
        self.api.force_authenticate(self.admin)
        dest = self.Destination.objects.create(name="Archive Target", slug="archive-target")
        reviewer = User.objects.create_user(email="reviewer@test.local", password="Review!Pass1")
        Review.objects.create(destination=dest, user=reviewer, comment="Loved it")
        resp = self.api.delete(f"/api/v1/admin/destinations/{dest.id}")
        self.assertEqual(resp.status_code, 200)
        dest.refresh_from_db()
        self.assertFalse(dest.is_active)
        self.assertEqual(dest.status, self.Destination.SubmissionStatus.ARCHIVED)
        self.assertEqual(Review.objects.filter(destination=dest).count(), 1)

    def test_anonymous_cannot_create_or_archive(self):
        resp = self.api.post("/api/v1/admin/destinations", {"name": "Anon Place"}, format="json")
        self.assertIn(resp.status_code, (401, 403))


class WardNumberRegressionTests(TestCase):
    """§21 ward tier: the recorded ward_number must round-trip through the
    admin destination API and reject junk without a 500."""

    def setUp(self):
        from .models import Destination
        self.Destination = Destination
        self.api = APIClient()
        self.admin = make_superuser()
        self.dest = Destination.objects.create(
            name="Ward Test Place", slug="ward-test-place",
            province="Bagmati", district="Kathmandu",
            municipality="Kathmandu Metropolitan City",
        )

    def test_put_persists_and_get_returns_ward(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.put(
            f"/api/v1/admin/destinations/{self.dest.id}",
            {"ward_number": "7"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.dest.refresh_from_db()
        self.assertEqual(self.dest.ward_number, 7)
        detail = self.api.get(f"/api/v1/admin/destinations/{self.dest.id}")
        self.assertEqual(detail.json()["ward_number"], 7)

    def test_blank_ward_clears_it(self):
        self.api.force_authenticate(self.admin)
        self.dest.ward_number = 5
        self.dest.save(update_fields=["ward_number"])
        resp = self.api.put(
            f"/api/v1/admin/destinations/{self.dest.id}",
            {"ward_number": ""},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.dest.refresh_from_db()
        self.assertIsNone(self.dest.ward_number)

    def test_junk_ward_is_clean_400(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.put(
            f"/api/v1/admin/destinations/{self.dest.id}",
            {"ward_number": "not-a-number"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ward", resp.json()["detail"].lower())

    def test_create_accepts_ward(self):
        self.api.force_authenticate(self.admin)
        resp = self.api.post(
            "/api/v1/admin/destinations",
            {"name": "Ward Created Place", "ward_number": "12"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        created = self.Destination.objects.get(id=resp.json()["id"])
        self.assertEqual(created.ward_number, 12)


class TokenRefreshContractTests(TestCase):
    """Pins the JWT refresh contract the axios interceptor relies on:
    a valid refresh yields a fresh access AND a rotated refresh (the client
    must persist the rotation because the old token gets blacklisted)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="refresh-user@test.local",
            password="Refresh!Pass123",
            role="TRAVELLER",
        )

    def _obtain(self):
        resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "refresh-user@test.local", "password": "Refresh!Pass123"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        return resp.json()

    def test_valid_refresh_returns_new_access_and_rotated_refresh(self):
        tokens = self._obtain()
        resp = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": tokens["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("access", body)
        self.assertTrue(body["access"])
        # ROTATE_REFRESH_TOKENS=True: a new refresh comes back and differs.
        self.assertIn("refresh", body)
        self.assertNotEqual(body["refresh"], tokens["refresh"])

    def test_used_refresh_token_is_blacklisted_after_rotation(self):
        tokens = self._obtain()
        first = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": tokens["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)
        replay = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": tokens["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(replay.status_code, 401)

    def test_garbage_refresh_rejected_401(self):
        resp = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": "not-a-jwt"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_destinations_list_is_public_read(self):
        resp = self.client.get("/api/v1/destinations/?page=1&limit=12&ordering=name")
        self.assertEqual(resp.status_code, 200)

    def test_destinations_list_rejects_invalid_bearer(self):
        # Documents the sharp edge the client-side interceptor handles: DRF
        # rejects an invalid Authorization header before permission checks.
        resp = self.client.get(
            "/api/v1/destinations/?page=1&limit=12",
            HTTP_AUTHORIZATION="Bearer stale-or-forged-token",
        )
        self.assertEqual(resp.status_code, 401)


class UniversalPlaceEndpointTests(TestCase):
    """Pins the newly-routed universal Navigation endpoints (spec items 2/4/5)."""

    @classmethod
    def setUpTestData(cls):
        from .models import Destination
        cls.dest = Destination.objects.create(
            name="Hupsekot Waterfall",
            slug="hupsekot-waterfall",
            city="Hupsekot",
            district="Nawalpur",
            latitude=27.6500,
            longitude=84.1200,
            is_active=True,
        )

    def test_places_search_finds_recorded_destination(self):
        resp = self.client.get("/api/v1/places/search/", {"q": "Hupsekot Waterfall", "lat": "27.7", "lng": "84.1"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertGreaterEqual(body["count"], 1)
        names = [r.get("name", "").lower() for r in body["results"]]
        self.assertTrue(any("hupsekot" in n for n in names), names[:5])

    def test_places_search_category_intent(self):
        resp = self.client.get("/api/v1/places/search/", {"q": "hospital", "lat": "27.7", "lng": "84.1"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())

    def test_places_nearby_returns_items_and_results(self):
        resp = self.client.get(
            "/api/v1/places/nearby/",
            {"lat": "27.65", "lng": "84.12", "category": "hospital", "radius_km": "50"},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("items", body)
        self.assertIn("results", body)

    def test_places_nearby_caches_repeat_queries(self):
        from django.core.cache import cache
        cache.clear()
        params = {"lat": "27.65001", "lng": "84.12001", "category": "bank", "radius_km": "10"}
        first = self.client.get("/api/v1/places/nearby/", params)
        self.assertEqual(first.status_code, 200)
        second = self.client.get("/api/v1/places/nearby/", params)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())


class NavigationOriginResolutionTests(TestCase):
    """POST /navigation/route must resolve origin_name instead of demanding
    coordinates the frontend used to fake with a default city."""

    @classmethod
    def setUpTestData(cls):
        from .models import Destination
        cls.dest = Destination.objects.create(
            name="Phewa Lake",
            slug="phewa-lake",
            city="Pokhara",
            district="Kaski",
            latitude=28.2117,
            longitude=83.9517,
            is_active=True,
        )
        cls.origin = Destination.objects.create(
            name="Kathmandu Durbar Square",
            slug="kathmandu-durbar-square",
            city="Kathmandu",
            district="Kathmandu",
            latitude=27.6722,
            longitude=85.3066,
            is_active=True,
        )

    def test_origin_name_resolves_without_coordinates(self):
        resp = self.client.post(
            "/api/v1/navigation/route",
            {"origin_name": "Kathmandu Durbar Square", "destination_name": "Phewa Lake"},
            content_type="application/json",
        )
        # 200 when the graph can route; 404 with an honest routing message
        # when it cannot — but never a silent default-city route.
        self.assertIn(resp.status_code, (200, 404, 503))
        if resp.status_code == 404:
            self.assertNotIn("matches origin", resp.json().get("detail", ""))

    def test_unknown_origin_is_a_clean_404(self):
        resp = self.client.post(
            "/api/v1/navigation/route",
            {"origin_name": "zzz-nonexistent-ville", "destination_name": "Phewa Lake"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)
        self.assertIn("origin", resp.json()["detail"].lower())


class TransportModeHonestyTests(TestCase):
    """Spec item 8: modes without real schedule data must not fabricate ETAs."""

    @classmethod
    def setUpTestData(cls):
        from .models import Destination
        cls.origin = Destination.objects.create(
            name="Kathmandu Durbar Square", slug="kds-2", city="Kathmandu",
            latitude=27.6722, longitude=85.3066, is_active=True,
        )
        cls.dest = Destination.objects.create(
            name="Phewa Lake", slug="phewa-2", city="Pokhara",
            latitude=28.2117, longitude=83.9517, is_active=True,
        )

    def _route(self, mode):
        return self.client.post(
            "/api/v1/navigation/route",
            {
                "start_latitude": "27.6722", "start_longitude": "85.3066",
                "destination_name": "Phewa Lake", "transport_mode": mode,
            },
            content_type="application/json",
        )

    def test_tourist_bus_has_no_invented_eta(self):
        resp = self._route("Tourist Bus")
        self.assertIn(resp.status_code, (200, 404, 503))
        if resp.status_code == 200:
            body = resp.json()
            self.assertIsNone(body.get("duration_min"))
            self.assertEqual(body.get("duration_source"), "unavailable")
            self.assertIn("transit", body.get("duration_note", "").lower())

    def test_flight_has_no_invented_schedule(self):
        resp = self._route("Flight")
        self.assertIn(resp.status_code, (200, 404, 503))
        if resp.status_code == 200:
            body = resp.json()
            self.assertIsNone(body.get("duration_min"))
            self.assertEqual(body.get("duration_source"), "unavailable")
            self.assertEqual(body.get("route"), [])
            # Flight distance is the straight line, not the road graph.
            self.assertLess(body.get("distance_km", 9999), 200)

    def test_car_duration_carries_honest_source_label(self):
        resp = self._route("Private Car / Taxi")
        self.assertIn(resp.status_code, (200, 404, 503))
        if resp.status_code == 200 and resp.json().get("duration_min"):
            # Either the routing engine supplied it, or it is a labelled
            # average-speed estimate — never an unexplained number.
            self.assertIn(resp.json().get("duration_source"), ("estimated", "routing_engine"))
            self.assertTrue(resp.json().get("duration_note"))

    def test_walking_never_shows_driving_duration(self):
        resp = self._route("Walking / Trek")
        self.assertIn(resp.status_code, (200, 404, 503))
        if resp.status_code == 200 and resp.json().get("distance_km"):
            body = resp.json()
            self.assertEqual(body.get("duration_source"), "estimated")
            # Trekking pace (3.5 km/h) must dominate: 100+ km route = 1700+ min
            if body["distance_km"] > 100:
                self.assertGreater(body["duration_min"], 1500)


class UserRouteHistoryTests(TestCase):
    """Saved routes + navigation history (spec items 15/16)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="traveler@nepaltourism.com", password="Traveler@12345", role="tourist"
        )
        self.other = User.objects.create_user(
            email="other@nepaltourism.com", password="Traveler@12345", role="tourist"
        )
        self.client = APIClient()

    def _auth(self, user=None):
        self.client.force_authenticate(user or self.user)

    def _payload(self, **over):
        base = {
            "origin_name": "Kathmandu", "origin_latitude": 27.7172, "origin_longitude": 85.3240,
            "destination_name": "Phewa Lake", "destination_latitude": 28.2096, "destination_longitude": 83.9561,
            "transport_mode": "Private Car / Taxi", "distance_km": 253.08,
            "duration_min": 434, "duration_source": "routing_engine",
        }
        base.update(over)
        return base

    def test_requires_auth(self):
        for method, url in [("get", "/api/v1/navigation/routes/"), ("post", "/api/v1/navigation/routes/")]:
            resp = getattr(self.client, method)(url, self._payload() if method == "post" else None,
                                                format="json" if method == "post" else None)
            self.assertIn(resp.status_code, (401, 403))

    def test_log_and_list_own_history_only(self):
        self._auth()
        resp = self.client.post("/api/v1/navigation/routes/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201, resp.content[:200])
        # Another user's private log stays invisible.
        self._auth(self.other)
        self.client.post("/api/v1/navigation/routes/", self._payload(destination_name="Sarangkot"), format="json")
        self._auth()
        resp = self.client.get("/api/v1/navigation/routes/")
        names = [r["destination_name"] for r in resp.json()]
        self.assertEqual(names, ["Phewa Lake"])

    def test_star_saved_filter_and_delete(self):
        self._auth()
        rid = self.client.post("/api/v1/navigation/routes/", self._payload(), format="json").json()["id"]
        self.client.post("/api/v1/navigation/routes/", self._payload(destination_name="Nagarkot"), format="json")
        resp = self.client.patch(f"/api/v1/navigation/routes/{rid}/", {"is_saved": True, "label": "Home → Lakeside"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["label"], "Home → Lakeside")
        saved = self.client.get("/api/v1/navigation/routes/?saved=1").json()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["destination_name"], "Phewa Lake")
        self.assertEqual(self.client.delete(f"/api/v1/navigation/routes/{rid}/").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/navigation/routes/?saved=1").json(), [])

    def test_cannot_touch_other_users_route(self):
        self._auth(self.other)
        rid = self.client.post("/api/v1/navigation/routes/", self._payload(), format="json").json()["id"]
        self._auth()
        self.assertEqual(self.client.patch(f"/api/v1/navigation/routes/{rid}/", {"is_saved": True}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/v1/navigation/routes/{rid}/").status_code, 404)

    def test_destination_name_required(self):
        self._auth()
        resp = self.client.post("/api/v1/navigation/routes/", self._payload(destination_name="  "), format="json")
        self.assertEqual(resp.status_code, 400)


class NavigationAnalyticsTests(TestCase):
    """Admin navigation analytics (spec item 24) — real aggregates only."""

    def setUp(self):
        self.admin = User.objects.create_superuser("analytics-admin@test.local", "Analytics!Pass1")
        self.tourist = User.objects.create_user(email="analytics-tourist@test.local", password="Tourist!Pass1", role="tourist")
        self.client = APIClient()

    def _mk(self, user, dest, mode="Private Car / Taxi", km=100.0, saved=False):
        UserRoute.objects.create(
            user=user, origin_name="Kathmandu", origin_latitude=27.7172, origin_longitude=85.324,
            destination_name=dest, destination_latitude=28.0, destination_longitude=84.0,
            transport_mode=mode, distance_km=km, duration_min=120, duration_source="estimated",
            is_saved=saved,
        )

    def test_requires_admin(self):
        self.assertIn(self.client.get("/api/v1/admin/navigation-analytics/").status_code, (401, 403))
        self.client.force_authenticate(self.tourist)
        self.assertEqual(self.client.get("/api/v1/admin/navigation-analytics/").status_code, 403)

    def test_aggregates_logged_routes(self):
        self._mk(self.tourist, "Phewa Lake", km=200.0)
        self._mk(self.tourist, "Phewa Lake", mode="Motorcycle", km=200.0, saved=True)
        self._mk(self.admin, "Nagarkot", km=30.0)
        self.client.force_authenticate(self.admin)
        resp = self.client.get("/api/v1/admin/navigation-analytics/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_calculations"], 3)
        self.assertEqual(data["distinct_travellers"], 2)
        self.assertEqual(data["saved_routes"], 1)
        self.assertEqual(data["average_distance_km"], 143.3)  # (200+200+30)/3
        top = {row["destination_name"]: row["calculations"] for row in data["top_destinations"]}
        self.assertEqual(top, {"Phewa Lake": 2, "Nagarkot": 1})
        modes = {row["transport_mode"]: row["calculations"] for row in data["mode_split"]}
        self.assertEqual(modes, {"Private Car / Taxi": 2, "Motorcycle": 1})
        self.assertEqual(data["calculations_last_30_days"], 3)

    def test_empty_database_reports_honest_zeros(self):
        self.client.force_authenticate(self.admin)
        data = self.client.get("/api/v1/admin/navigation-analytics/").json()
        self.assertEqual(data["total_calculations"], 0)
        self.assertIsNone(data["average_distance_km"])  # never a fabricated 0-distance claim
        self.assertEqual(data["top_destinations"], [])


class SearchPlacesCategoryRadiusTests(TestCase):
    """Nearby category filters must return that category, inside the radius.

    Regression for two live bugs: plural tab ids ('hospitals') skipped the
    curated provider branches and dumped 30 arbitrary destinations instead,
    and radius_km was accepted but never applied (results 200+ km away).
    """

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="Nature", slug="nature-spr")
        Destination.objects.create(
            name="Far Away Temple", slug="far-away-temple", category=cls.cat,
            city="Dhangadhi", district="Kailali", province="Sudurpashchim",
            latitude=28.7, longitude=80.6,  # ~500 km west of Kathmandu
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        ktm = Destination.objects.create(
            name="Kathmandu Core", slug="kathmandu-core-spr", category=cls.cat,
            city="Kathmandu", district="Kathmandu", province="Bagmati",
            latitude=27.7172, longitude=85.324,
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        cls.hosp = Hospital.objects.create(
            destination=ktm, name="Test City Hospital", address="Kathmandu", phone="102",
            latitude=27.71, longitude=85.33,
        )

    def test_plural_hospitals_returns_only_hospitals(self):
        results = LocationSearchService.search_places(
            user_lat=27.7172, user_lng=85.324, category="hospitals", radius_km=25, limit=30
        )
        self.assertTrue(results, "expected hospital results near Kathmandu")
        for r in results:
            self.assertEqual(r["category"], "Hospital", f"non-hospital leaked: {r['name']} ({r['category']})")

    def test_radius_is_applied(self):
        results = LocationSearchService.search_places(
            user_lat=27.7172, user_lng=85.324, category="", radius_km=25, limit=30, query="temple"
        )
        for r in results:
            self.assertLessEqual(r["distance_km"], 25.0, f"{r['name']} at {r['distance_km']} km exceeds radius")

    def test_unknown_category_returns_empty_not_random_destinations(self):
        results = LocationSearchService.search_places(
            user_lat=27.7172, user_lng=85.324, category="unicorn_stables", radius_km=25, limit=30
        )
        self.assertEqual(results, [])

    def test_hotels_plural_maps_to_curated_hotels(self):
        ktm = Destination.objects.get(slug="kathmandu-core-spr")
        Hotel.objects.create(destination=ktm, name="Test Kathmandu Hotel", address="Kathmandu", latitude=27.71, longitude=85.32, is_active=True)
        results = LocationSearchService.search_places(
            user_lat=27.7172, user_lng=85.324, category="hotels", radius_km=25, limit=30
        )
        self.assertTrue(results)
        for r in results:
            self.assertEqual(r["category"], "Hotel & Lodge")


class SearchPlacesRadiusSliceTests(TestCase):
    """A place inside the radius must be found even when many out-of-radius
    rows occupy the queryset slice (live bug: hotels near Pokhara -> 0)."""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="City", slug="city-slice")
        hub = Destination.objects.create(
            name="Pokhara Hub", slug="pokhara-hub-slice", category=cls.cat,
            city="Pokhara", district="Kaski", province="Gandaki",
            latitude=28.2096, longitude=83.9856,
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        # 25 far-away hotels fill any naive [:20] slice
        far = Destination.objects.create(
            name="Far Hub", slug="far-hub-slice", category=cls.cat,
            city="Dhangadhi", district="Kailali", province="Sudurpashchim",
            latitude=28.7, longitude=80.6,
            is_active=True, status=Destination.SubmissionStatus.APPROVED,
        )
        for i in range(25):
            Hotel.objects.create(
                destination=far, name=f"Far Hotel {i}", address="Kailali",
                latitude=28.7 + i * 0.001, longitude=80.6, is_active=True,
            )
        Hotel.objects.create(
            destination=hub, name="Lakeside Pokhara Hotel", address="Lakeside",
            latitude=28.2080, longitude=83.9580, is_active=True,
        )

    def test_hotel_inside_radius_found_despite_far_slice_fillers(self):
        results = LocationSearchService.search_places(
            user_lat=28.2096, user_lng=83.9856, category="hotels", radius_km=25, limit=40
        )
        names = [r["name"] for r in results]
        self.assertIn("Lakeside Pokhara Hotel", names)
        for r in results:
            self.assertLessEqual(r["distance_km"], 25.0)


class ChatbotNavigationWiringTests(TestCase):
    """The assistant must answer distance questions from the navigation
    service — never from a hardcoded table or an LLM's imagination."""

    def test_distance_answer_uses_routing_engine_not_hardcoded_table(self):
        from chatbot.services import get_chatbot_reply
        result = get_chatbot_reply([{"role": "user", "content": "How far is Pokhara from Kathmandu?"}])
        reply = result["reply"]
        card = result.get("distance_cards")
        # The old implementation hardcoded 204.5 km / "6 – 7 hours" for this
        # exact pair — those fabricated values must never appear again.
        self.assertNotIn("204.5", reply)
        self.assertNotIn("6 – 7 hours", reply)
        self.assertNotIn("Domestic Flight Time", reply)
        self.assertIn("Pokhara", reply)
        self.assertIn("Kathmandu", reply)
        # A real road distance with a labelled source (engine reachable in CI
        # via the bundled GraphML), or an explicit unavailability statement.
        self.assertTrue(
            ("Road Distance:** `2" in reply or "Information unavailable" in reply),
            reply[:400],
        )

    def test_unresolvable_place_gets_honest_answer(self):
        from chatbot.services import get_chatbot_reply
        result = get_chatbot_reply([{"role": "user", "content": "How far is Xylophonia from Kathmandu?"}])
        reply = result["reply"]
        self.assertIn("could not find recorded coordinates", reply)
        self.assertNotIn("Road Distance", reply)

    def test_compute_distance_card_fields(self):
        from chatbot.services import compute_distance_and_transit
        card = compute_distance_and_transit("Kathmandu", "Pokhara")
        self.assertEqual(card["status"], "ok")
        self.assertIsNotNone(card["straight_distance_km"])
        # Straight-line KTM->Pokhara is ~146 km; a real road route is longer.
        self.assertGreater(card["straight_distance_km"], 100)
        if card["road_distance_km"] is not None:
            self.assertGreaterEqual(card["road_distance_km"], card["straight_distance_km"])
            self.assertIn(card["duration_source"], ("routing_engine", "estimated"))
        else:
            self.assertEqual(card["duration_source"], "unavailable")
        self.assertIsNone(card["flight_time"])  # fabricated flight times are gone


class StaffTaskWorkflowTests(TestCase):
    """Assignment-driven staff workflow (Staff Ops spec §29): admin assigns →
    staff starts → submits for review → admin approves, with notifications,
    audit entries, and IDOR guards at every step."""

    def setUp(self):
        self.admin = User.objects.create_superuser("ops-admin@test.local", "Ops!Pass123")
        self.staff = User.objects.create_user(email="ops-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.other_staff = User.objects.create_user(email="ops-other@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.client = APIClient()

    def _task(self, **over):
        from admin_panel.models import AdminTask
        defaults = dict(title="Verify Pokhara hotel information", description="Check facilities",
                        assigned_to=self.staff, assigned_by=self.admin, priority="high")
        defaults.update(over)
        return AdminTask.objects.create(**defaults)

    def _act(self, task, action, note="", as_user=None):
        self.client.force_authenticate(as_user or self.staff)
        return self.client.post(f"/api/v1/admin-panel/tasks/{task.id}/action/",
                                {"action": action, "note": note}, format="json")

    def test_full_assignment_workflow(self):
        from admin_panel.models import AdminTask
        self.client.force_authenticate(self.admin)
        resp = self.client.post("/api/v1/admin-panel/tasks/", {
            "title": "Verify Pokhara hotel information", "description": "Check facilities",
            "assigned_to": self.staff.id, "priority": "high",
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content[:200])
        task = AdminTask.objects.get(pk=resp.json()["id"])
        # assignment notification went to the staff member
        self.assertTrue(self.staff.notifications.filter(title="New task assigned").exists())

        # staff starts
        r = self._act(task, "start")
        self.assertEqual(r.status_code, 200, r.content[:200])
        task.refresh_from_db()
        self.assertEqual(task.status, "in_progress")
        self.assertIsNotNone(task.started_at)

        # completion requires a note
        r = self._act(task, "complete")
        self.assertEqual(r.status_code, 400)

        # submit for review instead → admin approves
        r = self._act(task, "submit_review", "Updated description and facilities")
        self.assertEqual(r.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "in_review")
        self.assertTrue(self.admin.notifications.filter(title__icontains="submit review").exists())

        r = self._act(task, "approve", "Looks good", as_user=self.admin)
        self.assertEqual(r.status_code, 200, r.content[:200])
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.reviewed_by, self.admin)
        self.assertTrue(self.staff.notifications.filter(title__icontains="approved").exists())

        # audited
        from audit.models import AuditLog
        actions = set(AuditLog.objects.filter(object_type="AdminTask", object_id=str(task.id)).values_list("action", flat=True))
        self.assertIn("task.assign", actions)
        self.assertIn("task.start", actions)
        self.assertIn("task.approve", actions)

    def test_reject_returns_to_in_progress_with_reason(self):
        task = self._task(status="in_review")
        r = self._act(task, "reject", "Facility list incomplete", as_user=self.admin)
        self.assertEqual(r.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "in_progress")
        self.assertEqual(task.review_note, "Facility list incomplete")
        self.assertTrue(self.staff.notifications.filter(title__icontains="rejected").exists())

    def test_idor_staff_cannot_act_on_others_tasks(self):
        task = self._task()  # assigned to self.staff
        r = self._act(task, "start", as_user=self.other_staff)
        self.assertEqual(r.status_code, 403)
        # staff cannot approve their own submission
        task2 = self._task(status="in_review")
        r = self._act(task2, "approve", as_user=self.staff)
        self.assertEqual(r.status_code, 403)

    def test_block_and_escalate(self):
        task = self._task()
        self._act(task, "start")
        r = self._act(task, "block", "Hotel contact unreachable")
        self.assertEqual(r.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "blocked")
        r = self._act(task, "escalate", "Need supervisor to call owner")
        self.assertEqual(r.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.is_escalated)
        self.assertEqual(task.escalation_reason, "Need supervisor to call owner")
        self.assertTrue(self.admin.notifications.filter(title__icontains="escalate").exists())

    def test_performance_endpoint(self):
        task = self._task()
        self._act(task, "start")
        self._act(task, "complete", "Done and verified")
        self.client.force_authenticate(self.staff)
        data = self.client.get("/api/v1/admin-panel/my-performance/").json()
        self.assertEqual(data["tasks_completed"], 1)
        self.assertEqual(data["on_time_rate"], 100.0)
        self.assertEqual(data["tasks_total"], 1)


class SupportTicketWorkflowTests(TestCase):
    """Staff-scoped customer support center (Staff Ops spec §7-10)."""

    def setUp(self):
        self.admin = User.objects.create_superuser("sup-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="sup-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.other = User.objects.create_user(email="sup-other@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.customer = User.objects.create_user(email="sup-customer@test.local", password="Cust!Pass123", role="tourist")
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"feedback": ["view", "change"], "dashboard": ["view"]})
        StaffCapabilityProfile.objects.create(user=self.other, capabilities={"feedback": ["view", "change"], "dashboard": ["view"]})
        self.client = APIClient()
        from tourist.models import UserFeedback
        self.ticket = UserFeedback.objects.create(
            user=self.customer, subject="Cannot find my hotel booking", message="Booking BK10291 is missing.",
            category="booking", priority="high",
        )

    def _list(self, as_user):
        self.client.force_authenticate(as_user)
        return self.client.get("/api/v1/admin-panel/support/tickets/")

    def _action(self, ticket, action, note="", as_user=None):
        self.client.force_authenticate(as_user or self.staff)
        return self.client.post(f"/api/v1/admin-panel/support/tickets/{ticket.id}/action/",
                                {"action": action, "note": note}, format="json")

    def test_staff_see_only_assigned_and_unassigned(self):
        from tourist.models import UserFeedback
        UserFeedback.objects.create(user=self.customer, subject="Other staff ticket", message="x", assigned_to=self.other)
        data = self._list(self.staff).json()
        subjects = {row["subject"] for row in data["results"]}
        self.assertIn("Cannot find my hotel booking", subjects)      # unassigned pool
        self.assertNotIn("Other staff ticket", subjects)             # another staffer's ticket
        admin_subjects = {row["subject"] for row in self._list(self.admin).json()["results"]}
        self.assertIn("Other staff ticket", admin_subjects)          # admin sees all

    def test_capability_required(self):
        plain = User.objects.create_user(email="sup-noperm@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        resp = self._list(plain)
        self.assertEqual(resp.status_code, 403)

    def test_claim_then_resolve_flow(self):
        r = self._action(self.ticket, "claim")
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.staff)
        self.assertEqual(self.ticket.status, "in_progress")
        # second claim fails
        self.assertEqual(self._action(self.ticket, "claim", as_user=self.other).status_code, 400)
        # other staff cannot act on it
        self.assertEqual(self._action(self.ticket, "resolve", as_user=self.other).status_code, 400)
        r = self._action(self.ticket, "resolve", "Your booking is confirmed — see email.")
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "resolved")
        self.assertIsNotNone(self.ticket.closed_at)
        self.assertTrue(self.customer.notifications.filter(title__startswith="Resolved:").exists())
        from audit.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(object_type="UserFeedback", action="support.resolve").exists())

    def test_escalation_requires_reason_and_notifies_admins(self):
        self._action(self.ticket, "claim")
        self.assertEqual(self._action(self.ticket, "escalate").status_code, 400)
        r = self._action(self.ticket, "escalate", "Payment refund needed — finance must act.")
        self.assertEqual(r.status_code, 200, r.content[:200])
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_escalated)
        self.assertTrue(self.ticket.messages.filter(is_internal=True, body__contains="[Escalated]").exists())
        self.assertTrue(self.admin.notifications.filter(title__startswith="Escalated ticket:").exists())
        escalated = self.client.get("/api/v1/admin-panel/support/tickets/?status=escalated")
        self.assertEqual(escalated.status_code, 200)

    def test_customer_reply_notifies_assigned_staff(self):
        self._action(self.ticket, "claim")
        self.client.force_authenticate(self.customer)
        r = self.client.post(f"/api/v1/feedback/{self.ticket.id}/message", {"message": "Any update?"}, format="json")
        self.assertEqual(r.status_code, 201, r.content[:200])
        self.assertTrue(self.staff.notifications.filter(title__startswith="Customer replied:").exists())
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.is_escalated)  # fresh reply de-escalates

class HotelBookingScopeTests(TestCase):
    """Staff see only assigned hotels + their bookings (Staff Ops spec §11-12)."""

    def setUp(self):
        from tourist.models import Destination, Hotel
        from admin_panel.models import HotelAssignment
        from booking.models import Booking
        self.admin = User.objects.create_superuser("hb-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="hb-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"hotels": ["view", "change"], "dashboard": ["view"]})
        self.customer = User.objects.create_user(email="hb-customer@test.local", password="Cust!Pass123", role="tourist")
        self.dest = Destination.objects.create(name="Pokhara", slug="pokhara-hb", latitude=28.2, longitude=83.9)
        self.mine = Hotel.objects.create(destination=self.dest, name="My Assigned Lodge", address="Lakeside")
        self.theirs = Hotel.objects.create(destination=self.dest, name="Unassigned Grand", address="Mahendrapool")
        HotelAssignment.objects.create(hotel=self.mine, admin=self.staff)
        self.my_booking = Booking.objects.create(user=self.customer, hotel=self.mine, check_in="2026-10-01", check_out="2026-10-03", guests=2)
        self.other_booking = Booking.objects.create(user=self.customer, hotel=self.theirs, check_in="2026-10-01", check_out="2026-10-02", guests=1)
        self.client = APIClient()

    def _list(self, as_user):
        self.client.force_authenticate(as_user)
        return self.client.get("/api/v1/admin-panel/my-bookings/")

    def test_staff_see_only_assigned_hotel_bookings(self):
        data = self._list(self.staff).json()
        ids = {row["id"] for row in data["results"]}
        self.assertEqual(ids, {self.my_booking.id})
        self.assertEqual(data["counts"]["pending"], 1)
        admin_ids = {row["id"] for row in self._list(self.admin).json()["results"]}
        self.assertEqual(admin_ids, {self.my_booking.id, self.other_booking.id})

    def test_capability_required(self):
        plain = User.objects.create_user(email="hb-noperm@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.assertEqual(self._list(plain).status_code, 403)
        self.client.force_authenticate(plain)
        resp = self.client.post(f"/api/v1/admin-panel/my-bookings/{self.my_booking.id}/action/", {"action": "confirm"}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_out_of_scope_booking_denied(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/admin-panel/my-bookings/{self.other_booking.id}/action/", {"action": "confirm"}, format="json")
        self.assertEqual(resp.status_code, 403)
        self.other_booking.refresh_from_db()
        self.assertEqual(self.other_booking.status, "pending")

    def test_confirm_notifies_and_audits(self):
        from tourist.models import Notification
        from audit.models import AuditLog
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/admin-panel/my-bookings/{self.my_booking.id}/action/",
                                {"action": "confirm"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "confirmed")
        self.my_booking.refresh_from_db()
        self.assertEqual(self.my_booking.status, "confirmed")
        self.assertTrue(Notification.objects.filter(user=self.customer, title="Booking confirmed").exists())
        self.assertTrue(AuditLog.objects.filter(action="booking.confirm").exists())

    def test_unknown_action_rejected(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/admin-panel/my-bookings/{self.my_booking.id}/action/",
                                {"action": "refund"}, format="json")
        self.assertEqual(resp.status_code, 400)


class DataEntryPipelineTests(TestCase):
    """Destination data entry DRAFT → SUBMITTED → REVIEW → APPROVED (spec §13-14)."""

    def setUp(self):
        self.admin = User.objects.create_superuser("de-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="de-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={
            "destinations": ["view", "add", "change"], "dashboard": ["view"]})
        self.client = APIClient()

    def _post(self, url, payload, as_user):
        self.client.force_authenticate(as_user)
        return self.client.post(url, payload, format="json")

    def test_staff_creates_and_submits_draft(self):
        from tourist.models import Notification
        resp = self._post("/api/v1/admin-panel/data-entry/",
                          {"name": "Tilicho Lake Trek", "district": "Manang", "short_description": "High-altitude lake trek"},
                          self.staff)
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertEqual(body["status"], "draft")
        self.assertEqual(body["submitted_by"], "de-staff@test.local")
        resp = self._post(f"/api/v1/admin-panel/data-entry/{body['id']}/action/", {"action": "submit"}, self.staff)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "submitted")
        self.assertTrue(Notification.objects.filter(user=self.admin, title="Destination awaiting review").exists())

    def test_staff_cannot_self_approve(self):
        from tourist.models import Destination
        d = Destination.objects.create(name="Self Approve Test", status="submitted", submitted_by=self.staff)
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/admin-panel/data-entry/{d.id}/action/", {"action": "approve"}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_admin_approve_notifies_and_audits(self):
        from tourist.models import Destination, DestinationAuditLog, Notification
        d = Destination.objects.create(name="Approve Me", status="submitted", submitted_by=self.staff)
        resp = self._post(f"/api/v1/admin-panel/data-entry/{d.id}/action/", {"action": "approve", "note": "Great entry"}, self.admin)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "approved")
        self.assertTrue(DestinationAuditLog.objects.filter(destination=d, action="approved", actor=self.admin).exists())
        self.assertTrue(Notification.objects.filter(user=self.staff, title__contains="approved").exists())

    def test_reject_requires_note(self):
        from tourist.models import Destination
        d = Destination.objects.create(name="Reject Me", status="submitted", submitted_by=self.staff)
        resp = self._post(f"/api/v1/admin-panel/data-entry/{d.id}/action/", {"action": "reject"}, self.admin)
        self.assertEqual(resp.status_code, 400)
        resp = self._post(f"/api/v1/admin-panel/data-entry/{d.id}/action/", {"action": "reject", "note": "Add coordinates"}, self.admin)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "rejected")
        self.assertEqual(resp.json()["review_note"], "Add coordinates")

    def test_staff_sees_only_own_entries(self):
        from tourist.models import Destination
        Destination.objects.create(name="My Draft", status="draft", submitted_by=self.staff)
        Destination.objects.create(name="Other Draft", status="draft")
        self.client.force_authenticate(self.staff)
        names = {row["name"] for row in self.client.get("/api/v1/admin-panel/data-entry/").json()["results"]}
        self.assertIn("My Draft", names)
        self.assertNotIn("Other Draft", names)


class MediaQueueTests(TestCase):
    """Destination image review queue (spec §15)."""

    def setUp(self):
        from tourist.models import Destination
        self.admin = User.objects.create_superuser("mq-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="mq-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"images": ["view", "add"], "dashboard": ["view"]})
        self.dest = Destination.objects.create(name="Media Test Dest", slug="media-test-dest", latitude=27.7, longitude=85.3)
        self.client = APIClient()

    def test_staff_upload_lands_pending(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.post("/api/v1/admin-panel/media/",
                                {"destination": self.dest.id, "external_url": "https://example.com/a.jpg", "caption": "Sunrise"},
                                format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["status"], "pending")

    def test_approve_requires_capability(self):
        from tourist.models import DestinationImage
        img = DestinationImage.objects.create(destination=self.dest, external_url="https://example.com/b.jpg", verification_status="pending")
        self.client.force_authenticate(self.staff)  # only images view+add
        resp = self.client.post(f"/api/v1/admin-panel/media/{img.id}/action/", {"action": "approve"}, format="json")
        self.assertEqual(resp.status_code, 403)
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f"/api/v1/admin-panel/media/{img.id}/action/", {"action": "approve"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "approved")

    def test_reject_audited(self):
        from audit.models import AuditLog
        from tourist.models import DestinationImage
        img = DestinationImage.objects.create(destination=self.dest, external_url="https://example.com/c.jpg", verification_status="pending")
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f"/api/v1/admin-panel/media/{img.id}/action/", {"action": "reject"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "rejected")
        self.assertTrue(AuditLog.objects.filter(action="image.reject").exists())


class SafetyOpsTests(TestCase):
    """Unified safety queue over Alert / CurrentHazard / DataReport (spec §16)."""

    def setUp(self):
        from tourist.models import Alert, CurrentHazard, DataReport, Destination
        self.admin = User.objects.create_superuser("so-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="so-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"safety": ["view", "change"], "dashboard": ["view"]})
        self.reporter = User.objects.create_user(email="so-reporter@test.local", password="Tour!Pass123", role="tourist")
        self.dest = Destination.objects.create(name="Safety Test Dest", slug="safety-test-dest", latitude=27.8, longitude=85.4)
        self.alert = Alert.objects.create(alert_type="weather", title="Heavy rain warning", description="Landslide risk", severity="high", city="Pokhara")
        self.hazard = CurrentHazard.objects.create(destination=self.dest, hazard_type="landslide", title="Trail blocked", source_name="Local police", observed_at=timezone.now())
        self.report = DataReport.objects.create(user=self.reporter, destination=self.dest, report_type="safety", severity="high", description="Wrong emergency number shown")
        self.client = APIClient()

    def test_capability_required(self):
        plain = User.objects.create_user(email="so-noperm@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.client.force_authenticate(plain)
        self.assertEqual(self.client.get("/api/v1/admin-panel/safety/").status_code, 403)

    def test_staff_queue_has_all_sections(self):
        self.client.force_authenticate(self.staff)
        data = self.client.get("/api/v1/admin-panel/safety/").json()
        self.assertEqual(data["counts"]["active_alerts"], 1)
        self.assertEqual(data["counts"]["unverified_alerts"], 1)
        self.assertEqual(data["counts"]["active_hazards"], 1)
        self.assertEqual(data["counts"]["open_reports"], 1)
        self.assertEqual(data["alerts"][0]["title"], "Heavy rain warning")
        self.assertEqual(data["hazards"][0]["title"], "Trail blocked")
        self.assertEqual(data["reports"][0]["reporter"], "so-reporter@test.local")

    def test_verify_alert_and_fix_report(self):
        from audit.models import AuditLog
        from tourist.models import DataReport
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/admin-panel/safety/alert/{self.alert.id}/action/", {"action": "verify"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.is_verified)
        resp = self.client.post(f"/api/v1/admin-panel/safety/report/{self.report.id}/action/", {"action": "fix"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, DataReport.Status.FIXED)
        self.assertEqual(self.report.resolved_by, self.staff)
        self.assertTrue(AuditLog.objects.filter(action="safety.alert.verify").exists())
        self.assertTrue(AuditLog.objects.filter(action="safety.report.fix").exists())

    def test_report_reject_requires_note_and_unknown_kind_400(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/admin-panel/safety/report/{self.report.id}/action/", {"action": "reject"}, format="json")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(f"/api/v1/admin-panel/safety/report/{self.report.id}/action/", {"action": "reject", "note": "Already correct"}, format="json")
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(f"/api/v1/admin-panel/safety/bridge/1/action/", {"action": "verify"}, format="json")
        self.assertEqual(resp.status_code, 400)


class NavigationExtensionsTests(TestCase):
    """Route options, saved-route recalculation and province navigation."""

    def setUp(self):
        from tourist.models import UserRoute
        self.owner = User.objects.create_user(email="nav-owner@test.local", password="Nav!Pass123", role="tourist")
        self.other = User.objects.create_user(email="nav-other@test.local", password="Nav!Pass123", role="tourist")
        self.route = UserRoute.objects.create(
            user=self.owner, origin_name="Kathmandu", origin_latitude=27.7172, origin_longitude=85.3240,
            destination_name="Pokhara", destination_latitude=28.2096, destination_longitude=83.9856,
            transport_mode="Private Car / Taxi", distance_km=150.0, duration_min=300, duration_source="estimated",
        )
        self.client = APIClient()

    def test_route_options_requires_coordinates(self):
        resp = self.client.post("/api/v1/navigation/route-options/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_route_options_honest_when_no_road_service(self):
        resp = self.client.post("/api/v1/navigation/route-options/", {
            "origin_lat": 27.7172, "origin_lng": 85.3240, "dest_lat": 28.2096, "dest_lng": 83.9856,
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["primary"]["status"], {"routed", "graph_routed", "routing_unconfigured", "routing_unavailable"})
        # No fabricated alternatives: list is empty unless a real service returned them
        self.assertIsInstance(data["alternatives"], list)
        self.assertTrue(data["alternatives_note"])
        if data["primary"]["status"] == "routing_unconfigured":
            self.assertEqual(data["alternatives"], [])
            self.assertIsNone(data["primary"]["route_distance_km"])

    def test_recalculate_owner_only(self):
        self.client.force_authenticate(self.other)
        resp = self.client.post(f"/api/v1/navigation/routes/{self.route.id}/recalculate/")
        self.assertEqual(resp.status_code, 404)  # not the owner → not found
        self.client.force_authenticate(self.owner)
        resp = self.client.post(f"/api/v1/navigation/routes/{self.route.id}/recalculate/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["previous"]["duration_source"], "estimated")
        self.assertIn(data["routing_status"], {"routed", "graph_routed", "routing_unconfigured", "routing_unavailable"})
        # stale estimate must never survive a failed recalculation
        if data["routing_status"] in {"routing_unconfigured", "routing_unavailable"}:
            self.assertIsNone(data["current"]["duration_min"])
            self.assertEqual(data["current"]["duration_source"], "unavailable")

    def test_provinces_payload(self):
        from tourist.models import Destination
        Destination.objects.create(name="Swayambhunath", slug="nav-swayambhunath", province="Bagmati Province",
                                   latitude=27.7149, longitude=85.2904, status="approved")
        resp = self.client.get("/api/v1/navigation/provinces/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 7)
        bagmati = next(p for p in data["results"] if p["name"] == "Bagmati Province")
        self.assertGreaterEqual(bagmati["destination_count"], 1)
        self.assertIn("Swayambhunath", [d["name"] for d in bagmati["featured"]])

    def test_unified_aliases_reachable(self):
        # the same views answer under the unified /navigation/ prefix
        resp = self.client.get("/api/v1/navigation/places/search/", {"q": "Kathmandu"})
        self.assertIn(resp.status_code, {200, 400})
        resp = self.client.get("/api/v1/navigation/provinces/")
        self.assertEqual(resp.status_code, 200)


class StaffPermissionLockdownTests(TestCase):
    """Spec §36 hard rule: staff can never change their own permissions."""

    def setUp(self):
        self.staff = User.objects.create_user(email="lock-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"feedback": ["view"], "dashboard": ["view"]})
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

    def test_staff_cannot_update_capability_profiles(self):
        resp = self.client.put("/api/v1/admin/staff-capabilities/", {
            "user_id": self.staff.id,
            "capabilities": {"users": ["view", "change", "delete"], "settings": ["change"]},
        }, format="json")
        self.assertEqual(resp.status_code, 403)
        self.staff.capability_profile.refresh_from_db()
        self.assertEqual(self.staff.capability_profile.capabilities, {"feedback": ["view"], "dashboard": ["view"]})

    def test_staff_cannot_list_capability_profiles(self):
        self.assertEqual(self.client.get("/api/v1/admin/staff-capabilities/").status_code, 403)

    def test_profile_patch_cannot_escalate_role(self):
        resp = self.client.patch("/api/v1/auth/profile/", {
            "role": "admin", "is_staff": False, "is_superuser": True, "is_verified": True,
            "first_name": "Renamed",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, "staff")          # unchanged
        self.assertTrue(self.staff.is_staff)                 # unchanged
        self.assertFalse(self.staff.is_superuser)            # unchanged
        self.assertFalse(self.staff.is_verified)             # unchanged
        self.assertEqual(self.staff.first_name, "Renamed")   # benign field still works

    def test_registration_cannot_self_assign_admin_role(self):
        self.client.force_authenticate(None)
        base = {"password": "Esc!Pass12345", "password_confirm": "Esc!Pass12345",
                "first_name": "Esc", "last_name": "Alator"}
        # 1) privileged role names are rejected outright at signup
        resp = self.client.post("/api/v1/auth/register/", {**base, "email": "lock-esc@test.local", "role": "admin"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.filter(email="lock-esc@test.local").exists())
        # 2) a normal signup lands on the tourist role
        resp = self.client.post("/api/v1/auth/register/", {**base, "email": "lock-ok@test.local"}, format="json")
        self.assertIn(resp.status_code, {200, 201})
        self.assertEqual(User.objects.get(email="lock-ok@test.local").role, "tourist")


class CuratedRouteVerifyTests(TestCase):
    """Curated transit routes: deliberate verify + engine recalculate (nav spec)."""

    def setUp(self):
        from tourist.models import Destination, DestinationTransitRoute
        self.admin = User.objects.create_superuser("tr-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="tr-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.dest = Destination.objects.create(name="Transit Dest", slug="transit-dest", latitude=28.2096, longitude=83.9856)
        self.route = DestinationTransitRoute.objects.create(
            destination=self.dest, origin="Kathmandu (Kalanki)",
            origin_latitude=27.7172, origin_longitude=85.3240,
            destination_latitude=28.2096, destination_longitude=83.9856,
            transport_mode="Tourist Bus", distance_km=999.0, approx_duration="20 hours",
            confidence_level="ESTIMATED",
        )
        self.no_coords = DestinationTransitRoute.objects.create(
            destination=self.dest, origin="Somewhere", transport_mode="Local Jeep (4WD)",
            distance_km=42.0, confidence_level="ESTIMATED",
        )
        self.client = APIClient()

    def test_anonymous_cannot_verify(self):
        resp = self.client.post(f"/api/v1/transit-routes/{self.route.id}/verify/")
        self.assertEqual(resp.status_code, 401)

    def test_staff_without_capability_cannot_verify(self):
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"dashboard": ["view"]})
        self.client.force_authenticate(self.staff)
        resp = self.client.post(f"/api/v1/transit-routes/{self.route.id}/verify/")
        self.assertEqual(resp.status_code, 403)

    def test_admin_verify_stamps_provenance(self):
        from audit.models import AuditLog
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f"/api/v1/transit-routes/{self.route.id}/verify/")
        self.assertEqual(resp.status_code, 200)
        self.route.refresh_from_db()
        self.assertTrue(self.route.is_verified)
        self.assertIsNotNone(self.route.verified_at)
        self.assertEqual(self.route.confidence_level, "ADMIN_VERIFIED")
        self.assertTrue(AuditLog.objects.filter(action="transit.verify").exists())

    def test_recalculate_uses_engine_and_clears_verification(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f"/api/v1/transit-routes/{self.route.id}/recalculate/")
        if resp.status_code == 200:
            data = resp.json()
            self.assertIn(data["routing_status"], {"routed", "graph_routed"})
            self.route.refresh_from_db()
            self.assertEqual(self.route.confidence_level, "CALCULATED")
            self.assertFalse(self.route.is_verified)          # engine output needs a human verify again
            self.assertNotEqual(float(self.route.distance_km), 999.0)  # stale manual value replaced
            self.assertEqual(data["previous"]["confidence_level"], "ESTIMATED")
        else:
            # Engine unavailable here: stored value must be untouched, honest 503
            self.assertEqual(resp.status_code, 503)
            self.route.refresh_from_db()
            self.assertEqual(float(self.route.distance_km), 999.0)

    def test_recalculate_without_coordinates_is_honest_400(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f"/api/v1/transit-routes/{self.no_coords.id}/recalculate/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("unavailable", resp.json()["detail"].lower())
        self.no_coords.refresh_from_db()
        self.assertEqual(float(self.no_coords.distance_km), 42.0)


class WorkforceGuideTests(TestCase):
    """Tourism workforce: guide profiles, applications, verification center (spec §2/§3/§10/§11)."""

    def setUp(self):
        from tourist.models import GuideProfile
        self.admin = User.objects.create_superuser("wf-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="wf-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"marketplace": ["view", "change"]})
        self.applicant = User.objects.create_user(email="wf-guide@test.local", password="Guide!Pass123", role="tourist", first_name="Pemba", last_name="Sherpa")
        self.tourist = User.objects.create_user(email="wf-tourist@test.local", password="Tour!Pass123", role="tourist")
        self.verified = GuideProfile.objects.create(
            user=User.objects.create_user(email="wf-pro@test.local", password="Guide!Pass123", role="guide", first_name="Pro", last_name="Guide"),
            headline="Everest region specialist", languages=["Nepali", "English"], regions=["Solukhumbu"],
            base_city="Namche", verification_status="verified",
        )
        self.client = APIClient()

    def _apply(self, payload=None):
        self.client.force_authenticate(self.applicant)
        return self.client.post("/api/v1/workforce/guide-applications/", payload or {
            "full_name": "Pemba Sherpa", "experience_summary": "12 years trekking in Khumbu",
            "languages": ["Nepali", "English"], "skills": ["trekking", "high-altitude"],
            "destinations_covered": ["Everest Base Camp"], "base_city": "Namche",
            "license_info": "MoCTCA 1234", "expected_daily_rate_npr": 4500,
        }, format="json")

    def test_directory_shows_only_verified_public_guides(self):
        from tourist.models import GuideProfile
        GuideProfile.objects.create(user=self.applicant, verification_status="pending")
        resp = self.client.get("/api/v1/workforce/guides/")
        self.assertEqual(resp.status_code, 200)
        names = [row["name"] for row in resp.json()["results"]]
        self.assertIn("Pro Guide", names)
        self.assertNotIn("Pemba Sherpa", names)  # unverified never listed

    def test_application_flow_and_duplicate_guard(self):
        from tourist.models import Notification
        resp = self._apply()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["status"], "applied")
        self.assertTrue(Notification.objects.filter(user=self.admin, title="New guide application").exists())
        dup = self._apply()
        self.assertEqual(dup.status_code, 400)

    def test_admin_queue_requires_capability(self):
        plain = User.objects.create_user(email="wf-noperm@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.client.force_authenticate(plain)
        self.assertEqual(self.client.get("/api/v1/workforce/admin/applications/").status_code, 403)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get("/api/v1/workforce/admin/applications/").status_code, 200)

    def test_full_verification_flow_approves_and_provisions_profile(self):
        from audit.models import AuditLog
        from tourist.models import GuideProfile, Notification
        app_id = self._apply().json()["id"]
        self.client.force_authenticate(self.admin)
        base = "/api/v1/workforce/admin/applications"
        self.assertEqual(self.client.post(f"{base}/{app_id}/action/", {"action": "review"}, format="json").json()["status"], "under_review")
        self.assertEqual(self.client.post(f"{base}/{app_id}/action/", {"action": "verify_documents"}, format="json").json()["status"], "document_verification")
        resp = self.client.post(f"{base}/{app_id}/action/", {"action": "approve", "note": "License confirmed"}, format="json")
        self.assertEqual(resp.json()["status"], "approved")
        profile = GuideProfile.objects.get(user=self.applicant)
        self.assertEqual(profile.verification_status, "verified")
        self.assertIsNotNone(profile.verified_at)
        self.assertEqual(profile.verified_by, self.admin)
        self.assertEqual(profile.languages, ["Nepali", "English"])  # carried from application
        self.assertTrue(Notification.objects.filter(user=self.applicant, title="Guide application approved").exists())
        self.assertTrue(AuditLog.objects.filter(action="workforce.guide.approve").exists())
        # now visible in the public directory
        names = [row["name"] for row in self.client.get("/api/v1/workforce/guides/").json()["results"]]
        self.assertIn("Pemba Sherpa", names)

    def test_needs_info_requires_note_and_notifies(self):
        from tourist.models import Notification
        app_id = self._apply().json()["id"]
        self.client.force_authenticate(self.admin)
        resp = self.client.post(f"/api/v1/workforce/admin/applications/{app_id}/action/", {"action": "needs_info"}, format="json")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(f"/api/v1/workforce/admin/applications/{app_id}/action/",
                                {"action": "needs_info", "note": "Upload citizenship scan"}, format="json")
        self.assertEqual(resp.json()["status"], "needs_info")
        self.assertTrue(Notification.objects.filter(user=self.applicant, title="Additional information requested").exists())

    def test_suspend_and_reinstate_controls_directory(self):
        self.client.force_authenticate(self.admin)
        gid = self.verified.id
        resp = self.client.post(f"/api/v1/workforce/admin/guides/{gid}/action/", {"action": "suspend"}, format="json")
        self.assertEqual(resp.status_code, 400)  # reason required
        resp = self.client.post(f"/api/v1/workforce/admin/guides/{gid}/action/", {"action": "suspend", "note": "Complaint under investigation"}, format="json")
        self.assertEqual(resp.json()["verification_status"], "suspended")
        names = [row["name"] for row in self.client.get("/api/v1/workforce/guides/").json()["results"]]
        self.assertNotIn("Pro Guide", names)
        self.client.post(f"/api/v1/workforce/admin/guides/{gid}/action/", {"action": "reinstate"}, format="json")
        names = [row["name"] for row in self.client.get("/api/v1/workforce/guides/").json()["results"]]
        self.assertIn("Pro Guide", names)

    def test_guides_cannot_self_verify(self):
        self.client.force_authenticate(self.applicant)
        resp = self.client.put("/api/v1/workforce/guide-profile/", {
            "headline": "Self verified", "verification_status": "verified", "verified_at": "2026-01-01T00:00:00Z",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["verification_status"], "unverified")  # server-controlled
        self.assertEqual(resp.json()["headline"], "Self verified")          # benign field saved


class TourismJobsTests(TestCase):
    """Tourism work/gig marketplace (workforce spec §9)."""

    def setUp(self):
        from tourist.models import TourismJob
        self.admin = User.objects.create_superuser("tj-admin@test.local", "Sup!Pass123")
        self.poster = User.objects.create_user(email="tj-poster@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.poster, capabilities={"marketplace": ["view", "add", "change"]})
        self.worker = User.objects.create_user(email="tj-worker@test.local", password="Work!Pass123", role="tourist", first_name="Job", last_name="Seeker")
        self.job = TourismJob.objects.create(
            posted_by=self.poster, title="Trek Assistant — Annapurna Circuit", role_type="trek_assistant",
            description="Carry equipment and assist guides on the Annapurna Circuit.",
            city="Pokhara", employment_type="seasonal", compensation="NPR 2,500/day",
        )
        self.client = APIClient()

    def _apply(self, user=None, job_id=None):
        self.client.force_authenticate(user or self.worker)
        return self.client.post("/api/v1/workforce/job-applications/", {
            "job": job_id or self.job.id, "cover_letter": "I have trekked the circuit 6 times.",
            "skills": ["high-altitude", "first-aid"], "availability": "Oct-Nov 2026",
        }, format="json")

    def test_public_list_shows_only_open_jobs(self):
        from tourist.models import TourismJob
        TourismJob.objects.create(posted_by=self.poster, title="Closed Gig", description="x", status="closed")
        resp = self.client.get("/api/v1/workforce/jobs/")
        titles = [row["title"] for row in resp.json()["results"]]
        self.assertIn("Trek Assistant — Annapurna Circuit", titles)
        self.assertNotIn("Closed Gig", titles)

    def test_apply_and_duplicate_guard(self):
        from tourist.models import Notification
        resp = self._apply()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["status"], "applied")
        self.assertTrue(Notification.objects.filter(user=self.poster, title="New job application").exists())
        self.assertEqual(self._apply().status_code, 400)

    def test_apply_requires_auth_and_open_job(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/v1/workforce/job-applications/", {"job": self.job.id, "cover_letter": "x"}, format="json").status_code, 401)
        self.job.status = "filled"
        self.job.save(update_fields=["status"])
        self.assertEqual(self._apply().status_code, 400)

    def test_job_creation_requires_capability(self):
        payload = {"title": "Content Creator", "description": "Write destination stories", "role_type": "content_creator"}
        plain = User.objects.create_user(email="tj-noperm@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.client.force_authenticate(plain)
        self.assertEqual(self.client.post("/api/v1/workforce/jobs/", payload, format="json").status_code, 403)
        self.client.force_authenticate(self.poster)
        resp = self.client.post("/api/v1/workforce/jobs/", payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["status"], "open")

    def test_review_flow_shortlist_hire_notifies_and_audits(self):
        from audit.models import AuditLog
        from tourist.models import Notification
        app_id = self._apply().json()["id"]
        self.client.force_authenticate(self.admin)
        base = "/api/v1/workforce/admin/job-applications"
        resp = self.client.post(f"{base}/{app_id}/action/", {"action": "shortlist"}, format="json")
        self.assertEqual(resp.json()["status"], "shortlisted")
        resp = self.client.post(f"{base}/{app_id}/action/", {"action": "reject"}, format="json")
        self.assertEqual(resp.status_code, 400)  # note required
        resp = self.client.post(f"{base}/{app_id}/action/", {"action": "hire", "note": "Start Oct 1"}, format="json")
        self.assertEqual(resp.json()["status"], "hired")
        self.assertTrue(Notification.objects.filter(user=self.worker, title="Job application hired").exists())
        self.assertTrue(AuditLog.objects.filter(action="workforce.job.hire").exists())

    def test_job_status_actions_and_filters(self):
        self.client.force_authenticate(self.poster)
        resp = self.client.post(f"/api/v1/workforce/admin/jobs/{self.job.id}/action/", {"action": "pause"}, format="json")
        self.assertEqual(resp.json()["status"], "paused")
        self.assertEqual(self.client.get("/api/v1/workforce/admin/jobs/?status=paused").json()["counts"]["paused"], 1)
        resp = self.client.post(f"/api/v1/workforce/admin/jobs/{self.job.id}/action/", {"action": "bogus"}, format="json")
        self.assertEqual(resp.status_code, 400)


class GuideBookingReviewTests(TestCase):
    """Tourist↔guide booking requests + reviews/reputation (workforce spec §12/§13)."""

    def setUp(self):
        from tourist.models import GuideProfile
        self.admin = User.objects.create_superuser("gb-admin@test.local", "Sup!Pass123")
        self.guide_user = User.objects.create_user(email="gb-guide@test.local", password="Guide!Pass123", role="tourist", first_name="Pemba", last_name="Sherpa")
        self.guide = GuideProfile.objects.create(user=self.guide_user, verification_status="verified", is_public=True,
                                                 headline="Annapurna specialist", daily_rate_npr=3000)
        self.tourist = User.objects.create_user(email="gb-tourist@test.local", password="Tour!Pass123", role="tourist", first_name="Trip", last_name="Planner")
        self.client = APIClient()

    def _create(self, start="2026-10-05", end="2026-10-09"):
        self.client.force_authenticate(self.tourist)
        return self.client.post("/api/v1/workforce/guide-bookings/", {
            "guide_id": self.guide.id, "start_date": start, "end_date": end,
            "group_size": 4, "message": "Annapurna base camp trek",
        }, format="json")

    def _act(self, booking_id, action, user, note=""):
        self.client.force_authenticate(user)
        return self.client.post(f"/api/v1/workforce/guide-bookings/{booking_id}/action/",
                                {"action": action, "note": note}, format="json")

    def test_unverified_or_suspended_guides_cannot_be_booked(self):
        self.guide.verification_status = "suspended"
        self.guide.save(update_fields=["verification_status"])
        resp = self._create()
        self.assertEqual(resp.status_code, 400)
        self.guide.verification_status = "verified"
        self.guide.is_public = False
        self.guide.save(update_fields=["is_public"])
        self.assertEqual(self._create().status_code, 400)

    def test_full_lifecycle_request_accept_complete_review(self):
        from tourist.models import Notification
        booking_id = self._create().json()["id"]
        # guide notified
        self.assertTrue(Notification.objects.filter(user=self.guide_user, title="New booking request").exists())
        # tourist cannot accept own request
        self.assertEqual(self._act(booking_id, "accept", self.tourist).status_code, 403)
        # review before completion → 400
        self.client.force_authenticate(self.tourist)
        self.assertEqual(self.client.post(f"/api/v1/workforce/guide-bookings/{booking_id}/review/", {"rating": 5}, format="json").status_code, 400)
        # guide accepts → complete
        self.assertEqual(self._act(booking_id, "accept", self.guide_user).json()["status"], "accepted")
        self.assertEqual(self._act(booking_id, "complete", self.guide_user).json()["status"], "completed")
        # tourist reviews once
        self.client.force_authenticate(self.tourist)
        resp = self.client.post(f"/api/v1/workforce/guide-bookings/{booking_id}/review/",
                                {"rating": 5, "review": "Best guide ever"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/workforce/guide-bookings/{booking_id}/review/", {"rating": 4}, format="json").status_code, 400)

    def test_decline_requires_note_and_stranger_cannot_act(self):
        booking_id = self._create().json()["id"]
        self.assertEqual(self._act(booking_id, "decline", self.guide_user).status_code, 400)
        stranger = User.objects.create_user(email="gb-stranger@test.local", password="Tour!Pass123", role="tourist")
        self.assertEqual(self._act(booking_id, "accept", stranger).status_code, 403)
        self.assertEqual(self._act(booking_id, "decline", self.guide_user, note="Fully booked").json()["status"], "declined")

    def test_duplicate_active_request_blocked_and_cancel_frees(self):
        self._create()
        dup = self._create(start="2026-11-01", end="2026-11-05")
        self.assertEqual(dup.status_code, 400)
        self.assertIn("already have an active request", dup.json()["detail"])
        bookings = self.client.get("/api/v1/workforce/guide-bookings/?side=tourist").json()["results"]
        self.assertEqual(self._act(bookings[0]["id"], "cancel", self.tourist).json()["status"], "cancelled")
        self.assertEqual(self._create(start="2026-11-01", end="2026-11-05").status_code, 201)

    def test_public_reviews_and_directory_aggregate(self):
        booking_id = self._create().json()["id"]
        self._act(booking_id, "accept", self.guide_user)
        self._act(booking_id, "complete", self.guide_user)
        self.client.force_authenticate(self.tourist)
        self.client.post(f"/api/v1/workforce/guide-bookings/{booking_id}/review/",
                         {"rating": 4, "review": "Knowledgeable and punctual"}, format="json")
        self.client.force_authenticate(None)
        reviews = self.client.get(f"/api/v1/workforce/guides/{self.guide.id}/reviews/").json()
        self.assertEqual(reviews["rating_avg"], 4.0)
        self.assertEqual(reviews["review_count"], 1)
        listing = self.client.get("/api/v1/workforce/guides/").json()["results"][0]
        self.assertEqual(listing["rating_avg"], 4.0)
        self.assertEqual(listing["review_count"], 1)

    def test_guide_side_queue_requires_profile(self):
        self.client.force_authenticate(self.tourist)
        self.assertEqual(self.client.get("/api/v1/workforce/guide-bookings/?side=guide").status_code, 404)
        self._create()
        self.client.force_authenticate(self.guide_user)
        results = self.client.get("/api/v1/workforce/guide-bookings/?side=guide").json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["tourist_email"], "gb-tourist@test.local")

    def test_invalid_dates_rejected(self):
        self.client.force_authenticate(self.tourist)
        self.assertEqual(self.client.post("/api/v1/workforce/guide-bookings/", {"guide_id": self.guide.id}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/workforce/guide-bookings/", {"guide_id": self.guide.id, "start_date": "2026-10-09", "end_date": "2026-10-05"}, format="json").status_code, 400)


class WorkforceOverviewStatsTests(TestCase):
    """Workforce roll-up + guide earnings/stats (workforce spec §14)."""

    def setUp(self):
        from datetime import date
        from tourist.models import GuideBookingRequest, GuideProfile, TourismJob
        self.admin = User.objects.create_superuser("ov-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="ov-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"marketplace": ["view"]})
        self.guide_user = User.objects.create_user(email="ov-guide@test.local", password="Guide!Pass123", role="tourist")
        self.guide = GuideProfile.objects.create(user=self.guide_user, verification_status="verified",
                                                 is_public=True, daily_rate_npr=2000)
        self.tourist = User.objects.create_user(email="ov-tourist@test.local", password="Tour!Pass123", role="tourist")
        TourismJob.objects.create(posted_by=self.admin, title="Photographer wanted", description="x")
        GuideBookingRequest.objects.create(tourist=self.tourist, guide_profile=self.guide,
                                           start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), status="completed")
        GuideBookingRequest.objects.create(tourist=self.tourist, guide_profile=self.guide,
                                           start_date=date(2026, 11, 1), end_date=date(2026, 11, 3), status="accepted")
        self.client = APIClient()

    def test_overview_requires_capability_and_reports_counts(self):
        plain = User.objects.create_user(email="ov-noperm@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        self.client.force_authenticate(plain)
        self.assertEqual(self.client.get("/api/v1/workforce/admin/overview/").status_code, 403)
        self.client.force_authenticate(self.staff)
        data = self.client.get("/api/v1/workforce/admin/overview/").json()
        self.assertEqual(data["jobs"]["open"], 1)
        self.assertEqual(data["bookings"]["completed"], 1)
        self.assertEqual(data["bookings"]["accepted"], 1)
        self.assertEqual(data["bookings"]["requested"], 0)
        self.assertEqual(data["guides"]["verified"], 1)
        self.assertEqual(data["pending_work"], 0)
        GuideBookingRequest = self.guide.booking_requests.model
        GuideBookingRequest.objects.create(tourist=self.tourist, guide_profile=self.guide,
                                           start_date="2026-12-01", status="requested")
        data = self.client.get("/api/v1/workforce/admin/overview/").json()
        self.assertEqual(data["pending_work"], 1)

    def test_guide_stats_own_profile_only_with_earnings_estimate(self):
        self.client.force_authenticate(self.tourist)
        self.assertEqual(self.client.get("/api/v1/workforce/guide-stats/").status_code, 404)
        self.client.force_authenticate(self.guide_user)
        data = self.client.get("/api/v1/workforce/guide-stats/").json()
        self.assertEqual(data["booking_counts"]["completed"], 1)
        self.assertEqual(data["booking_counts"]["accepted"], 1)
        # completed trip 10/01→10/05 = 5 days × 2000 = 10,000
        self.assertEqual(data["completed_earnings_estimate_npr"], 10000.0)
        # upcoming accepted trip 11/01→11/03 = 3 days × 2000 = 6,000
        self.assertEqual(len(data["upcoming_trips"]), 1)
        self.assertEqual(data["upcoming_earnings_estimate_npr"], 6000.0)
        self.assertIn("does not process", data["estimate_basis"])
        self.assertIsNone(data["rating_avg"])

    def test_guide_stats_includes_reputation_after_review(self):
        from datetime import date
        from tourist.models import GuideBookingRequest, GuideReview
        booking = GuideBookingRequest.objects.create(tourist=self.tourist, guide_profile=self.guide,
                                                     start_date=date(2026, 9, 1), status="completed")
        GuideReview.objects.create(booking=booking, user=self.tourist, guide_profile=self.guide,
                                   rating=4, review="Solid guide")
        self.client.force_authenticate(self.guide_user)
        data = self.client.get("/api/v1/workforce/guide-stats/").json()
        self.assertEqual(data["rating_avg"], 4.0)
        self.assertEqual(data["review_count"], 1)
        # single-day completed trip also counts: 1 × 2000 = 2000
        self.assertEqual(data["completed_earnings_estimate_npr"], 12000.0)


class DestinationCoverImagePriorityTests(TestCase):
    """Admin cover changes must be visible: detail `images[]` lists the
    admin-designated cover FIRST, and cover_image_url reflects the cover."""

    def setUp(self):
        from tourist.models import Destination, DestinationImage
        self.dest = Destination.objects.create(name="Bandipur", slug="bandipur-cover-test")
        self.first = DestinationImage.objects.create(
            destination=self.dest, external_url="https://old.example/first.jpg",
            verification_status="approved", is_verified=True, is_cover=False)
        self.cover = DestinationImage.objects.create(
            destination=self.dest, external_url="https://new.example/cover.jpg",
            verification_status="approved", is_verified=True, is_cover=True)
        self.client = APIClient()

    def test_detail_images_lists_cover_first(self):
        data = self.client.get("/api/v1/destinations/bandipur-cover-test/").json()
        self.assertEqual(data["images"][0], "https://new.example/cover.jpg")
        self.assertIn("https://old.example/first.jpg", data["images"])

    def test_cover_image_url_falls_back_to_cover_photo(self):
        data = self.client.get("/api/v1/destinations/bandipur-cover-test/").json()
        # No Destination.cover_image set → cover photo drives cover_image_url
        self.assertEqual(data["cover_image_url"], "https://new.example/cover.jpg")

    def test_admin_cover_url_update_visible_in_detail(self):
        admin = User.objects.create_superuser("cover-admin@test.local", "Sup!Pass123")
        self.client.force_authenticate(admin)
        resp = self.client.patch(f"/api/v1/admin/destinations/{self.dest.id}/images",
                                 {"image_url": "https://admin.example/changed.jpg"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.client.force_authenticate(None)
        data = self.client.get("/api/v1/destinations/bandipur-cover-test/").json()
        self.assertEqual(data["cover_image_url"], "https://admin.example/changed.jpg")


class HomepageCMSDraftPublishTests(TestCase):
    """Draft/publish isolation for the homepage CMS (prompt §13/§32/§51):
    editing a published section must NOT change the public homepage until
    Publish; preview serves the draft; legacy sections keep working."""

    def setUp(self):
        from tourist.models import ManagedPage, ContentSection
        from tourist.cms_publishing import sync_published_snapshot
        self.admin = User.objects.create_superuser("cms-admin@test.local", "Sup!Pass123")
        self.staff = User.objects.create_user(email="cms-staff@test.local", password="Staff!Pass123", role="staff", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.staff, capabilities={"content": ["view", "add", "change"]})
        self.page, _ = ManagedPage.objects.get_or_create(
            key="home", defaults={"route": "/", "title": "Nepal Yatra", "status": "published"})
        self.page.status = "published"
        self.page.is_enabled = True
        self.page.save(update_fields=["status", "is_enabled"])
        self.section, _ = ContentSection.objects.get_or_create(
            page=self.page, key="features",
            defaults={"title": "Why travel with Nepal Portal", "body": "Everything you need.",
                      "section_type": "cards", "status": "published"})
        self.section.title = "Why travel with Nepal Portal"
        self.section.body = "Everything you need."
        self.section.status = "published"
        self.section.is_visible = True
        self.section.save()
        sync_published_snapshot(self.section)
        self.client = APIClient()

    def _public_section(self, key="features"):
        data = self.client.get("/api/v1/config/public/").json()
        for page in data.get("pages", []):
            for sec in page.get("sections", []):
                if sec["key"] == key:
                    return sec
        return None

    def _patch(self, payload):
        self.client.force_authenticate(self.admin)
        return self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.section.id, **payload}, format="json")

    def test_edit_is_draft_until_publish(self):
        # Save Draft: plain update → public unchanged
        resp = self._patch({"title": "Plan Your Complete Nepal Adventure"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._public_section()["title"], "Why travel with Nepal Portal")
        # Admin preview endpoint shows the draft
        self.client.force_authenticate(self.admin)
        preview = self.client.get(f"/api/v1/admin/cms/?resource=sections&id={self.section.id}&preview=1").json()["preview"]
        self.assertEqual(preview["title"], "Plan Your Complete Nepal Adventure")
        # Publish → public updates
        self._patch({"action": "publish"})
        self.assertEqual(self._public_section()["title"], "Plan Your Complete Nepal Adventure")

    def test_visibility_and_status_still_gate_public(self):
        self._patch({"is_visible": False})
        self.assertIsNone(self._public_section())
        self._patch({"is_visible": True})
        self.assertIsNotNone(self._public_section())
        self._patch({"action": "unpublish"})
        self.assertIsNone(self._public_section())

    def test_legacy_section_without_snapshot_serves_live_fields(self):
        from tourist.models import ContentSection
        legacy, _ = ContentSection.objects.get_or_create(
            page=self.page, key="legacy-text",
            defaults={"title": "Legacy live title", "section_type": "text", "status": "published"})
        legacy.title = "Legacy live title"
        legacy.status = "published"
        legacy.is_visible = True
        legacy.published_snapshot = None
        legacy.save()
        self.assertEqual(self._public_section("legacy-text")["title"], "Legacy live title")
        # editing a legacy section keeps the old (pre-snapshot) behaviour
        self._patch = lambda payload: (self.client.force_authenticate(self.admin),
            self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": legacy.id, **payload}, format="json"))[1]
        self._patch({"title": "Legacy edited"})
        self.assertEqual(self._public_section("legacy-text")["title"], "Legacy edited")

    def test_blocks_flow_through_snapshot(self):
        from tourist.models import ContentBlock
        ContentBlock.objects.create(section=self.section, block_type="heading", title="Itinerary", position=1)
        self._patch({"action": "publish"})
        self.assertEqual(len(self._public_section()["blocks"]), 1)
        # a new block is a draft until the next publish
        self.client.force_authenticate(self.admin)
        self.client.post(f"/api/v1/admin/sections/{self.section.id}/blocks/",
                         {"block_type": "button", "title": "Budget", "data": {"url": "/budget-estimator"}}, format="json")
        self.assertEqual(len(self._public_section()["blocks"]), 1)
        self._patch({"action": "publish"})
        self.assertEqual(len(self._public_section()["blocks"]), 2)

    def test_non_staff_cannot_touch_cms(self):
        tourist = User.objects.create_user(email="cms-tourist@test.local", password="Tour!Pass123", role="tourist")
        self.client.force_authenticate(tourist)
        self.assertEqual(self.client.get("/api/v1/admin/cms/?resource=sections").status_code, 403)
        self.assertEqual(self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.section.id, "title": "Hacked"}, format="json").status_code, 403)
        self.assertEqual(self._public_section()["title"], "Why travel with Nepal Portal")


class HomepageCMSBlockTypesTests(TestCase):
    """card_grid + packages block types and the seeded draft homepage
    sections (CMS prompt §8/§9): validation, draft gating, publish flow."""

    def setUp(self):
        from tourist.models import ManagedPage
        self.admin = User.objects.create_superuser("blk-admin@test.local", "Sup!Pass123")
        self.page, _ = ManagedPage.objects.get_or_create(
            key="home", defaults={"route": "/", "title": "Nepal Yatra", "status": "published"})
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def _section(self, key):
        from tourist.models import ContentSection
        return ContentSection.objects.filter(page=self.page, key=key).first()

    def test_seeded_sections_exist_as_drafts_and_are_not_public(self):
        tp = self._section("travel-planning")
        fp = self._section("featured-packages")
        self.assertIsNotNone(tp)
        self.assertIsNotNone(fp)
        self.assertEqual(tp.status, "draft")
        self.assertEqual(fp.status, "draft")
        self.assertEqual(tp.blocks.filter(block_type="card_grid").count(), 1)
        self.assertEqual(fp.blocks.filter(block_type="packages").count(), 1)
        public = self.client.get("/api/v1/config/public/").json()
        keys = [s["key"] for p in public.get("pages", []) if p.get("route") == "/" for s in p.get("sections", [])]
        self.assertNotIn("travel-planning", keys)
        self.assertNotIn("featured-packages", keys)
        # publishing makes it public (snapshot path)
        self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": tp.id, "action": "publish"}, format="json")
        public = self.client.get("/api/v1/config/public/").json()
        rows = [s for p in public.get("pages", []) if p.get("route") == "/" for s in p.get("sections", []) if s["key"] == "travel-planning"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["blocks"]), 1)
        self.assertEqual(rows[0]["blocks"][0]["block_type"], "card_grid")
        # cleanup: unpublish again so the public homepage stays unchanged
        self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": tp.id, "action": "unpublish"}, format="json")

    def test_card_grid_validation(self):
        tp = self._section("travel-planning")
        resp = self.client.post(f"/api/v1/admin/sections/{tp.id}/blocks/", {
            "block_type": "card_grid", "title": "Bad cards",
            "data": {"items": [{"title": "OK", "url": "/good"}, {"title": "Bad", "url": "https://evil.example"}]},
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("internal routes", resp.json()["detail"])
        resp = self.client.post(f"/api/v1/admin/sections/{tp.id}/blocks/", {
            "block_type": "card_grid", "title": "Good cards",
            "data": {"items": [{"emoji": "🗺️", "title": "Itinerary", "description": "Plan it", "url": "/travel-planning"}]},
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_packages_limit_validation(self):
        fp = self._section("featured-packages")
        resp = self.client.post(f"/api/v1/admin/sections/{fp.id}/blocks/", {
            "block_type": "packages", "title": "Too many", "data": {"limit": 50},
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(f"/api/v1/admin/sections/{fp.id}/blocks/", {
            "block_type": "packages", "title": "Just right", "data": {"limit": 3},
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_non_staff_cannot_create_blocks(self):
        tourist = User.objects.create_user(email="blk-tourist@test.local", password="Tour!Pass123", role="tourist")
        self.client.force_authenticate(tourist)
        tp = self._section("travel-planning")
        self.assertEqual(self.client.post(f"/api/v1/admin/sections/{tp.id}/blocks/", {
            "block_type": "card_grid", "title": "Hack", "data": {"items": []}}, format="json").status_code, 403)


class MediaLibraryCoverPropagationTests(TestCase):
    """Central Media Library fixes: set-cover promotes any approved image to
    the public cover, and replacements propagate to string references."""

    def setUp(self):
        from tourist.models import Destination, DestinationImage
        self.admin = User.objects.create_superuser("mlib-admin@test.local", "Sup!Pass123")
        self.dest = Destination.objects.create(name="Bandipur", slug="bandipur-mlib")
        self.old = DestinationImage.objects.create(
            destination=self.dest, external_url="https://cdn.example/old-bandipur.jpg",
            verification_status="approved", is_verified=True, is_cover=True)
        self.new = DestinationImage.objects.create(
            destination=self.dest, external_url="https://cdn.example/new-bandipur.jpg",
            verification_status="approved", is_verified=True, is_cover=False)
        self.pending = DestinationImage.objects.create(
            destination=self.dest, external_url="https://cdn.example/pending.jpg",
            verification_status="pending", is_cover=False)
        self.dest.cover_image = "https://cdn.example/old-bandipur.jpg"
        self.dest.save(update_fields=["cover_image"])
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def _public_cover(self):
        data = self.client.get("/api/v1/destinations/bandipur-mlib/").json()
        return data.get("cover_image_url")

    def test_set_cover_updates_public_site(self):
        self.assertEqual(self._public_cover(), "https://cdn.example/old-bandipur.jpg")
        resp = self.client.patch("/api/v1/admin/media-library/", {"id": self.new.id, "action": "set_cover"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self._public_cover(), "https://cdn.example/new-bandipur.jpg")
        self.old.refresh_from_db()
        self.assertFalse(self.old.is_cover)

    def test_pending_image_cannot_become_cover(self):
        resp = self.client.patch("/api/v1/admin/media-library/", {"id": self.pending.id, "action": "set_cover"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("approved", resp.json()["detail"])
        self.assertEqual(self._public_cover(), "https://cdn.example/old-bandipur.jpg")

    def test_replacement_propagates_to_cms_references(self):
        from tourist.models import ManagedPage, ContentSection
        page = ManagedPage.objects.create(route="/mlib-test", key="mlib-test", title="MLib Test", status="published")
        section = ContentSection.objects.create(
            page=page, key="banner", title="Banner", section_type="image",
            image_url="https://cdn.example/old-bandipur.jpg", status="published")
        resp = self.client.patch("/api/v1/admin/media-library/", {
            "id": self.old.id, "external_url": "https://cdn.example/replaced-bandipur.jpg",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["propagated_references"], 1)
        section.refresh_from_db()
        self.assertIn("replaced-bandipur", section.image_url)
        # cover follows the replaced cover image too
        self.assertIn("replaced-bandipur", self._public_cover())

    def test_non_staff_cannot_touch_media_library(self):
        tourist = User.objects.create_user(email="mlib-tourist@test.local", password="Tour!Pass123", role="tourist")
        self.client.force_authenticate(tourist)
        self.assertEqual(self.client.get("/api/v1/admin/media-library/").status_code, 403)
        self.assertEqual(self.client.patch("/api/v1/admin/media-library/", {"id": self.new.id, "action": "set_cover"}, format="json").status_code, 403)


class NearbyPOIsOverpassTests(TestCase):
    """Location-based nearby places (OpenStreetMap/Overpass proxy)."""

    def setUp(self):
        from django.core.cache import cache
        from tourist.models import Destination
        cache.clear()  # POI payloads are cached per location — isolate tests
        self.dest = Destination.objects.create(name="POI Town", slug="poi-town", latitude=28.2, longitude=83.99)

    def _fake_elements(self):
        return {"elements": [
            {"id": 1, "lat": 28.210, "lon": 83.995, "tags": {"name": "Far Hotel", "tourism": "hotel"}},
            {"id": 2, "lat": 28.201, "lon": 83.991, "tags": {"name": "Near Hotel", "tourism": "guest_house"}},
            {"id": 3, "lat": 28.205, "lon": 83.992, "tags": {"name": "City Hospital", "amenity": "hospital"}},
            {"id": 4, "lat": 28.202, "lon": 83.990, "tags": {"name": "Shiva Mandir", "amenity": "place_of_worship"}},
            {"id": 5, "lat": 28.203, "lon": 83.993, "tags": {"name": "Lake View Point", "tourism": "viewpoint"}},
            {"id": 6, "lat": 28.300, "lon": 84.100, "tags": {"name": "Unnamed Node", "amenity": "atm"}},
        ]}

    def test_groups_sorts_and_computes_distances(self):
        from unittest.mock import patch, MagicMock
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.json.return_value = self._fake_elements()
        with patch("requests.post", return_value=fake):
            resp = self.client.get("/api/v1/destinations/poi-town/nearby-pois/?radius_km=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["source"], "OpenStreetMap (Overpass API)")
        hotels = data["categories"]["hotels"]["results"]
        self.assertEqual([h["name"] for h in hotels], ["Near Hotel", "Far Hotel"])  # nearest first
        self.assertLess(hotels[0]["distance_km"], hotels[1]["distance_km"])
        self.assertEqual(data["categories"]["temples"]["results"][0]["name"], "Shiva Mandir")
        self.assertEqual(len(data["categories"]["hospitals"]["results"]), 1)
        # nameless nodes are skipped, banks empty but present
        self.assertEqual(data["categories"]["banks"]["results"], [])

    def test_overpass_outage_is_honest_503(self):
        from unittest.mock import patch
        with patch("requests.post", side_effect=Exception("network down")):
            resp = self.client.get("/api/v1/destinations/poi-town/nearby-pois/")
        self.assertEqual(resp.status_code, 503)
        self.assertIn("unavailable", resp.json()["detail"])

    def test_unknown_destination_404_and_missing_coords_422(self):
        from tourist.models import Destination
        Destination.objects.create(name="No Coords", slug="poi-no-coords")
        self.assertEqual(self.client.get("/api/v1/destinations/does-not-exist/nearby-pois/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/destinations/poi-no-coords/nearby-pois/").status_code, 422)


class CMSAdminControlTests(TestCase):
    """Admin full-control additions: page/section deletion, card images, support links."""

    def setUp(self):
        from tourist.models import ManagedPage, ContentSection
        self.admin = User.objects.create_superuser("cmsctl-admin@test.local", "Sup!Pass123")
        self.page = ManagedPage.objects.create(route="/ctl-test", key="ctl-test", title="CTL Test", status="published")
        self.section = ContentSection.objects.create(page=self.page, key="intro", title="Intro", section_type="text", status="published")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_admin_can_delete_section_and_page_with_cascade(self):
        resp = self.client.delete("/api/v1/admin/cms/", {"resource": "sections", "id": self.section.id}, format="json")
        self.assertEqual(resp.status_code, 200)
        from tourist.models import ContentSection
        self.assertFalse(ContentSection.objects.filter(pk=self.section.pk).exists())
        resp = self.client.delete("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.id}, format="json")
        self.assertEqual(resp.status_code, 200)
        from tourist.models import ManagedPage
        self.assertFalse(ManagedPage.objects.filter(pk=self.page.pk).exists())

    def test_homepage_delete_is_refused(self):
        from tourist.models import ManagedPage
        home, _ = ManagedPage.objects.get_or_create(route="/", defaults={"key": "home", "title": "Home", "status": "published"})
        resp = self.client.delete("/api/v1/admin/cms/", {"resource": "pages", "id": home.id}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(ManagedPage.objects.filter(pk=home.pk).exists())

    def test_tourist_cannot_delete_pages(self):
        tourist = User.objects.create_user(email="cmsctl-tourist@test.local", password="Tour!Pass123", role="tourist")
        self.client.force_authenticate(tourist)
        resp = self.client.delete("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.id}, format="json")
        self.assertIn(resp.status_code, (401, 403))

    def test_card_grid_accepts_https_images_and_rejects_javascript_urls(self):
        resp = self.client.post("/api/v1/admin/sections/%d/blocks/" % self.section.id, {
            "block_type": "card_grid",
            "data": {"items": [{"title": "Flag", "image": "https://cdn.example/flag.jpg", "url": "/about"}]},
        }, format="json")
        self.assertEqual(resp.status_code, 201, resp.content[:200])
        resp = self.client.post("/api/v1/admin/sections/%d/blocks/" % self.section.id, {
            "block_type": "card_grid",
            "data": {"items": [{"title": "Bad", "image": "javascript:alert(1)"}]},
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("image", resp.json()["detail"].lower())

    def test_support_links_seeded_in_navigation(self):
        from tourist.models import ManagedNavigationItem
        self.assertTrue(ManagedNavigationItem.objects.filter(location="navbar", route="/support").exists())
        self.assertTrue(ManagedNavigationItem.objects.filter(location="footer", route="/support").exists())
        public = self.client.get("/api/v1/config/public/")
        self.assertEqual(public.status_code, 200)
        nav = public.json().get("navigation") or []
        routes = [item.get("route") for item in nav]
        self.assertIn("/support", routes)


class CoordinateNearbyPOIsTests(TestCase):
    """Coordinate-first nearby places + admin-configurable categories (§2/§4/§9/§60)."""

    def setUp(self):
        from django.core.cache import cache
        from tourist.models import Destination, SiteSetting
        cache.clear()
        SiteSetting.objects.filter(key="poi_categories").delete()
        self.dest = Destination.objects.create(name="Verified Viewpoint Camp", slug="verified-viewpoint-camp",
                                               latitude=28.205, longitude=83.992)

    def _mocked_elements(self):
        return {"elements": [
            {"type": "node", "id": 11, "lat": 28.208, "lon": 83.994, "tags": {"name": "Lakeview Hospital", "amenity": "hospital", "phone": "061-520111"}},
            {"type": "node", "id": 12, "lat": 28.201, "lon": 83.990, "tags": {"name": "Potala Monastery", "amenity": "place_of_worship", "religion": "buddhist"}},
            {"type": "node", "id": 13, "lat": 28.202, "lon": 83.991, "tags": {"name": "Machhapuchhre Lodge", "tourism": "guest_house"}},
        ]}

    def _fake_response(self):
        from unittest.mock import MagicMock
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.json.return_value = self._mocked_elements()
        return fake

    def test_coordinates_required(self):
        self.assertEqual(self.client.get("/api/v1/nearby/pois/").status_code, 400)
        self.assertEqual(self.client.get("/api/v1/nearby/pois/?latitude=200&longitude=1").status_code, 400)

    def test_user_location_search_merges_verified_db_places(self):
        from unittest.mock import patch
        with patch("requests.post", return_value=self._fake_response()):
            resp = self.client.get("/api/v1/nearby/pois/?latitude=28.2&longitude=83.99&radius_km=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        hospitals = data["categories"]["hospitals"]["results"]
        self.assertEqual(hospitals[0]["name"], "Lakeview Hospital")
        self.assertEqual(hospitals[0]["phone"], "061-520111")
        self.assertTrue(hospitals[0]["source_url"].startswith("https://www.openstreetmap.org/"))
        self.assertEqual(data["categories"]["temples"]["results"][0]["religion"], "buddhist")
        db_names = [row["name"] for row in data["verified_database_places"]]
        self.assertIn("Verified Viewpoint Camp", db_names)  # admin-added place surfaces
        self.assertIsNone(data["provider_error"])

    def test_provider_outage_still_serves_verified_database_places(self):
        from unittest.mock import patch
        with patch("requests.post", side_effect=Exception("osm down")):
            resp = self.client.get("/api/v1/nearby/pois/?latitude=28.2&longitude=83.99&radius_km=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("unavailable", data["provider_error"])
        self.assertEqual(len(data["verified_database_places"]), 1)  # fallback works

    def test_admin_can_configure_categories(self):
        from unittest.mock import patch
        self.admin = User.objects.create_superuser("poicat-admin@test.local", "Sup!Pass123")
        client = APIClient()
        client.force_authenticate(self.admin)
        resp = client.put("/api/v1/admin/poi-categories/", {"categories": [
            {"key": "hospitals", "label": "Medical centres", "enabled": True, "order": 1, "limit": 3},
            {"key": "temples", "enabled": False},
        ]}, format="json")
        self.assertEqual(resp.status_code, 200)
        labels = {row["key"]: row for row in resp.json()["categories"]}
        self.assertEqual(labels["hospitals"]["label"], "Medical centres")
        self.assertFalse(labels["temples"]["enabled"])
        with patch("requests.post", return_value=self._fake_response()) as posted:
            search = self.client.get("/api/v1/nearby/pois/?latitude=28.2&longitude=83.99&radius_km=5")
        self.assertEqual(search.status_code, 200)
        cats = search.json()["categories"]
        self.assertNotIn("temples", cats)  # disabled by admin
        query_sent = posted.call_args.kwargs.get("data", {}).get("data", "") or (posted.call_args.args[1] if len(posted.call_args.args) > 1 else "")
        self.assertNotIn("place_of_worship", str(posted.call_args))
        self.assertIn("Medical centres", str({k: v["label"] for k, v in cats.items()}))

    def test_tourist_cannot_configure_categories(self):
        tourist = User.objects.create_user(email="poicat-tourist@test.local", password="Tour!Pass123", role="tourist")
        client = APIClient()
        client.force_authenticate(tourist)
        self.assertEqual(client.put("/api/v1/admin/poi-categories/", {"categories": []}, format="json").status_code, 403)


class TripInterestsAndSectionStyleTests(TestCase):
    """Admin-configurable trip interests (§22) + section style config (§47)."""

    def setUp(self):
        from tourist.models import ManagedPage, ContentSection, SiteSetting
        SiteSetting.objects.filter(key="trip_interests").delete()
        self.admin = User.objects.create_superuser("trip-admin@test.local", "Sup!Pass123")
        self.page = ManagedPage.objects.create(route="/trip-test", key="trip-test", title="Trip Test", status="published")
        self.section = ContentSection.objects.create(page=self.page, key="intro", title="Intro", section_type="text", status="published")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_admin_updates_interests_and_public_config_exposes_them(self):
        resp = self.client.put("/api/v1/admin/trip-interests/", {"interests": [
            {"key": "paragliding", "label": "Paragliding", "emoji": "🪂", "enabled": True, "order": 2},
            {"key": " rafting ", "label": "Rafting", "emoji": "🚣", "enabled": True, "order": 1},  # trimmed -> valid
            {"key": "yoga", "label": "", "emoji": "🧘"},  # missing label dropped
        ]}, format="json")
        self.assertEqual(resp.status_code, 200)
        saved = resp.json()["interests"]
        self.assertEqual([row["key"] for row in saved], ["rafting", "paragliding"])
        public = APIClient().get("/api/v1/config/public/")
        self.assertEqual(public.status_code, 200)
        interests = (public.json().get("settings") or {}).get("trip_interests")
        self.assertEqual([row["key"] for row in interests], ["rafting", "paragliding"])

    def test_tourist_cannot_update_interests(self):
        tourist = User.objects.create_user(email="trip-tourist@test.local", password="Tour!Pass123", role="tourist")
        self.client.force_authenticate(tourist)
        self.assertEqual(self.client.put("/api/v1/admin/trip-interests/", {"interests": []}, format="json").status_code, 403)

    def test_section_style_config_flows_to_public(self):
        resp = self.client.patch("/api/v1/admin/cms/", {
            "resource": "sections", "id": self.section.id, "action": "update",
            "config": {"text_scale": "lg", "align": "center", "bg_image": "https://cdn.example/bg.jpg", "background_style": "dark-slate"},
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.section.id, "action": "publish"}, format="json")
        public = APIClient().get("/api/v1/config/public/")
        page = next(p for p in public.json()["pages"] if p["key"] == "trip-test")
        cfg = next(sec for sec in page["sections"] if sec["key"] == "intro")["config"]
        self.assertEqual(cfg["text_scale"], "lg")
        self.assertEqual(cfg["align"], "center")
        self.assertEqual(cfg["bg_image"], "https://cdn.example/bg.jpg")
        self.assertEqual(cfg["background_style"], "dark-slate")


class LocationAwareRecommendationTests(TestCase):
    """Master spec §21/§119: opt-in traveller location for recommendations."""

    def setUp(self):
        from .models import Category, Destination
        self.lakes = Category.objects.create(name="Lakes Loc Test", slug="lakes")
        self.near = Destination.objects.create(
            name="Phewa Near Shore", slug="phewa-near-shore", category=self.lakes,
            district="Kaski", province="Gandaki", latitude=28.20, longitude=83.96,
            short_description="A calm lake shore walk",
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )
        self.far = Destination.objects.create(
            name="Eastern Far Lake", slug="eastern-far-lake", category=self.lakes,
            district="Sunsari", province="Koshi", latitude=26.65, longitude=87.27,
            short_description="A distant lake reserve",
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )

    def test_location_context_adds_distance_and_boosts_near_results(self):
        resp = self.client.get("/api/v1/destinations/mood-recommendations/", {
            "mood": "lakeside", "latitude": 28.21, "longitude": 83.98, "limit": 6,
        })
        self.assertEqual(resp.status_code, 200)
        results = resp.json()["results"]
        slugs = [row["slug"] for row in results]
        self.assertIn("phewa-near-shore", slugs)
        near_row = next(row for row in results if row["slug"] == "phewa-near-shore")
        self.assertLess(near_row["distance_km"], 5)
        self.assertTrue(near_row["distance_is_straight_line"])
        self.assertIn("proximity", near_row["match_breakdown"])
        self.assertEqual(resp.json()["preferences"]["location"], {"latitude": 28.21, "longitude": 83.98})
        if "eastern-far-lake" in slugs:
            self.assertLess(slugs.index("phewa-near-shore"), slugs.index("eastern-far-lake"))

    def test_invalid_coordinates_are_ignored_not_fatal(self):
        resp = self.client.get("/api/v1/destinations/mood-recommendations/", {
            "mood": "lakeside", "latitude": 999, "longitude": 83.98, "limit": 6,
        })
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIsNone(payload["preferences"]["location"])
        # The serializer always exposes the distance_km key; without a valid
        # location it must stay empty and the §21/§119 flag must be absent.
        self.assertFalse(any(row.get("distance_km") is not None for row in payload["results"]))
        self.assertFalse(any("distance_is_straight_line" in row for row in payload["results"]))


class RichTextBodySanitizationTests(TestCase):
    """Master spec §46: javascript: URLs never survive into stored bodies."""

    def setUp(self):
        from .models import ManagedPage, ContentSection
        self.admin = User.objects.create_superuser("rt-admin@test.local", "Sup!Pass123")
        self.page = ManagedPage.objects.create(route="/rt-test", key="rt-test", title="RT", status="published")
        self.section = ContentSection.objects.create(page=self.page, key="intro", title="I", section_type="text", status="published")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_javascript_href_is_neutralized_on_save(self):
        resp = self.client.patch("/api/v1/admin/cms/", {
            "resource": "sections", "id": self.section.id, "action": "update",
            "body": '<p>Hi</p><a href="javascript:alert(1)">click</a><img src="JaVaScRiPt:evil()">',
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.section.refresh_from_db()
        self.assertNotIn("javascript:", self.section.body.lower())
        self.assertIn('href="#"', self.section.body)
        self.assertIn("<p>Hi</p>", self.section.body)


class RoadDistanceProviderTests(TestCase):
    """Master spec §6/§69: real road distance via an admin-configured provider."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def _set_provider(self, value):
        from .models import SiteSetting
        SiteSetting.objects.filter(key="routing_provider").delete()
        SiteSetting.objects.create(key="routing_provider", value=value, is_public=False)

    def _metrics(self, coords=(27.7172, 85.3240, 28.2096, 83.9956)):
        return self.client.post("/api/v1/routing/metrics/", {
            "start_latitude": coords[0], "start_longitude": coords[1],
            "end_latitude": coords[2], "end_longitude": coords[3],
        })

    def test_migration_seeds_https_provider_setting(self):
        import importlib
        from .models import SiteSetting
        SiteSetting.objects.filter(key="routing_provider").delete()
        migration = importlib.import_module("tourist.migrations.0068_seed_routing_provider")
        from django.apps import apps as global_apps
        migration.seed_routing_provider(global_apps, None)
        row = SiteSetting.objects.get(key="routing_provider")
        self.assertTrue(row.value["base_url"].startswith("https://"))
        self.assertFalse(row.is_public)

    def test_admin_provider_setting_produces_road_distance(self):
        from unittest.mock import MagicMock, patch
        self._set_provider({"enabled": True, "base_url": "https://osrm.example.test/route/v1/driving", "api_key": ""})
        fake = MagicMock()
        fake.json.return_value = {"routes": [{"distance": 123456.0, "duration": 7200.0}]}
        fake.raise_for_status.return_value = None
        with patch("tourist.routing_service.requests.get", return_value=fake) as mocked:
            response = self._metrics()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "routed")
        self.assertEqual(data["road_distance_km"], 123.46)
        self.assertEqual(data["duration_min"], 120)
        self.assertEqual(mocked.call_count, 1)
        self.assertIn("osrm.example.test", mocked.call_args[0][0])

    def test_http_provider_is_rejected_without_calling_it(self):
        from unittest.mock import patch
        self._set_provider({"enabled": True, "base_url": "http://insecure.example.test/route/v1/driving"})
        with patch("tourist.routing_service.requests.get") as mocked:
            response = self._metrics()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(mocked.call_count, 0)
        self.assertNotEqual(data["status"], "routed")
        self.assertIsNotNone(data["straight_line_km"])

    def test_provider_failure_degrades_to_labelled_fallback(self):
        from unittest.mock import patch
        import requests as requests_lib
        self._set_provider({"enabled": True, "base_url": "https://osrm.example.test/route/v1/driving"})
        with patch("tourist.routing_service.requests.get", side_effect=requests_lib.RequestException("boom")):
            response = self._metrics()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], {"graph_routed", "routing_unavailable"})
        self.assertIsNone(data["road_distance_km"])
        # The note must keep the honest labelling in every fallback branch.
        self.assertTrue("not road distance" in data["note"] or "not a street-level" in data["note"] or "not a GraphHopper/OSRM" in data["note"])


class DistrictItineraryFallbackTests(TestCase):
    """Master prompt: itineraries must be district-specific, never one generic plan."""

    def setUp(self):
        from .models import Category, Destination
        cat = Category.objects.create(name="Heritage Itin Test", slug="heritage-itin")
        for i, (district, name) in enumerate([
            ("Rolpa", "Talgara Heritage Village"), ("Rolpa", "Jhimruk Ridge Viewpoint"), ("Rolpa", "Rolpa Bazaar Street"),
            ("Kaski", "Phewa Shore Walk"), ("Kaski", "Sarangkot Sunrise Ridge"), ("Kaski", "Begnas Lake Edge"),
        ]):
            Destination.objects.create(
                name=name, slug=f"itin-{district.lower()}-{i}", category=cat,
                district=district, city="", province="Gandaki",
                latitude=28.0 + i * 0.05, longitude=83.0 + i * 0.05,
                short_description="A recorded test place",
                status=Destination.SubmissionStatus.APPROVED, is_active=True,
            )

    def _plan(self, place, days=2):
        response = self.client.post("/api/v1/ml/itinerary/", {"days": days, "start_city": place}, format="json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_district_name_scopes_the_plan(self):
        data = self._plan("Rolpa")
        self.assertEqual(data["source"], "internal_db_engine")
        stops = [d for day in data["itinerary"] for d in day["destinations"]]
        self.assertTrue(stops)
        for stop in stops:
            self.assertEqual(stop["district"], "Rolpa")
            self.assertNotIn("day_trip", stop)

    def test_different_districts_get_different_plans(self):
        a = {d["name"] for day in self._plan("Rolpa")["itinerary"] for d in day["destinations"]}
        b = {d["name"] for day in self._plan("Kaski")["itinerary"] for d in day["destinations"]}
        self.assertTrue(a and b)
        self.assertFalse(a & b, "Rolpa and Kaski plans must not share stops")

    def test_unknown_place_is_labelled_not_fabricated(self):
        data = self._plan("Atlantis")
        self.assertEqual(data["source"], "internal_db_engine")
        self.assertIn("No verified places", data["data_note"])

    def test_fallback_days_are_time_aware(self):
        """§12: stops carry start/end times, travel legs and an honest
        timing_note — estimates labelled as estimates, never exact fakes."""
        data = self._plan("Kaski", days=1)
        stops = [d for day in data["itinerary"] for d in day["destinations"]]
        self.assertGreaterEqual(len(stops), 2)
        first, second = stops[0], stops[1]
        self.assertEqual(first["start_time"], "09:00")
        self.assertEqual(first["duration_minutes"], 90)
        self.assertEqual(first["end_time"], "10:30")
        self.assertIn("travel_from_previous", second)
        self.assertGreater(second["travel_from_previous"]["minutes_estimated"], 0)
        # Second stop starts after first end + the estimated travel leg.
        expected = 10 * 60 + 30 + second["travel_from_previous"]["minutes_estimated"]
        self.assertEqual(second["start_time"], f"{expected // 60:02d}:{expected % 60:02d}")
        self.assertIn("planning estimates", data["timing_note"])


class SqliteLockHardeningTests(TestCase):
    """`database is locked` 500s: busy timeout + WAL wiring must stay in place."""

    def test_timeout_configured_and_wal_handler_registered(self):
        from django.conf import settings as dj_settings
        from django.db import connection
        from django.db.backends.signals import connection_created
        if connection.vendor != "sqlite":
            self.skipTest("sqlite-only hardening")
        self.assertEqual(dj_settings.DATABASES["default"]["OPTIONS"]["timeout"], 20)
        import weakref
        from tourist.signals import _enable_sqlite_wal
        resolved = []
        for entry in connection_created.receivers:
            receiver = entry[1]
            fn = receiver() if isinstance(receiver, weakref.ReferenceType) else receiver
            if fn is not None:
                resolved.append(fn)
        self.assertIn(_enable_sqlite_wal, resolved)



class DistrictArchitectureTests(TestCase):
    """Task-79 §5/§24: 77-district structure + /api/v1/districts/ endpoints."""

    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command("seed_districts", verbosity=0)

    def test_seed_creates_all_77_districts_idempotently(self):
        from django.core.management import call_command
        self.assertEqual(Province.objects.count(), 7)
        self.assertEqual(District.objects.count(), 77)
        call_command("seed_districts", verbosity=0)  # second run must not duplicate
        self.assertEqual(Province.objects.count(), 7)
        self.assertEqual(District.objects.count(), 77)

    def test_rolpa_exists_in_lumbini(self):
        rolpa = District.objects.select_related("province").get(slug="rolpa")
        self.assertEqual(rolpa.province.name, "Lumbini")
        self.assertIsNotNone(rolpa.latitude)

    def test_district_list_endpoint(self):
        res = self.client.get("/api/v1/districts/")
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertEqual(payload["count"], 77)
        search = self.client.get("/api/v1/districts/?search=rolpa").json()
        self.assertEqual(search["count"], 1)
        self.assertEqual(search["results"][0]["name"], "Rolpa")
        by_province = self.client.get("/api/v1/districts/?province=koshi").json()
        self.assertEqual(by_province["count"], 14)

    def test_province_endpoint(self):
        res = self.client.get("/api/v1/provinces/").json()
        self.assertEqual(res["count"], 7)
        koshi = next(p for p in res["results"] if p["name"] == "Koshi")
        self.assertEqual(koshi["district_count"], 14)

    def test_district_detail_aggregates_real_data_and_labels_gaps(self):
        # A real published destination recorded against Rolpa must appear...
        category = Category.objects.first() or Category.objects.create(name="Test", slug="test")
        Destination.objects.create(
            name="Jaljala Himal Viewpoint", slug="jaljala-viewpoint-test",
            district="Rolpa", city_english="Rolpa",
            latitude=28.42, longitude=82.70, category=category,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )
        payload = self.client.get("/api/v1/districts/rolpa/").json()
        self.assertEqual(payload["province"], "Lumbini")
        self.assertGreaterEqual(payload["destination_count"], 1)
        names = [d["name"] for bucket in payload["destinations_by_category"].values() for d in bucket]
        self.assertIn("Jaljala Himal Viewpoint", names)
        self.assertEqual(payload["emergency_numbers"]["police"], "100")
        self.assertTrue(payload["nearby_districts"])
        # ...and unverified description stays honestly unavailable, not invented.
        self.assertEqual(payload["description"], "Information unavailable")
        # Auto-composed administrative summary states verified fields only.
        self.assertIn("Rolpa is a", payload["summary"])
        self.assertIn("Lumbini", payload["summary"])
        self.assertIn("Auto-generated", payload["summary"])

    def test_district_without_data_gets_honest_note(self):
        payload = self.client.get("/api/v1/districts/humla/").json()
        self.assertIn("data_note", payload)
        self.assertIn("No verified tourism places", payload["data_note"])

    def test_unknown_district_404(self):
        self.assertEqual(self.client.get("/api/v1/districts/atlantis/").status_code, 404)


class TravelOptionsTests(TestCase):
    """Task-79 §15/§16: destination navigation screen backend."""

    def test_travel_options_compare_modes_honestly(self):
        res = self.client.post(
            "/api/v1/navigation/travel-options/",
            {"origin_name": "Kathmandu", "destination_name": "Pashupatinath"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        modes = {option["mode"] for option in data["options"]}
        self.assertEqual(modes, {"taxi", "bus", "walk", "bicycle"})
        self.assertGreater(data["distance_km"], 0)
        self.assertIn(data["recommended"], modes)
        self.assertTrue(data["recommendation_reasons"])
        walk = next(o for o in data["options"] if o["mode"] == "walk")
        self.assertEqual(walk["cost_npr"], [0, 0])
        taxi = next(o for o in data["options"] if o["mode"] == "taxi")
        # fare_card migration seeds admin-editable estimates → labelled estimate
        self.assertIsNotNone(taxi["cost_npr"])
        self.assertIn("fare card", taxi["cost_note"])
        # No live routing provider in tests → turn-by-turn comes from the
        # bundled graph, clearly labelled as not street-level (never faked).
        if data["turn_by_turn"] is not None:
            self.assertEqual(data["turn_by_turn"]["source"], "bundled_nepal_graphml")
            self.assertIn("bundled", data["turn_by_turn_note"])
            for step in data["turn_by_turn"]["steps"]:
                self.assertIn("instruction", step)
        else:
            self.assertIn("routing provider", data["turn_by_turn_note"])

    def test_unknown_destination_404(self):
        res = self.client.post(
            "/api/v1/navigation/travel-options/",
            {"origin_name": "Kathmandu", "destination_name": "Atlantis Temple"},
            format="json",
        )
        self.assertEqual(res.status_code, 404)

    def test_missing_origin_400(self):
        res = self.client.post(
            "/api/v1/navigation/travel-options/",
            {"destination_name": "Pashupatinath"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)


class ItineraryMLGuardTests(TestCase):
    """Task-79: the ML microservice is the primary itinerary planner, but
    Django must never serve a plan built around a different place than the
    traveller requested (the ML planner defaults to Kathmandu for place
    names it does not know, e.g. the district "Kaski")."""

    def setUp(self):
        category = Category.objects.first() or Category.objects.create(name="Test", slug="test")
        Destination.objects.create(
            name="Phewa Lake", slug="phewa-lake-guard-test",
            district="Kaski", city_english="Pokhara",
            latitude=28.21, longitude=83.95, category=category,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )

    def test_plan_matching_requested_place_is_accepted(self):
        from tourist.views_ml import _ml_plan_matches_place
        payload = {"itinerary": [{"city": "Pokhara", "destinations": [{"name": "X", "city": "Pokhara"}]}]}
        self.assertTrue(_ml_plan_matches_place(payload, "Pokhara"))
        self.assertTrue(_ml_plan_matches_place(payload, ""))  # no place constraint
        self.assertTrue(_ml_plan_matches_place({"days": [{"city": "Pokhara"}]}, "pokhara"))

    def test_off_topic_plan_is_detected(self):
        from tourist.views_ml import _ml_plan_matches_place
        payload = {"itinerary": [{"city": "Kathmandu", "destinations": [{"name": "X", "city": "Kathmandu"}]}]}
        self.assertFalse(_ml_plan_matches_place(payload, "Kaski"))

    def test_off_topic_ml_response_falls_back_to_db_engine(self):
        from unittest import mock

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"itinerary": [{"city": "Kathmandu", "day": 1,
                                       "destinations": [{"name": "Ktm Place", "city": "Kathmandu"}]}]}

        with mock.patch("tourist.views_ml.requests.post", return_value=FakeResponse()):
            resp = self.client.post(
                "/api/v1/ml/itinerary/",
                {"days": 1, "start_city": "Kaski"},
                format="json",
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # The Kathmandu plan was rejected; the district-scoped DB engine ran.
        self.assertEqual(data.get("source"), "internal_db_engine")
        stops = [x for day in data["itinerary"] for x in day.get("destinations", [])]
        self.assertTrue(stops)
        for stop in stops:
            self.assertTrue(
                "kaski" in str(stop.get("district", "")).lower() or stop.get("day_trip"),
                f"off-topic stop leaked: {stop.get('name')} / {stop.get('district')}",
            )

    def test_on_topic_ml_response_is_served_and_enriched(self):
        from unittest import mock

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"total_estimated_npr": 5000,
                        "itinerary": [{"city": "Kaski", "day": 1, "theme": "lakes",
                                       "destinations": [{"name": "Phewa Lake", "city": "Pokhara",
                                                         "latitude": 28.21, "longitude": 83.95}]}]}

        with mock.patch("tourist.views_ml.requests.post", return_value=FakeResponse()):
            resp = self.client.post(
                "/api/v1/ml/itinerary/",
                {"days": 1, "start_city": "Kaski"},
                format="json",
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data.get("source"))
        self.assertEqual(data["total_estimated_npr"], 5000)
        self.assertEqual(data["service_data_source"], "live_database_distance_ranking")

class RoutingProviderStepsTests(TestCase):
    """Task-79 §15: when an admin configures a live OSRM-compatible provider,
    street-level turn-by-turn must come from it — parsed per the OSRM
    contract, using the provider's road names, never invented."""

    OSRM_ROUTE = {"code": "Ok", "routes": [{
        "distance": 2860.0,
        "duration": 480.0,
        "geometry": {"coordinates": [[85.32, 27.71], [85.33, 27.72]]},
        "legs": [{"distance": 2860.0, "duration": 480.0, "steps": [
            {"distance": 120.0, "duration": 30.0, "name": "Durbar Marg",
             "maneuver": {"type": "depart", "modifier": "north"}},
            {"distance": 900.0, "duration": 180.0, "name": "Ring Road",
             "maneuver": {"type": "turn", "modifier": "right"}},
            {"distance": 400.0, "duration": 90.0, "name": "",
             "maneuver": {"type": "roundabout", "exit": 2}},
            {"distance": 0, "duration": 0, "name": "",
             "maneuver": {"type": "arrive"}},
        ]}],
    }]}

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_step_instruction_mapping(self):
        from tourist.routing_service import _step_instruction
        self.assertEqual(
            _step_instruction({"name": "Durbar Marg", "distance": 120,
                               "maneuver": {"type": "depart"}})["instruction"],
            "Head out on Durbar Marg",
        )
        self.assertEqual(
            _step_instruction({"name": "Ring Road", "distance": 900,
                               "maneuver": {"type": "turn", "modifier": "right"}})["instruction"],
            "Turn right onto Ring Road",
        )
        self.assertIn(
            "exit 2",
            _step_instruction({"name": "", "distance": 400,
                               "maneuver": {"type": "roundabout", "exit": 2}})["instruction"],
        )
        self.assertEqual(
            _step_instruction({"name": "", "distance": 0,
                               "maneuver": {"type": "arrive"}})["instruction"],
            "Arrive at your destination",
        )

    def test_travel_options_uses_provider_steps_when_configured(self):
        from unittest.mock import MagicMock, patch
        from .models import SiteSetting
        SiteSetting.objects.filter(key="routing_provider").delete()
        SiteSetting.objects.create(
            key="routing_provider", is_public=False,
            value={"enabled": True, "base_url": "https://osrm.example.test/route/v1/driving",
                   "api_key": ""},
        )
        fake = MagicMock()
        fake.json.return_value = self.OSRM_ROUTE
        fake.raise_for_status.return_value = None
        with patch("tourist.routing_service.requests.get", return_value=fake) as mocked:
            res = self.client.post(
                "/api/v1/navigation/travel-options/",
                {"origin_name": "Kathmandu", "destination_name": "Pashupatinath"},
                format="json",
            )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        tbt = data["turn_by_turn"]
        self.assertIsNotNone(tbt)
        self.assertEqual(tbt["source"], "routing_provider")
        self.assertIsNone(data["turn_by_turn_note"])
        instructions = [step["instruction"] for step in tbt["steps"]]
        self.assertIn("Head out on Durbar Marg", instructions)
        self.assertIn("Turn right onto Ring Road", instructions)
        self.assertIn("Arrive at your destination", instructions)
        self.assertEqual(tbt["steps"][1]["road"], "Ring Road")
        self.assertTrue(tbt["geometry"])
        self.assertGreaterEqual(mocked.call_count, 1)
        self.assertIn("osrm.example.test", mocked.call_args[0][0])

class DistrictDescriptionSeedTests(TestCase):
    """Curated descriptions come only from the source-noted seed command and
    never overwrite existing (admin-entered) content."""

    def setUp(self):
        from django.core.management import call_command
        call_command("seed_districts", verbosity=0)

    def test_command_fills_only_empty_descriptions(self):
        from django.core.management import call_command
        from tourist.management.commands.seed_district_descriptions import DESCRIPTIONS
        from .models import District
        call_command("seed_district_descriptions")
        ktm = District.objects.get(slug="kathmandu")
        self.assertIn("capital district", ktm.description)
        self.assertIn("UNESCO", ktm.description)
        # every curated district got filled (catches slug drift)
        for slug in DESCRIPTIONS:
            self.assertTrue(
                (District.objects.get(slug=slug).description or "").strip(),
                f"curated district '{slug}' left empty - slug drift?",
            )
        # a second run must not touch existing content
        ktm.description = "Admin curated text."
        ktm.save()
        call_command("seed_district_descriptions")
        ktm.refresh_from_db()
        self.assertEqual(ktm.description, "Admin curated text.")
        # districts outside the curated set keep the honest gap
        from .models import Province
        province = Province.objects.first()
        fresh = District.objects.create(
            name="Test District", slug="test-district-honest-gap", province=province
        )
        call_command("seed_district_descriptions")
        fresh.refresh_from_db()
        self.assertEqual((fresh.description or "").strip(), "")


class SectionTypographyConfigTests(TestCase):
    """Section content controls: body rich text + typography config must
    survive the admin save-path (regression: custom_bg/custom_color were
    silently dropped by _safe_section_config)."""

    def test_custom_colors_and_typography_survive_safe_config(self):
        from tourist.views_admin import AdminCMSView
        safe = AdminCMSView._safe_section_config({
            "custom_bg": "#07101F",
            "custom_color": "#FFF",
            "title_color": "#1D5146",
            "font_family": "serif",
            "heading_level": "h3",
            "heading_size": "lg",
            "text_scale": "lg",
            "align": "center",
        })
        self.assertEqual(safe["custom_bg"], "#07101F")
        self.assertEqual(safe["custom_color"], "#FFF")
        self.assertEqual(safe["title_color"], "#1D5146")
        self.assertEqual(safe["font_family"], "serif")
        self.assertEqual(safe["heading_level"], "h3")
        self.assertEqual(safe["heading_size"], "lg")

    def test_invalid_values_are_rejected_or_dropped(self):
        from tourist.views_admin import AdminCMSView
        with self.assertRaises(ValueError):
            AdminCMSView._safe_section_config({"custom_bg": "red; background:url(x)"})
        with self.assertRaises(ValueError):
            AdminCMSView._safe_section_config({"title_color": "javascript:alert(1)"})
        safe = AdminCMSView._safe_section_config({"font_family": "Comic Sans", "heading_level": "h9"})
        self.assertNotIn("font_family", safe)
        self.assertNotIn("heading_level", safe)


class RouteAlternativesTests(TestCase):
    """Phase-2 alternatives selector: real alternatives only — provider
    alternatives=true when configured, different graph weightings otherwise.
    Identical corridors are dropped; failures yield [] not padded variety."""

    OSRM_THREE = {"code": "Ok", "routes": [
        {"distance": 200000.0, "duration": 14400.0,
         "geometry": {"coordinates": [[85.32, 27.71], [85.00, 27.90], [83.99, 28.21]]},
         "legs": [{"steps": [{"distance": 200000.0, "duration": 14400.0, "name": "Prithvi Highway",
                              "maneuver": {"type": "depart"}}]}]},
        {"distance": 215000.0, "duration": 15000.0,
         "geometry": {"coordinates": [[85.32, 27.71], [84.60, 27.60], [83.99, 28.21]]},
         "legs": [{"steps": [{"distance": 215000.0, "duration": 15000.0, "name": "Southern Loop",
                              "maneuver": {"type": "depart"}}]}]},
        {"distance": 230000.0, "duration": 16200.0,
         "geometry": {"coordinates": [[85.32, 27.71], [84.20, 28.10], [83.99, 28.21]]},
         "legs": [{"steps": [{"distance": 230000.0, "duration": 16200.0, "name": "Northern Loop",
                              "maneuver": {"type": "depart"}}]}]},
    ]}

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def _set_provider(self, value):
        from .models import SiteSetting
        SiteSetting.objects.filter(key="routing_provider").delete()
        SiteSetting.objects.create(key="routing_provider", value=value, is_public=False)

    def test_signature_accepts_dicts_and_arrays(self):
        from tourist.routing_service import _route_signature
        self.assertEqual(
            _route_signature([{"lat": 27.7, "lng": 85.3}, [27.8, 85.4]]),
            ((27.7, 85.3), (27.8, 85.4)),
        )
        self.assertEqual(_route_signature([]), ())
        self.assertEqual(_route_signature([{"lat": "bad"}, "junk"]), ())

    def test_provider_alternatives_parsed_per_osrm_contract(self):
        from unittest.mock import MagicMock, patch
        from tourist.routing_service import route_alternatives
        self._set_provider({"enabled": True, "base_url": "https://osrm.example.test/route/v1/driving"})
        fake = MagicMock()
        fake.json.return_value = self.OSRM_THREE
        fake.raise_for_status.return_value = None
        with patch("tourist.routing_service.requests.get", return_value=fake) as mocked:
            alts = route_alternatives(27.7172, 85.3240, 28.2096, 83.9856)
        # routes[1:3] only — the primary is routes[0]
        self.assertEqual(len(alts), 2)
        self.assertEqual(alts[0]["distance_km"], 215.0)
        self.assertEqual(alts[0]["duration_min"], 250)
        self.assertEqual(alts[0]["duration_source"], "routing_provider")
        self.assertEqual(alts[0]["routing_engine"], "osrm_protocol_provider")
        # geometry converted to the {lat,lng} contract and steps carried
        self.assertEqual(alts[0]["route"][0], {"lat": 27.71, "lng": 85.32})
        self.assertEqual(alts[0]["steps"][0]["instruction"], "Head out on Southern Loop")
        self.assertIn("alternatives", mocked.call_args.kwargs["params"])

    def test_provider_failure_degrades_to_labelled_graph_alternatives(self):
        from unittest.mock import patch
        import requests as requests_lib
        from tourist.routing_service import route_alternatives
        self._set_provider({"enabled": True, "base_url": "https://osrm.example.test/route/v1/driving"})
        with patch("tourist.routing_service.requests.get", side_effect=requests_lib.RequestException("boom")):
            alts = route_alternatives(27.7172, 85.3240, 28.2096, 83.9856)
        # same degradation path as the primary route: bundled graph,
        # explicitly labelled — never presented as provider routes
        self.assertGreaterEqual(len(alts), 1)
        for alt in alts:
            self.assertEqual(alt["routing_engine"], "bundled_nepal_graphml")
            self.assertIn("coordinate-based", alt["note"])

    def test_graph_alternatives_use_different_weightings(self):
        from .models import SiteSetting
        from tourist.routing_service import route_alternatives, _route_signature
        SiteSetting.objects.filter(key="routing_provider").delete()
        import sys
        from pathlib import Path
        ml_root = Path(__file__).resolve().parent.parent.parent / "ml_service"
        if str(ml_root) not in sys.path:
            sys.path.insert(0, str(ml_root))
        from model.route.route_engine import best_route
        primary = best_route(27.7172, 85.3240, 28.2096, 83.9856, "fastest")
        self.assertFalse(primary.get("error"))
        alts = route_alternatives(27.7172, 85.3240, 28.2096, 83.9856,
                                  primary_route_type="fastest",
                                  primary_route=primary.get("route", []))
        self.assertGreaterEqual(len(alts), 1)
        primary_sig = _route_signature(primary.get("route", []))
        for alt in alts:
            self.assertEqual(alt["routing_engine"], "bundled_nepal_graphml")
            self.assertEqual(alt["duration_source"], "estimated")
            self.assertIn("coordinate-based", alt["note"])
            self.assertNotEqual(_route_signature(alt["route"]), primary_sig,
                                "identical corridor must be discarded, not shown as an alternative")

    def test_navigation_route_attaches_alternatives(self):
        response = self.client.post("/api/v1/navigation/route", {
            "origin_name": "Kathmandu",
            "destination_name": "Pokhara",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        alts = data.get("alternatives", [])
        self.assertGreaterEqual(len(alts), 1)
        for alt in alts:
            self.assertGreaterEqual(len(alt["route"]), 2)
            self.assertEqual(alt["routing_engine"], "bundled_nepal_graphml")

    def test_tourist_bus_alternatives_get_no_invented_times(self):
        response = self.client.post("/api/v1/navigation/route", {
            "origin_name": "Kathmandu",
            "destination_name": "Pokhara",
            "transport_mode": "Tourist Bus",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        for alt in response.json().get("alternatives", []):
            self.assertIsNone(alt["duration_min"])
            self.assertEqual(alt["duration_source"], "unavailable")


class RoutingProviderAdminTests(TestCase):
    """Phase 3: admins can configure the road-routing provider from the panel
    — HTTPS-only, secret never echoed in full, honest connection test."""

    URL = "/api/v1/admin/routing-provider/"

    def _admin(self):
        client = APIClient()
        client.force_authenticate(user=make_superuser())
        return client

    def test_http_base_url_rejected(self):
        resp = self._admin().patch(self.URL, {
            "enabled": True, "base_url": "http://insecure.example.test/route/v1/driving",
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("https", resp.data["detail"])

    def test_unknown_fields_rejected(self):
        resp = self._admin().patch(self.URL, {"base_url": "https://osrm.example.test", "surprise": 1}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_https_roundtrip_key_masking_and_public_config_exclusion(self):
        client = self._admin()
        saved = client.patch(self.URL, {
            "enabled": True,
            "base_url": "https://osrm.example.test/route/v1/driving/",
            "api_key": "SECRET-1234567890",
        }, format="json")
        self.assertEqual(saved.status_code, 200, saved.content)
        self.assertTrue(saved.data["enabled"])
        self.assertEqual(saved.data["base_url"], "https://osrm.example.test/route/v1/driving")  # trailing slash trimmed
        self.assertTrue(saved.data["api_key_set"])
        self.assertEqual(saved.data["api_key_last4"], "7890")
        self.assertNotIn("SECRET-1234567890", saved.content.decode())

        fetched = client.get(self.URL)
        self.assertTrue(fetched.data["api_key_set"])
        self.assertNotIn("SECRET-1234567890", fetched.content.decode())

        # credential never leaks into the public config snapshot
        public = APIClient().get("/api/v1/config/public/").json()
        self.assertNotIn("routing_provider", public.get("settings", {}))

        # omitting api_key keeps the stored secret
        kept = client.patch(self.URL, {"enabled": False}, format="json")
        self.assertEqual(kept.status_code, 200)
        self.assertTrue(kept.data["api_key_set"])
        self.assertFalse(kept.data["enabled"])

    def test_connection_test_reports_honest_verdicts(self):
        from unittest.mock import MagicMock, patch
        import requests as requests_lib
        client = self._admin()
        client.patch(self.URL, {"enabled": True, "base_url": "https://osrm.example.test"}, format="json")

        ok = MagicMock()
        ok.json.return_value = {"code": "Ok", "routes": [{"distance": 1500.0, "duration": 300.0}]}
        ok.raise_for_status.return_value = None
        with patch("requests.get", return_value=ok):
            good = client.post(self.URL, {"action": "test"}, format="json")
        self.assertEqual(good.status_code, 200)
        self.assertTrue(good.data["ok"])
        self.assertEqual(good.data["routes_count"], 1)

        with patch("requests.get", side_effect=requests_lib.RequestException("connection refused")):
            bad = client.post(self.URL, {"action": "test"}, format="json")
        self.assertEqual(bad.status_code, 200)
        self.assertFalse(bad.data["ok"])
        self.assertIn("connection refused", bad.data["error"])

    def test_requires_authentication(self):
        resp = APIClient().get(self.URL)
        self.assertIn(resp.status_code, (401, 403))


class MultiStopRouteTests(TestCase):
    """Phase 4: multi-stop routes — every leg through the same engine and
    honesty rules; totals are leg sums; unresolvable stops are rejected."""

    URL = "/api/v1/navigation/route"
    KTM = {"latitude": 27.7172, "longitude": 85.3240}
    PKR = {"latitude": 28.2096, "longitude": 83.9856}

    def _route(self, payload):
        # DRF client — Django's default test client would multipart-encode
        # the payload and stringify the waypoints list.
        return APIClient().post(self.URL, payload, format="json")

    def test_coordinate_roundtrip_is_leg_sum(self):
        single = self._route({"start_latitude": 27.7172, "start_longitude": 85.3240,
                              "end_latitude": 28.2096, "end_longitude": 83.9856})
        self.assertEqual(single.status_code, 200, single.content)
        one_way = float(single.json()["distance_km"])

        multi = self._route({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "end_latitude": 27.7172, "end_longitude": 85.3240,
            "waypoints": [{"latitude": 28.2096, "longitude": 83.9856, "name": "Pokhara"}],
        })
        self.assertEqual(multi.status_code, 200, multi.content)
        data = multi.json()
        total = float(data["distance_km"])
        # KTM -> Pokhara -> KTM must be roughly the round trip, not one leg
        self.assertGreater(total, one_way * 1.7)
        self.assertLess(total, one_way * 2.3)
        self.assertEqual(data["waypoints"][0]["name"], "Pokhara")
        instructions = [s.get("instruction", "") for s in data.get("steps", [])]
        self.assertTrue(any("Waypoint 1: pass through Pokhara" in text for text in instructions))
        self.assertGreaterEqual(len(data["route"]), 4)
        # alternatives are a single-stop concept — none fabricated here
        self.assertNotIn("alternatives", data)

    def test_named_waypoint_resolves_through_place_index(self):
        resp = self._route({
            "origin_name": "Kathmandu",
            "destination_name": "Pokhara",
            "waypoints": ["Pokhara"],
        })
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [w["name"] for w in resp.json().get("waypoints", [])]
        self.assertEqual(len(names), 1)

    def test_unresolvable_waypoint_rejected(self):
        resp = self._route({
            "origin_name": "Kathmandu",
            "destination_name": "Pokhara",
            "waypoints": ["xyz_nonexistent_place"],
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn("waypoint", resp.json()["detail"])

    def test_more_than_three_waypoints_rejected(self):
        resp = self._route({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "end_latitude": 28.2096, "end_longitude": 83.9856,
            "waypoints": [dict(self.PKR), dict(self.PKR), dict(self.PKR), dict(self.PKR)],
        })
        self.assertEqual(resp.status_code, 400)

    def test_flight_multi_stop_rejected_without_invented_times(self):
        resp = self._route({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "end_latitude": 28.2096, "end_longitude": 83.9856,
            "transport_mode": "Flight",
            "waypoints": [dict(self.PKR)],
        })
        self.assertEqual(resp.status_code, 400)

    def test_tourist_bus_multi_stop_keeps_duration_unavailable(self):
        resp = self._route({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "end_latitude": 27.7172, "end_longitude": 85.3240,
            "transport_mode": "Tourist Bus",
            "waypoints": [dict(self.PKR)],
        })
        self.assertEqual(resp.status_code, 200, resp.content)
        data = resp.json()
        self.assertIsNone(data["duration_min"])
        self.assertEqual(data["duration_source"], "unavailable")
        self.assertGreater(float(data["distance_km"]), 400)


class TravelOptionsMultiStopTests(TestCase):
    """Phase 6+: travel-options gains the same waypoints contract as
    /navigation/route — distances become leg sums, honestly labelled."""

    URL = "/api/v1/navigation/travel-options/"

    def _post(self, payload):
        return APIClient().post(self.URL, payload, format="json")

    def test_multi_stop_leg_sum_and_flags(self):
        single = self._post({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "destination_name": "Pokhara",
        })
        self.assertEqual(single.status_code, 200, single.content)
        self.assertFalse(single.json()["multi_stop"])

        multi = self._post({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "destination_name": "Pokhara",
            "waypoints": [{"latitude": 27.578, "longitude": 84.499, "name": "Chitwan"}],
        })
        self.assertEqual(multi.status_code, 200, multi.content)
        data = multi.json()
        self.assertTrue(data["multi_stop"])
        self.assertEqual(data["waypoints"][0]["name"], "Chitwan")
        self.assertEqual(len(data["options"]), 4)
        taxi = next(o for o in data["options"] if o["mode"] == "taxi")
        self.assertGreater(float(taxi["distance_km"]), 100)
        # the via-Chitwan corridor must not silently reuse the direct figure
        single_km = float(next(o for o in single.json()["options"] if o["mode"] == "taxi")["distance_km"])
        self.assertNotAlmostEqual(float(taxi["distance_km"]), single_km, delta=1.0)

    def test_unresolvable_waypoint_rejected(self):
        resp = self._post({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "destination_name": "Pokhara",
            "waypoints": ["xyz_nonexistent_stop"],
        })
        self.assertEqual(resp.status_code, 404)

    def test_more_than_three_waypoints_rejected(self):
        resp = self._post({
            "start_latitude": 27.7172, "start_longitude": 85.3240,
            "destination_name": "Pokhara",
            "waypoints": [
                {"latitude": 27.6, "longitude": 84.4}, {"latitude": 27.5, "longitude": 84.3},
                {"latitude": 27.4, "longitude": 84.2}, {"latitude": 27.3, "longitude": 84.1},
            ],
        })
        self.assertEqual(resp.status_code, 400)


class AdminDataExplorerCRUDRegressionTests(TestCase):
    """Pins the generic Data Explorer CRUD + rich-text hardening (post-8cc83d4)."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())
        self.url = "/api/v1/admin/data-explorer/"

    def _destination(self):
        return Destination.objects.create(name="CRUD Fixture City", latitude=27.7, longitude=85.3)

    def _hospital(self, **kw):
        defaults = dict(name="Regression Test Hospital", district="Kathmandu", latitude=27.71, longitude=85.32, phone="01-4000000", address="Regression Test Road", destination=self._destination())
        defaults.update(kw)
        return Hospital.objects.create(**defaults)

    def test_unauthenticated_rejected(self):
        c = APIClient()
        self.assertEqual(c.get(self.url, {"resource": "hospitals"}).status_code, 401)

    def test_schema_lists_editable_fields(self):
        resp = self.client.get(self.url, {"resource": "hospitals", "schema": "1"})
        self.assertEqual(resp.status_code, 200)
        names = [f["name"] for f in resp.json()["editable"]]
        self.assertIn("name", names)
        self.assertIn("district", names)

    def test_patch_updates_and_reports_changed_fields(self):
        h = self._hospital()
        resp = self.client.patch(self.url, {
            "resource": "hospitals", "id": h.id, "fields": {"district": "Lalitpur"}
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["message"], "Record updated")
        self.assertIn("district", body["changed"])
        h.refresh_from_db()
        self.assertEqual(h.district, "Lalitpur")

    def test_patch_rejects_unknown_field(self):
        h = self._hospital()
        resp = self.client.patch(self.url, {
            "resource": "hospitals", "id": h.id, "fields": {"definitely_not_a_field": "x"}
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_patch_rejects_out_of_bounds_integer(self):
        h = self._hospital()
        resp = self.client.patch(self.url, {
            "resource": "hospitals", "id": h.id, "fields": {"latitude": 999999999999}
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_post_creates_then_delete_removes(self):
        # newsletter_signups has no required FKs, so generic create applies
        resp = self.client.post(self.url, {
            "resource": "newsletter_signups", "fields": {"email": "crud-created@test.local"}
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        new_id = resp.json()["id"]
        resp = self.client.delete(f"{self.url}?resource=newsletter_signups&id={new_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(NewsletterSignup.objects.filter(id=new_id).exists())

    def test_post_missing_required_returns_400(self):
        resp = self.client.post(self.url, {"resource": "hospitals", "fields": {"district": "Kathmandu"}}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_unknown_resource_rejected(self):
        self.assertEqual(self.client.get(self.url, {"resource": "not_a_model"}).status_code, 400)

    def test_destination_writes_routed_to_dedicated_editor(self):
        d = Destination.objects.create(name="CRUD Guard Dest", latitude=27.7, longitude=85.3)
        resp = self.client.patch(self.url, {
            "resource": "destinations", "id": d.id, "fields": {"name": "hacked"}
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("dedicated", str(resp.json()))


class DestinationRichTextHardeningTests(TestCase):
    """javascript: URLs in rich-text fields are neutralized on save."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())

    def test_javascript_href_neutralized(self):
        d = Destination.objects.create(name="RichText Guard", latitude=27.7, longitude=85.3)
        resp = self.client.put(
            f"/api/v1/admin/destinations/{d.id}",
            {
                "name": "RichText Guard",
                "description": '<p>ok</p><a href="javascript:alert(1)">x</a>',
            },
            format="json",
        )
        self.assertIn(resp.status_code, (200, 201))
        d.refresh_from_db()
        self.assertNotIn("javascript:", d.description.lower())
        self.assertIn("<p>ok</p>", d.description)


class CMSDuplicateRegressionTests(TestCase):
    """Blueprint: admin can duplicate pages (with sections) and sections."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())
        self.url = "/api/v1/admin/cms/"
        self.page = ManagedPage.objects.create(key="dup-source", route="/dup-source", title="Dup Source", status="published", is_enabled=True)
        ContentSection.objects.create(page=self.page, key="hero", title="Hero", section_type="hero", display_order=1)
        ContentSection.objects.create(page=self.page, key="faq", title="FAQ", section_type="faq", display_order=2)

    def test_duplicate_page_copies_sections_as_draft(self):
        resp = self.client.patch(self.url, {"resource": "pages", "id": self.page.pk, "action": "duplicate"}, format="json")
        self.assertEqual(resp.status_code, 200)
        new_id = resp.json()["id"]
        new_page = ManagedPage.objects.get(pk=new_id)
        self.assertEqual(new_page.status, "draft")
        self.assertFalse(new_page.is_enabled)
        self.assertNotEqual(new_page.key, self.page.key)
        self.assertEqual(new_page.sections.count(), 2)
        self.assertEqual(set(new_page.sections.values_list("title", flat=True)), {"Hero", "FAQ"})
        # source untouched
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")

    def test_duplicate_twice_gets_unique_keys(self):
        r1 = self.client.patch(self.url, {"resource": "pages", "id": self.page.pk, "action": "duplicate"}, format="json")
        r2 = self.client.patch(self.url, {"resource": "pages", "id": self.page.pk, "action": "duplicate"}, format="json")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertNotEqual(r1.json()["id"], r2.json()["id"])

    def test_duplicate_section_appends_draft_copy(self):
        hero = self.page.sections.get(key="hero")
        resp = self.client.patch(self.url, {"resource": "sections", "id": hero.pk, "action": "duplicate"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.page.sections.count(), 3)
        copy = ContentSection.objects.get(pk=resp.json()["id"])
        self.assertEqual(copy.status, "draft")
        self.assertNotEqual(copy.key, hero.key)
        self.assertGreater(copy.display_order, hero.display_order)

    def test_duplicate_rejected_for_settings(self):
        setting = SiteSetting.objects.create(key="dup-test", value="x")
        resp = self.client.patch(self.url, {"resource": "settings", "id": setting.pk, "action": "duplicate"}, format="json")
        self.assertEqual(resp.status_code, 400)


class DynamicPageFlowRegressionTests(TestCase):
    """Blueprint proof: admin creates a page -> template -> publish -> public
    API serves it, with NO React code change (frontend /page/:slug route)."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())
        self.url = "/api/v1/admin/cms/"

    def test_create_template_publish_reaches_public_api(self):
        r = self.client.post(self.url, {
            "resource": "pages", "key": "winter-proof", "route": "/winter-proof",
            "title": "Winter Proof", "status": "draft", "is_enabled": True,
        }, format="json")
        self.assertEqual(r.status_code, 201)
        pid = r.json()["id"]
        r = self.client.patch(self.url, {"resource": "pages", "id": pid, "action": "apply_template", "template": "landing"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(r.json()["created"], 0)
        # draft must NOT be public yet
        pub = self.client.get("/api/v1/config/public/").json()
        self.assertIsNone(next((p for p in pub["pages"] if p["key"] == "winter-proof"), None))
        # publish page + sections
        self.assertEqual(self.client.patch(self.url, {"resource": "pages", "id": pid, "action": "publish"}, format="json").status_code, 200)
        for sec in ContentSection.objects.filter(page_id=pid):
            self.client.patch(self.url, {"resource": "sections", "id": sec.pk, "action": "publish"}, format="json")
        pub = self.client.get("/api/v1/config/public/").json()
        page = next((p for p in pub["pages"] if p["key"] == "winter-proof"), None)
        self.assertIsNotNone(page)
        self.assertGreater(len(page["sections"]), 0)

    def test_section_edit_stays_draft_until_publish(self):
        page = ManagedPage.objects.create(key="snap-proof", route="/snap-proof", title="Snap", status="published", is_enabled=True)
        sec = ContentSection.objects.create(page=page, key="body", title="Original", section_type="text", status="published")
        from tourist.cms_publishing import sync_published_snapshot
        sync_published_snapshot(sec)
        # plain update: public keeps the frozen snapshot
        self.client.patch(self.url, {"resource": "sections", "id": sec.pk, "title": "Changed Draft"}, format="json")
        pub = self.client.get("/api/v1/config/public/").json()
        served = next(s for p in pub["pages"] if p["key"] == "snap-proof" for s in p["sections"] if s["key"] == "body")
        self.assertEqual(served["title"], "Original")
        # publish refreshes it
        self.client.patch(self.url, {"resource": "sections", "id": sec.pk, "action": "publish"}, format="json")
        pub = self.client.get("/api/v1/config/public/").json()
        served = next(s for p in pub["pages"] if p["key"] == "snap-proof" for s in p["sections"] if s["key"] == "body")
        self.assertEqual(served["title"], "Changed Draft")

    def test_dynamic_nav_item_reaches_public_api(self):
        r = self.client.post(self.url, {
            "resource": "navigation", "location": "navbar", "label": "Winter Nav Proof",
            "route": "/page/winter-proof", "display_order": 99, "is_active": True,
        }, format="json")
        self.assertEqual(r.status_code, 201)
        pub = self.client.get("/api/v1/config/public/").json()
        labels = [n.get("label") for n in pub.get("navigation", [])]
        self.assertIn("Winter Nav Proof", labels)


class RBACAttackRegressionTests(TestCase):
    """Blueprint §9-10: backend enforcement, not hidden buttons. ID-swapping
    must never expose another user's private records."""

    def setUp(self):
        self.a = User.objects.create_user(email="user-a@test.local", password="Passw0rd!Aa", role="TRAVELLER")
        self.b = User.objects.create_user(email="user-b@test.local", password="Passw0rd!Bb", role="TRAVELLER")
        self.dest = Destination.objects.create(name="RBAC Dest", latitude=27.7, longitude=85.3)

    def _client(self, user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    def test_traveller_cannot_create_or_publish_cms(self):
        c = self._client(self.a)
        self.assertIn(c.post("/api/v1/admin/cms/", {
            "resource": "pages", "key": "hacked", "route": "/hacked", "title": "Hacked",
        }, format="json").status_code, (401, 403))

    def test_traveller_cannot_write_data_explorer(self):
        c = self._client(self.a)
        self.assertIn(c.patch("/api/v1/admin/data-explorer/", {
            "resource": "hospitals", "id": 1, "fields": {"name": "hacked"},
        }, format="json").status_code, (401, 403))

    def test_id_swap_cannot_see_other_users_favorites(self):
        from .models import Favorite
        fav = Favorite.objects.create(user=self.a, destination=self.dest)
        cb = self._client(self.b)
        # list isolation
        listed = cb.get("/api/v1/favorites/").json()
        rows = listed.get("results", listed) if isinstance(listed, dict) else listed
        self.assertNotIn(fav.pk, [r["id"] for r in rows])
        # direct ID access + delete must not expose or destroy
        self.assertEqual(cb.get(f"/api/v1/favorites/{fav.pk}/").status_code, 404)
        self.assertEqual(cb.delete(f"/api/v1/favorites/{fav.pk}/").status_code, 404)
        self.assertTrue(Favorite.objects.filter(pk=fav.pk).exists())
        # owner still can
        ca = self._client(self.a)
        self.assertEqual(ca.get(f"/api/v1/favorites/{fav.pk}/").status_code, 200)

    def test_anonymous_cannot_reach_admin_cms_at_all(self):
        c = APIClient()
        self.assertEqual(c.get("/api/v1/admin/cms/", {"resource": "pages"}).status_code, 401)


class ScheduledExpiryRegressionTests(TestCase):
    """Blueprint §14: scheduled unpublish/expire executes automatically."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())

    def test_expired_section_auto_hidden_and_future_scheduled_hidden(self):
        from datetime import timedelta
        page = ManagedPage.objects.create(key="expiry-proof", route="/expiry-proof", title="Expiry", status="published", is_enabled=True)
        today = timezone.now().date()
        expired = ContentSection.objects.create(page=page, key="old", title="Expired Promo", section_type="text", status="published",
                                                config={"visibility": {"end_date": (today - timedelta(days=1)).isoformat()}})
        upcoming = ContentSection.objects.create(page=page, key="soon", title="Winter Promo", section_type="text", status="published",
                                                 config={"visibility": {"start_date": (today + timedelta(days=5)).isoformat()}})
        current = ContentSection.objects.create(page=page, key="now", title="Live Now", section_type="text", status="published")
        pub = self.client.get("/api/v1/config/public/").json()
        served = {s["key"] for p in pub["pages"] if p["key"] == "expiry-proof" for s in p["sections"]}
        self.assertNotIn("old", served)   # auto-expired
        self.assertNotIn("soon", served)  # not yet started
        self.assertIn("now", served)
        self.assertEqual(expired.status, "published")  # record intact, just hidden
        self.assertEqual(upcoming.status, "published")


class MediaDeletionProtectionTests(TestCase):
    """Media referenced by published CMS content cannot be blindly deleted."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())
        self.dest = Destination.objects.create(name="Media Guard Dest", latitude=27.7, longitude=85.3)

    def _image(self, url):
        from tourist.models import DestinationImage
        return DestinationImage.objects.create(destination=self.dest, external_url=url, source="test")

    def test_referenced_image_blocked_then_forced(self):
        from tourist.models import DestinationImage
        url = "https://cdn.test/used-by-cms.jpg"
        img = self._image(url)
        page = ManagedPage.objects.create(key="media-guard", route="/media-guard", title="Media Guard", status="published", is_enabled=True)
        ContentSection.objects.create(page=page, key="hero", title="Hero", section_type="hero",
                                      image_url=url, status="published", is_visible=True)
        r = self.client.delete(f"/api/v1/admin/images/{img.pk}")
        self.assertEqual(r.status_code, 409)
        self.assertIn("Media Guard", str(r.json().get("used_by")))
        self.assertTrue(DestinationImage.objects.filter(pk=img.pk).exists())
        # explicit force override still available
        r = self.client.delete(f"/api/v1/admin/images/{img.pk}?force=1")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(DestinationImage.objects.filter(pk=img.pk).exists())

    def test_unreferenced_image_deletes_normally(self):
        from tourist.models import DestinationImage
        img = self._image("https://cdn.test/not-used-anywhere.jpg")
        r = self.client.delete(f"/api/v1/admin/images/{img.pk}")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(DestinationImage.objects.filter(pk=img.pk).exists())


class SEOSitemapRegressionTests(TestCase):
    """Sitemap exposes published pages only; robots points at the sitemap."""

    def test_sitemap_includes_published_excludes_draft(self):
        ManagedPage.objects.create(key="seo-live", route="/seo-live", title="SEO Live", status="published", is_enabled=True)
        ManagedPage.objects.create(key="seo-draft", route="/seo-draft", title="SEO Draft", status="draft", is_enabled=True)
        body = self.client.get("/api/v1/seo/sitemap.xml").content.decode()
        self.assertIn("/page/seo-live", body)
        self.assertNotIn("seo-draft", body)
        self.assertTrue(body.startswith("<?xml"))

    def test_robots_references_sitemap_and_blocks_admin(self):
        body = self.client.get("/api/v1/seo/robots.txt").content.decode()
        self.assertIn("Sitemap:", body)
        self.assertIn("Disallow: /admin", body)


class LocalizationRegressionTests(TestCase):
    """Blueprint §14: one record, many languages — ?lang=ne serves the
    translation; English falls back to the source fields."""

    def test_translation_served_per_language(self):
        page = ManagedPage.objects.create(key="loc-page", route="/loc-page", title="Visit Nepal", status="published", is_enabled=True)
        sec = ContentSection.objects.create(page=page, key="intro", title="Welcome", body="Hello", section_type="text", status="published", is_visible=True)
        from .models import CMSContentTranslation
        CMSContentTranslation.objects.create(target_resource="pages", object_id=page.pk, language_code="ne", content={"title": "नेपाल भ्रमण"})
        CMSContentTranslation.objects.create(target_resource="sections", object_id=sec.pk, language_code="ne", content={"title": "स्वागत छ", "body": "नमस्ते"})
        en = self.client.get("/api/v1/config/public/").json()
        page_en = next(p for p in en["pages"] if p["key"] == "loc-page")
        self.assertEqual(page_en["title"], "Visit Nepal")
        ne = self.client.get("/api/v1/config/public/?lang=ne").json()
        page_ne = next(p for p in ne["pages"] if p["key"] == "loc-page")
        self.assertEqual(page_ne["title"], "नेपाल भ्रमण")
        sec_ne = next(s for s in page_ne["sections"] if s["key"] == "intro")
        self.assertEqual(sec_ne["title"], "स्वागत छ")
        self.assertEqual(sec_ne["body"], "नमस्ते")
        # untranslated language falls back to source, never to another translation
        hi = self.client.get("/api/v1/config/public/?lang=hi").json()
        page_hi = next(p for p in hi["pages"] if p["key"] == "loc-page")
        self.assertEqual(page_hi["title"], "Visit Nepal")


class ReviewWorkflowRegressionTests(TestCase):
    """Blueprint §7: draft -> in_review -> approved -> published, with
    changes_requested loop; review states never public."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())
        self.url = "/api/v1/admin/cms/"
        self.page = ManagedPage.objects.create(key="wf-page", route="/wf-page", title="WF", status="draft", is_enabled=True)

    def _act(self, action):
        return self.client.patch(self.url, {"resource": "pages", "id": self.page.pk, "action": action}, format="json")

    def test_full_workflow_and_public_exposure(self):
        self.assertEqual(self._act("submit_review").status_code, 200)
        self.page.refresh_from_db(); self.assertEqual(self.page.status, "in_review")
        pub = self.client.get("/api/v1/config/public/").json()
        self.assertIsNone(next((p for p in pub["pages"] if p["key"] == "wf-page"), None))
        self.assertEqual(self._act("request_changes").status_code, 200)
        self.page.refresh_from_db(); self.assertEqual(self.page.status, "changes_requested")
        self.assertEqual(self._act("submit_review").status_code, 200)
        self.assertEqual(self._act("approve").status_code, 200)
        self.page.refresh_from_db(); self.assertEqual(self.page.status, "approved")
        pub = self.client.get("/api/v1/config/public/").json()
        self.assertIsNone(next((p for p in pub["pages"] if p["key"] == "wf-page"), None))
        self.assertEqual(self._act("publish").status_code, 200)
        pub = self.client.get("/api/v1/config/public/").json()
        self.assertIsNotNone(next((p for p in pub["pages"] if p["key"] == "wf-page"), None))

    def test_invalid_transition_rejected(self):
        # draft cannot be "request_changes" target from published-only states
        self.page.status = "published"; self.page.save()
        self.assertEqual(self._act("approve").status_code, 400)


class RoleDifferentiatedApprovalTests(TestCase):
    """Content staff can edit/submit; only content.publish may approve/publish."""

    def setUp(self):
        from .models import StaffCapabilityProfile
        self.editor = User.objects.create_user(email="editor@test.local", password="Passw0rd!Ee", role="STAFF", is_staff=True)
        StaffCapabilityProfile.objects.create(user=self.editor, capabilities={"content": ["view", "change"]})
        self.page = ManagedPage.objects.create(key="rd-page", route="/rd-page", title="RD", status="draft", is_enabled=True)

    def _client(self):
        c = APIClient(); c.force_authenticate(user=self.editor); return c

    def test_editor_submits_but_cannot_approve_or_publish(self):
        c = self._client()
        r = c.patch("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.pk, "action": "submit_review"}, format="json")
        self.assertEqual(r.status_code, 200)
        r = c.patch("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.pk, "action": "approve"}, format="json")
        self.assertEqual(r.status_code, 403)
        r = c.patch("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.pk, "action": "publish"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_super_admin_can_approve_and_publish(self):
        c = APIClient(); c.force_authenticate(user=make_superuser())
        self.assertEqual(c.patch("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.pk, "action": "submit_review"}, format="json").status_code, 200)
        self.assertEqual(c.patch("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.pk, "action": "approve"}, format="json").status_code, 200)
        self.assertEqual(c.patch("/api/v1/admin/cms/", {"resource": "pages", "id": self.page.pk, "action": "publish"}, format="json").status_code, 200)


class SectionConfigSanitizerRegressionTests(TestCase):
    """Panel saves must PRESERVE admin content collections (cards, badge,
    section_titles, foods, all_symbols) while sanitizing them — the old
    whitelist silently destroyed them on every save."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())
        self.page = ManagedPage.objects.create(key="san-page", route="/san-page", title="San", status="published", is_enabled=True)
        self.sec = ContentSection.objects.create(page=self.page, key="s1", title="S", section_type="cards", status="published", is_visible=True)

    def test_content_collections_survive_save(self):
        cfg = {
            "badge": "Test Badge",
            "section_titles": {"unesco": "Heritage", "bad key!!": "x"},
            "cards": [{"title": "Card <script>alert(1)</script>One", "image_url": "/images/x.jpg", "to": "/destinations", "items": [{"name": "Sub", "to": "/d"}]}],
            "foods": [{"name": "MoMo", "image": "https://cdn.test/m.jpg"}],
            "all_symbols": [{"title": "Flag", "image": "javascript:alert(1)"}],
            "visibility": {"end_date": "2030-01-01"},
        }
        r = self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.sec.pk, "config": cfg}, format="json")
        self.assertEqual(r.status_code, 200)
        self.sec.refresh_from_db()
        c = self.sec.config
        self.assertEqual(c["badge"], "Test Badge")
        self.assertEqual(c["section_titles"], {"unesco": "Heritage", "badkey": "x"})  # key normalized
        self.assertEqual(c["cards"][0]["title"], "Card One")  # script stripped
        self.assertEqual(c["cards"][0]["image_url"], "/images/x.jpg")
        self.assertEqual(c["cards"][0]["items"][0]["name"], "Sub")
        self.assertEqual(c["foods"][0]["image"], "https://cdn.test/m.jpg")
        self.assertNotIn("image", c["all_symbols"][0])  # javascript: URL dropped
        self.assertEqual(c["visibility"], {"end_date": "2030-01-01"})

    def test_media_url_rule_still_enforced(self):
        r = self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.sec.pk,
            "config": {"media_url": "http://insecure.test/x.jpg"}}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_topic_and_faq_cards_survive_save(self):
        cfg = {
            "topic_cards": [
                {"id": "curation", "title": "How Curation Works", "titleBadge": "Standard",
                 "content": "Official registries.", "highlights": ["Verified GPS.", "Categorized."]},
            ],
            "faq_cards": [{"q": "Why unavailable?", "a": "We never fabricate data."}],
        }
        resp = self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.sec.pk, "config": cfg}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.sec.refresh_from_db()
        got = self.sec.config
        self.assertEqual(len(got.get("topic_cards", [])), 1)
        self.assertEqual(got["topic_cards"][0]["highlights"], ["Verified GPS.", "Categorized."])
        self.assertEqual(got["topic_cards"][0]["titlebadge"], "Standard")  # key normalized, value kept
        self.assertEqual(len(got.get("faq_cards", [])), 1)

    def test_topic_cards_malicious_input_sanitized(self):
        cfg = {"topic_cards": [
            {"id": "x", "title": "<script>alert(1)</script>Safe Title",
             "image_url": "javascript:alert(1)", "highlights": ["<b>ok</b>"] * 20},
        ]}
        resp = self.client.patch("/api/v1/admin/cms/", {"resource": "sections", "id": self.sec.pk, "config": cfg}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.sec.refresh_from_db()
        rec = self.sec.config["topic_cards"][0]
        self.assertNotIn("<script>", rec["title"])
        self.assertNotIn("image_url", rec)  # javascript: URL dropped
        self.assertLessEqual(len(rec["highlights"]), 12)

class MunicipalityMappingTests(TestCase):
    """Admin-verified municipality -> district mapping workflow (V3)."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=make_superuser())

    def test_csv_import_validates_districts(self):
        csv_text = (
            "name,district,province\n"
            "Besisahar Municipality,Lamjung,\n"
            "Fakeville,Not A District,\n"
            ",Kaski,\n"
        )
        resp = self.client.post("/api/v1/admin/geo/municipalities/", {"csv": csv_text}, format="json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["created"], 1)
        self.assertEqual(len(data["rejected"]), 2)
        m = MunicipalityMapping.objects.get(name="Besisahar Municipality")
        self.assertEqual(m.district, "Lamjung")
        self.assertEqual(m.province, "Gandaki")  # derived from district table
        self.assertTrue(m.verified)

    def test_unverified_candidates_never_write_destinations(self):
        from tourist.municipality_mappings import backfill_provinces
        MunicipalityMapping.objects.create(
            name="Somegaun", district="Kaski", province="Gandaki",
            source="coordinate_derived", verified=False)
        dest = Destination.objects.create(name="Test Place", district="Somegaun",
                                          latitude=28.2, longitude=83.99, province=None)
        result = backfill_provinces(dry_run=False)
        dest.refresh_from_db()
        self.assertIsNone(dest.province)  # unverified -> no write
        self.assertEqual(result["pending_verification"], 1)
        MunicipalityMapping.objects.filter(name="Somegaun").update(verified=True)
        backfill_provinces(dry_run=False)
        dest.refresh_from_db()
        self.assertEqual(dest.province, "Gandaki")  # verified -> backfilled

    def test_admin_can_verify_via_api(self):
        m = MunicipalityMapping.objects.create(name="Xgaun", district="Kaski",
                                               province="Gandaki", source="coordinate_derived")
        resp = self.client.patch("/api/v1/admin/geo/municipalities/",
                                 {"id": m.pk, "verified": True}, format="json")
        self.assertEqual(resp.status_code, 200)
        m.refresh_from_db()
        self.assertTrue(m.verified)

class UniversalSearchNationwideTests(TestCase):
    """Text search must not be silently centered on Pokhara when no GPS given."""

    def test_search_without_gps_finds_far_provinces(self):
        from tourist.location.search_service import LocationSearchService
        cat, _ = Category.objects.get_or_create(name="Pilgrimage")
        Destination.objects.create(name="Lumbini Test Temple", slug="lumbini-test-temple",
                                   category=cat, province="Lumbini", district="Rupandehi",
                                   latitude=27.47, longitude=83.28, is_active=True, status="approved")
        results = LocationSearchService.search_places(query="lumbini", limit=10)
        names = [r["name"] for r in results]
        self.assertIn("Lumbini Test Temple", names)

    def test_search_with_gps_still_respects_radius(self):
        from tourist.location.search_service import LocationSearchService
        cat, _ = Category.objects.get_or_create(name="Pilgrimage")
        Destination.objects.create(name="Faraway Lumbini Place", slug="faraway-lumbini-place",
                                   category=cat, province="Lumbini", district="Rupandehi",
                                   latitude=27.47, longitude=83.28, is_active=True, status="approved")
        # GPS in Kathmandu, 10 km radius -> Lumbini (150+ km away) must be excluded
        results = LocationSearchService.search_places(query="lumbini", user_lat=27.7172,
                                                      user_lng=85.324, radius_km=10, limit=10)
        names = [r["name"] for r in results]
        self.assertNotIn("Faraway Lumbini Place", names)
