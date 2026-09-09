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
from rest_framework.test import APIClient

from .location.search_service import LocationSearchService
from .models import (
    User,
    StaffCapabilityProfile,
    Category,
    Destination,
    Hospital,
    Hotel,
    UserFeedback,
    NotificationPreference,
    ManagedNavigationItem,
    ManagedPage,
    ContentSection,
    UserRoute,
)


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
