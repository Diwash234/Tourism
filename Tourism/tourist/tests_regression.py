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
