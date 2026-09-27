"""Regression tests for the release audit: privacy rights (account deletion,
newsletter unsubscribe), traveller features (search, decide, season guide,
sentiment, plan sharing, itinerary anchoring), CMS block validation and the
SPA fallback."""
import json
import tempfile
from pathlib import Path

from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from .models import (Category, ContentSection, Destination, ManagedPage, NewsletterSignup,
                     TravelPlan, TrustedContact, User)
from .views_account import unsubscribe_token


def make_dest(owner, category, name, lat, lon, district, **extra):
    return Destination.objects.create(
        name=name, category=category, description="Recorded place.", latitude=lat, longitude=lon,
        district=district, created_by=owner, status=Destination.SubmissionStatus.APPROVED, is_active=True, **extra)


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="traveller@example.com", password="Str0ng!Pass1", first_name="Asha")
        NewsletterSignup.objects.create(email="traveller@example.com")
        TravelPlan.objects.create(user=self.user, title="Annapurna", itinerary_data={"notes": "private"})
        self.client.force_authenticate(self.user)

    def test_requires_login(self):
        self.assertEqual(APIClient().post("/api/v1/auth/account/delete/", {}).status_code, 401)

    def test_kept_booking_records_lose_contact_details(self):
        from tourist.models import MarketplaceOrder
        order = MarketplaceOrder.objects.create(user=self.user, guest_name="Asha K", guest_email="asha@example.com", guest_phone="+977 9800000000", notes="vegetarian")
        r = self.client.post("/api/v1/auth/account/delete/", {"password": "Str0ng!Pass1"})
        self.assertEqual(r.status_code, 200)
        order.refresh_from_db()
        self.assertEqual((order.guest_name, order.guest_email, order.guest_phone, order.notes), ("Deleted User", "", "", ""))

    def test_profile_reports_whether_a_password_exists(self):
        self.assertIs(self.client.get("/api/v1/auth/profile/").json().get("has_password"), True)

    def test_wrong_password_keeps_account(self):
        r = self.client.post("/api/v1/auth/account/delete/", {"password": "nope"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["field"], "password")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.email, "traveller@example.com")

    def test_deletes_personal_records_and_anonymises(self):
        r = self.client.post("/api/v1/auth/account/delete/", {"password": "Str0ng!Pass1"})
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertTrue(body["deleted"])
        self.assertIn("kept", body)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.email.endswith("@deleted.invalid"))
        self.assertEqual(self.user.first_name, "Deleted")
        self.assertFalse(self.user.has_usable_password())
        self.assertFalse(TravelPlan.objects.filter(user=self.user).exists())
        self.assertFalse(NewsletterSignup.objects.filter(email="traveller@example.com").exists())
        # The old credentials no longer work.
        login = APIClient().post("/api/v1/auth/login/", {"email": "traveller@example.com", "password": "Str0ng!Pass1"}, format="json")
        self.assertNotEqual(login.status_code, 200)

    def test_oauth_account_confirms_with_email(self):
        oauth = User.objects.create_user(email="gh@example.com", password=None)
        oauth.set_unusable_password(); oauth.save()
        c = APIClient(); c.force_authenticate(oauth)
        self.assertEqual(c.post("/api/v1/auth/account/delete/", {"confirm_email": "other@example.com"}).status_code, 400)
        self.assertEqual(c.post("/api/v1/auth/account/delete/", {"confirm_email": "GH@example.com"}).status_code, 200)

    def test_superuser_cannot_self_delete(self):
        admin = User.objects.create_superuser(email="root@example.com", password="Admin!Pass123")
        c = APIClient(); c.force_authenticate(admin)
        self.assertEqual(c.post("/api/v1/auth/account/delete/", {"password": "Admin!Pass123"}).status_code, 403)


class NewsletterTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_subscribe_reply_does_not_reveal_existing_subscribers(self):
        first = self.client.post("/api/v1/newsletter/subscribe/", {"email": "a@example.com"}, format="json")
        again = self.client.post("/api/v1/newsletter/subscribe/", {"email": "a@example.com"}, format="json")
        self.assertEqual(first.json()["message"], again.json()["message"])

    def test_unsubscribe_with_signed_link(self):
        NewsletterSignup.objects.create(email="b@example.com")
        r = self.client.post("/api/v1/newsletter/unsubscribe/", {"token": unsubscribe_token("b@example.com")}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(NewsletterSignup.objects.get(email="b@example.com").is_active)

    def test_tampered_token_rejected(self):
        r = self.client.post("/api/v1/newsletter/unsubscribe/", {"token": unsubscribe_token("b@example.com") + "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_unsubscribe_by_email_same_reply_for_unknown_address(self):
        NewsletterSignup.objects.create(email="c@example.com")
        known = self.client.post("/api/v1/newsletter/unsubscribe/", {"email": "c@example.com"}, format="json")
        unknown = self.client.post("/api/v1/newsletter/unsubscribe/", {"email": "nobody@example.com"}, format="json")
        self.assertEqual(known.json(), unknown.json())
        self.assertFalse(NewsletterSignup.objects.get(email="c@example.com").is_active)

    def test_export_is_admin_only_and_includes_unsubscribe_links(self):
        NewsletterSignup.objects.create(email="d@example.com")
        self.assertIn(self.client.get("/api/v1/admin/newsletter/export.csv").status_code, (401, 403))
        admin = User.objects.create_superuser(email="ops@example.com", password="Admin!Pass123")
        self.client.force_authenticate(admin)
        r = self.client.get("/api/v1/admin/newsletter/export.csv")
        self.assertEqual(r.status_code, 200)
        text = r.content.decode()
        self.assertIn("d@example.com", text)
        self.assertIn("/unsubscribe?token=", text)


class TravellerFeatureTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(email="data@example.com", password="Admin!Pass123")
        self.cat = Category.objects.create(name="Trekking")
        self.namche = make_dest(self.admin, self.cat, "Namche Bazaar", 27.8069, 86.7140, "Solukhumbu")
        self.lukla = make_dest(self.admin, self.cat, "Lukla", 27.6870, 86.7314, "Solukhumbu")
        self.tengboche = make_dest(self.admin, self.cat, "Tengboche Monastery", 27.8362, 86.7646, "Solukhumbu")
        self.far_west = make_dest(self.admin, self.cat, "Khaptad National Park", 29.3833, 81.1333, "Doti")
        self.pokhara = make_dest(self.admin, self.cat, "Phewa Lake", 28.2096, 83.9591, "Kaski", city="Pokhara")
        self.client = APIClient()

    def test_search_finds_misspelling(self):
        r = self.client.get("/api/v1/search/", {"q": "namchee"})
        self.assertEqual(r.status_code, 200)
        titles = [i["title"] for g in r.json().get("groups", []) for i in g["items"]]
        self.assertTrue(any("Namche" in t for t in titles) or "namche" in json.dumps(r.json()).lower())

    def test_decide_validation(self):
        self.assertEqual(self.client.get("/api/v1/decide/", {"ids": str(self.namche.pk)}).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/decide/", {"ids": "999998,999999"}).status_code, 404)
        ok = self.client.get("/api/v1/decide/", {"ids": f"{self.namche.pk},{self.pokhara.pk}", "month": 1})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(len(ok.json()["places"]), 2)

    def test_season_guide(self):
        self.assertEqual(self.client.get("/api/v1/season-guide/", {"destination": "no-such-place"}).status_code, 404)
        r = self.client.get("/api/v1/season-guide/", {"destination": self.namche.slug})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["months"]), 12)

    def test_sentiment_without_reviews_is_honest(self):
        body = self.client.get(f"/api/v1/destinations/{self.namche.slug}/sentiment/").json()
        self.assertEqual(body["status"], "no_reviews")
        self.assertEqual(body["review_count"], 0)
        self.assertNotIn("overall", body)

    def test_share_and_revoke_hides_private_fields(self):
        owner = User.objects.create_user(email="owner@example.com", password="Str0ng!Pass1")
        plan = TravelPlan.objects.create(user=owner, title="Khumbu", itinerary_data={"days": 3, "notes": "door code 1234", "email": "owner@example.com"})
        other = APIClient(); other.force_authenticate(User.objects.create_user(email="x@example.com", password="Str0ng!Pass1"))
        self.assertEqual(other.post(f"/api/v1/travel-plans/{plan.pk}/share/").status_code, 404)
        c = APIClient(); c.force_authenticate(owner)
        token = c.post(f"/api/v1/travel-plans/{plan.pk}/share/").json()["token"]
        public = APIClient().get(f"/api/v1/shared-plans/{token}/").json()
        dumped = json.dumps(public)
        self.assertNotIn("door code", dumped)
        self.assertNotIn("owner@example.com", dumped)
        c.delete(f"/api/v1/travel-plans/{plan.pk}/share/")
        self.assertEqual(APIClient().get(f"/api/v1/shared-plans/{token}/").status_code, 404)

    def _plan(self, start):
        r = self.client.post("/api/v1/ml/itinerary/", data=json.dumps({"start_city": start, "days": 3, "travelers": 1, "interests": ["culture"]}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_itinerary_anchors_on_destination_slug_and_stays_nearby(self):
        with override_settings(ML_SERVICE_URL="http://127.0.0.1:9"):
            plan = self._plan(self.namche.slug.replace("-", " "))
        names = [d["name"] for day in plan["itinerary"] for d in day["destinations"]]
        self.assertIn("Namche Bazaar", names)
        self.assertNotIn("Khaptad National Park", names, "a 600 km jump is not a day trip")

    def test_itinerary_district_still_scoped(self):
        with override_settings(ML_SERVICE_URL="http://127.0.0.1:9"):
            plan = self._plan("Kaski")
        self.assertIn("Kaski", plan["data_note"])


class CMSBlockValidationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="cms@example.com", password="Admin!Pass123")
        self.client = APIClient(); self.client.force_authenticate(self.admin)
        page = ManagedPage.objects.create(route="/audit-test", key="audit-test", title="Audit test")
        self.section = ContentSection.objects.create(page=page, key="s1", title="S1")
        self.url = f"/api/v1/admin/sections/{self.section.pk}/blocks/"

    def post(self, block_type, data):
        return self.client.post(self.url, {"block_type": block_type, "data": data}, format="json")

    def test_gallery_rejects_http_and_missing_urls(self):
        self.assertEqual(self.post("gallery", {"images": [{"url": "http://insecure.test/a.jpg"}]}).status_code, 400)
        self.assertEqual(self.post("gallery", {"images": [{"alt": "no url"}]}).status_code, 400)
        self.assertIn(self.post("gallery", {"images": [{"url": "https://upload.wikimedia.org/a.jpg", "alt": "Lake"}]}).status_code, (200, 201))

    def test_live_grid_limit_and_map_range(self):
        self.assertEqual(self.post("hotel_grid", {"limit": 50}).status_code, 400)
        self.assertIn(self.post("destination_grid", {"limit": 6, "district": "Kaski"}).status_code, (200, 201))
        self.assertEqual(self.post("map", {"latitude": 127.7, "longitude": 85.3}).status_code, 400)
        self.assertEqual(self.post("statistics", {"items": [{"number": "77"}]}).status_code, 400)


class SpaFallbackTests(TestCase):
    def test_serves_index_without_cache(self):
        from Tourism.spa import spa_index
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "index.html").write_text("<!doctype html><div id=root></div>")
            with override_settings(FRONTEND_DIST_DIR=Path(tmp)):
                response = spa_index(RequestFactory().get("/destinations/anything"), path="destinations/anything")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Cache-Control"], "no-cache")
                self.assertIn(b"root", b"".join(response.streaming_content))

    def test_missing_build_is_404(self):
        from django.http import Http404
        from Tourism.spa import spa_index
        with tempfile.TemporaryDirectory() as tmp, override_settings(FRONTEND_DIST_DIR=Path(tmp)):
            with self.assertRaises(Http404):
                spa_index(RequestFactory().get("/x"))


class PageDescriptionMigrationTests(TestCase):
    def test_no_generated_descriptions_left(self):
        leftovers = [p.route for p in ManagedPage.objects.all() if p.meta_description.endswith("on the Nepal Yatra")]
        self.assertEqual(leftovers, [])


class GeoIPPrivacyTests(TestCase):
    def test_ip_is_not_sent_unless_a_view_needs_location(self):
        from unittest import mock
        from tourist.middleware import GeoIPMiddleware
        with mock.patch("tourist.middleware.geoip_lookup") as lookup:
            request = GeoIPMiddleware(lambda r: r)(RequestFactory().get("/api/v1/destinations/", REMOTE_ADDR="8.8.8.8"))
            self.assertEqual(lookup.call_count, 0)
            bool(request.geo_location)
            self.assertEqual(lookup.call_count, 1)
            local = GeoIPMiddleware(lambda r: r)(RequestFactory().get("/api/v1/x/", REMOTE_ADDR="10.0.0.5"))
            self.assertFalse(local.geo_location)
            self.assertEqual(lookup.call_count, 1)


class DirectoryDedupeTests(TestCase):
    def test_exact_repeat_rows_are_listed_once(self):
        from types import SimpleNamespace
        from tourist.views import _unique_places
        a = SimpleNamespace(pk=1, name="Police Station Baidam", phone="", latitude=28.215, longitude=83.956)
        b = SimpleNamespace(pk=2, name="Police Station Baidam", phone="", latitude=28.215, longitude=83.956)
        c = SimpleNamespace(pk=3, name="Police Station Baidam", phone="", latitude=28.300, longitude=83.956)
        self.assertEqual([r["id"] for r in _unique_places([a, b, c])], [1, 3])


class ImageOptimiseHelperTests(TestCase):
    def _upload(self, fmt, size=(64, 64), **save):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        buf = io.BytesIO()
        Image.new("RGB", size, "green").save(buf, format=fmt, **save)
        return SimpleUploadedFile(f"x.{fmt.lower()}", buf.getvalue())

    def test_gif_is_left_unchanged(self):
        from .image_optimize import optimise_image_upload
        upload = self._upload("GIF")
        result, report = optimise_image_upload(upload)
        self.assertIs(result, upload)
        self.assertFalse(report["optimised"])

    def test_original_kept_when_webp_would_not_be_smaller(self):
        from .image_optimize import optimise_image_upload
        upload = self._upload("WEBP", size=(8, 8))
        result, report = optimise_image_upload(upload)
        self.assertIs(result, upload)
        self.assertFalse(report["optimised"])

    def test_gps_metadata_is_removed(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .image_optimize import optimise_image_upload
        exif = Image.Exif()
        exif[0x8825] = {2: (27.0, 42.0, 0.0), 1: "N"}  # GPSInfo
        buf = io.BytesIO()
        Image.effect_noise((900, 600), 50).convert("RGB").save(buf, format="JPEG", quality=95, exif=exif.tobytes())
        self.assertIn(0x8825, Image.open(io.BytesIO(buf.getvalue())).getexif())
        result, report = optimise_image_upload(SimpleUploadedFile("gps.jpg", buf.getvalue()))
        self.assertTrue(report["optimised"])
        with Image.open(io.BytesIO(result.read())) as saved:
            self.assertEqual(saved.format, "WEBP")
            self.assertNotIn(0x8825, saved.getexif())

    def test_flag_parsing(self):
        from .image_optimize import wants_optimisation
        self.assertTrue(wants_optimisation("on"))
        self.assertFalse(wants_optimisation(None))
        self.assertFalse(wants_optimisation("0"))


class PublishedMetaDescriptionMigrationTests(TestCase):
    def test_snapshot_descriptions_follow_0088_but_keep_editor_text(self):
        import importlib
        from django.apps import apps as django_apps
        mig = importlib.import_module("tourist.migrations.0090_publish_page_meta_descriptions")
        about, _ = ManagedPage.objects.update_or_create(route="/about", defaults={
            "key": "about", "title": "About Us", "is_enabled": True, "status": "published",
            "published_snapshot": {"title": "About Us", "meta_description": "About Us on the Nepal Yatra"}})
        contact, _ = ManagedPage.objects.update_or_create(route="/contact", defaults={
            "key": "contact", "title": "Contact Us", "is_enabled": True, "status": "published",
            "published_snapshot": {"title": "Contact Us", "meta_description": "Written by our editor."}})
        mig.forwards(django_apps, None)
        about.refresh_from_db(); contact.refresh_from_db()
        self.assertEqual(about.published_snapshot["meta_description"], mig.DESCRIPTIONS["/about"])
        self.assertEqual(about.published_snapshot["title"], "About Us")
        self.assertEqual(contact.published_snapshot["meta_description"], "Written by our editor.")
        cache.clear()
        pages = APIClient().get("/api/v1/config/public/").json()["pages"]
        served = {p["route"]: p["meta_description"] for p in pages}
        self.assertEqual(served.get("/about"), mig.DESCRIPTIONS["/about"])
        self.assertNotIn("on the Nepal Yatra", " ".join(v or "" for v in served.values()))


class CMSCoversEveryPageTests(TestCase):
    """Migration 0091: every page route has a CMS record, mis-routed records fixed."""

    ROUTES = ["/cookie-policy", "/data-deletion", "/unsubscribe", "/before-you-travel", "/distances", "/search",
              "/discover", "/decide", "/trip", "/trip/:reference", "/plans/shared/:token", "/verify-email",
              "/reset-password", "/login/user", "/destinations/compare", "/safety", "/staff/destinations",
              "/staff/travel-plans", "/staff/feedback", "/privacy-policy", "/terms-of-service",
              "/safety/shared/:token"]

    def test_every_route_has_a_record_and_misrouted_ones_are_fixed(self):
        routes = dict(ManagedPage.objects.values_list("route", "key"))
        for route in self.ROUTES:
            self.assertIn(route, routes, route)
        self.assertEqual(routes["/privacy-policy"], "privacy-policy")
        self.assertEqual(routes["/terms-of-service"], "terms-of-service")
        self.assertEqual(routes["/safety/shared/:token"], "shared-trip")
        self.assertEqual(routes["/trip"], "trip-status")
        self.assertNotIn("/privacy", routes)
        self.assertNotIn("/terms", routes)
        # The public config merges the snapshot over live fields, so the
        # snapshot route must follow the fix.
        privacy = ManagedPage.objects.get(key="privacy-policy")
        self.assertEqual((privacy.published_snapshot or {}).get("route"), "/privacy-policy")

    def test_new_pages_start_with_hidden_draft_intro_and_private_ones_are_noindex(self):
        page = ManagedPage.objects.get(key="before-you-travel")
        intro = page.sections.get(key="intro")
        self.assertEqual(intro.status, "draft")
        self.assertFalse(intro.is_visible)
        self.assertTrue(page.search_visible)
        for key in ("shared-plan", "auth-reset-password", "staff-images", "auth-login-user"):
            self.assertFalse(ManagedPage.objects.get(key=key).search_visible, key)

    def test_public_config_serves_the_new_pages_without_draft_sections(self):
        cache.clear()
        pages = {p["route"]: p for p in APIClient().get("/api/v1/config/public/").json()["pages"]}
        self.assertIn("/cookie-policy", pages)
        self.assertEqual(pages["/privacy-policy"]["key"], "privacy-policy")
        self.assertEqual(pages["/before-you-travel"].get("sections") or [], [])

    def test_health_report_checks_every_page_and_flags_unpublished_changes(self):
        admin = User.objects.create_superuser(email="cms-health@example.com", password="Admin!Pass123")
        client = APIClient()
        client.force_authenticate(admin)
        total = ManagedPage.objects.count()
        self.assertGreater(total, 60)
        page = ManagedPage.objects.get(key="cookie-policy")
        page.title = "Cookie Policy (draft edit)"
        page.save(update_fields=["title"])
        data = client.get("/api/v1/admin/cms/", {"resource": "health"}).json()
        reports = data.get("pages") or data.get("results") or data.get("reports")
        self.assertIsNotNone(reports, data.keys())
        self.assertEqual(len(reports), total)
        cookie = [r for r in reports if r["key"] == "cookie-policy"][0]
        self.assertIn("unpublished_changes", [w["code"] for w in cookie["warnings"]])
        self.assertEqual(cookie["checks"]["published"], "warn")


class SecureExternalConfigurationTests(TestCase):
    def test_geoip_plain_http_is_disabled_without_a_network_call(self):
        from unittest.mock import patch
        from tourist.utils import geoip_lookup

        cache.clear()
        with override_settings(GEOIP_PROVIDER_URL="http://ip-api.com/json/{ip}"):
            with patch("tourist.utils.requests.get") as request:
                self.assertIsNone(geoip_lookup("8.8.8.8", blocking=True))
                request.assert_not_called()

    def test_geoip_uses_an_explicit_https_provider_when_configured(self):
        from unittest.mock import Mock, patch
        from tourist.utils import geoip_lookup

        cache.clear()
        response = Mock()
        response.json.return_value = {
            "country": "Nepal", "city": "Kathmandu", "lat": 27.7172, "lon": 85.3240,
        }
        with override_settings(GEOIP_PROVIDER_URL="https://geo.example.test/{ip}"):
            with patch("tourist.utils.requests.get", return_value=response) as request:
                result = geoip_lookup("8.8.4.4", blocking=True)
        self.assertEqual(result["city"], "Kathmandu")
        request.assert_called_once_with("https://geo.example.test/8.8.4.4", timeout=3)


class EmergencyCoverageAndHotlineTests(TestCase):
    def test_any_valid_nepal_coordinate_returns_protected_hotlines(self):
        response = APIClient().get("/api/v1/emergency/nearby/", {"latitude": 26.5, "longitude": 80.5, "radius_km": 10})
        self.assertEqual(response.status_code, 200)
        rows = {row["phone_number"] for row in response.json()["national_hotlines"]}
        self.assertTrue({"1144", "100", "102", "101", "103"}.issubset(rows))
        self.assertEqual(response.json()["location"]["source"], "coordinates")

    def test_coordinates_outside_nepal_are_rejected(self):
        response = APIClient().get("/api/v1/emergency/nearby/", {"latitude": 40, "longitude": -74})
        self.assertEqual(response.status_code, 400)
        self.assertIn("inside Nepal", response.json()["detail"])

    def test_admin_can_add_update_and_delete_noncritical_hotline(self):
        admin = User.objects.create_superuser(email="hotline-admin@example.com", password="Admin!Pass123")
        client = APIClient()
        client.force_authenticate(admin)
        payload = {
            "type": "mountain_rescue",
            "name": "Mountain rescue desk",
            "phone_number": "+977-1-5550000",
            "description": "Owner-supplied rescue desk",
            "source_name": "Owner verified directory",
            "source_url": "https://example.org/rescue",
        }
        created = client.post("/api/v1/admin/national-hotlines/", payload, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        changed = client.patch("/api/v1/admin/national-hotlines/", {**payload, "name": "Updated rescue desk"}, format="json")
        self.assertEqual(changed.status_code, 200, changed.content)
        deleted = client.delete("/api/v1/admin/national-hotlines/", {"type": "mountain_rescue"}, format="json")
        self.assertEqual(deleted.status_code, 200, deleted.content)

    def test_admin_cannot_delete_protected_hotline(self):
        admin = User.objects.create_superuser(email="hotline-protected@example.com", password="Admin!Pass123")
        client = APIClient()
        client.force_authenticate(admin)
        response = client.delete("/api/v1/admin/national-hotlines/", {"type": "police"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot be deleted", response.json()["detail"])
