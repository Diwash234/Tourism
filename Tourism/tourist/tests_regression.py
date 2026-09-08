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

from .models import (
    User,
    UserFeedback,
    NotificationPreference,
    ManagedNavigationItem,
    ManagedPage,
    ContentSection,
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
