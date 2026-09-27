"""CMS content-block write-integrity regression tests.

Content blocks are the one CMS write path that used to bypass every
guarantee the rest of the CMS enforces. These tests pin the fixed behaviour
so it cannot silently regress:

  1. ``rich_text`` / ``html`` block payloads are sanitized at the STORAGE
     boundary, not merely at render time in the browser.
  2. Every block mutation (create / update / delete / reorder) writes a
     ``CMSRevision`` and an ``AuditLog`` row, so a block edit can be rolled
     back and is visible in the admin audit trail.
  3. Every block mutation invalidates the cached public CMS payload, so the
     public site can never keep serving a stale ``/config/public/``.
  4. A block edit on a legacy section that was never published does NOT
     publish itself; the pre-edit state is frozen and the change stays a
     draft until an explicit Publish.
  5. Block reordering validates its input: unknown ids, ids belonging to a
     different section, and out-of-range positions are rejected with 400
     instead of being written by a raw queryset ``.update()``.
"""
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditLog

from .models import (
    CMSRevision,
    ContentBlock,
    ContentSection,
    ManagedPage,
    User,
)


class ContentBlockWriteIntegrityTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "block-admin@test.local", "BlockAdmin!123"
        )
        self.page, _ = ManagedPage.objects.get_or_create(
            key="home",
            defaults={"route": "/", "title": "Nepal Yatra", "status": "published"},
        )
        self.page.status = "published"
        self.page.is_enabled = True
        self.page.save(update_fields=["status", "is_enabled"])
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        # A cache entry that must be dropped by any block mutation.
        cache.set("public:config:v1", {"stale": True}, 300)
        cache.set("seo:sitemap:v1", "stale", 300)
        cache.set("dest:map-points:v1", "stale", 300)

    def _section(self, key="blocks", **kwargs):
        section, _ = ContentSection.objects.get_or_create(
            page=self.page,
            key=key,
            defaults={
                "title": "Block section",
                "body": "Original body.",
                "section_type": "blocks",
                "status": "published",
            },
        )
        for field, value in kwargs.items():
            setattr(section, field, value)
        if kwargs:
            section.save()
        return section

    def _create_block(self, section, block_type="rich_text", data=None, **extra):
        return self.client.post(
            f"/api/v1/admin/sections/{section.pk}/blocks/",
            {"block_type": block_type, "data": data or {}, **extra},
            format="json",
        )

    # ------------------------------------------------------------------
    # 1. Storage-boundary sanitization
    # ------------------------------------------------------------------
    def test_rich_text_block_html_is_sanitized_before_storage(self):
        section = self._section()
        response = self._create_block(
            section,
            "rich_text",
            {
                "html": (
                    '<p>Keep me</p>'
                    '<script>alert("xss")</script>'
                    '<img src=x onerror="alert(1)">'
                    '<a href="javascript:alert(2)">click</a>'
                )
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        stored = ContentBlock.objects.get(pk=response.data["id"]).data["html"]
        self.assertIn("Keep me", stored)
        self.assertNotIn("<script", stored.lower())
        self.assertNotIn("onerror", stored.lower())
        self.assertNotIn("javascript:", stored.lower())

    def test_html_block_html_is_sanitized_before_storage(self):
        section = self._section()
        response = self._create_block(
            section, "html", {"html": '<div onclick="steal()">hi</div><script>x()</script>'}
        )
        self.assertEqual(response.status_code, 201, response.data)
        stored = ContentBlock.objects.get(pk=response.data["id"]).data["html"]
        self.assertNotIn("<script", stored.lower())
        self.assertNotIn("onclick", stored.lower())

    def test_nested_block_html_is_sanitized(self):
        section = self._section()
        response = self._create_block(
            section,
            "card_grid",
            {"items": [{"title": "T", "body": '<script>bad()</script><p>ok</p>'}]},
        )
        self.assertEqual(response.status_code, 201, response.data)
        stored = str(ContentBlock.objects.get(pk=response.data["id"]).data)
        self.assertNotIn("<script", stored.lower())

    def test_patch_sanitizes_block_html_too(self):
        section = self._section()
        created = self._create_block(section, "rich_text", {"html": "<p>safe</p>"})
        block_id = created.data["id"]
        response = self.client.patch(
            f"/api/v1/admin/blocks/{block_id}/",
            {"data": {"html": '<p>safe</p><script>bad()</script>'}},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        stored = ContentBlock.objects.get(pk=block_id).data["html"]
        self.assertNotIn("<script", stored.lower())

    # ------------------------------------------------------------------
    # 2. Audit log + revision history
    # ------------------------------------------------------------------
    def test_block_create_writes_revision_and_audit_log(self):
        section = self._section()
        response = self._create_block(section, "rich_text", {"html": "<p>Body</p>"})
        self.assertEqual(response.status_code, 201, response.data)

        revisions = CMSRevision.objects.filter(
            resource="sections", object_id=section.pk
        ).order_by("revision_number")
        self.assertTrue(revisions.exists(), "block create must record a CMS revision")
        latest = revisions.last()
        self.assertIn(
            "blocks",
            latest.snapshot,
            "the revision snapshot must capture the section's blocks",
        )
        self.assertTrue(
            AuditLog.objects.filter(action="cms.blocks.create").exists(),
            "block create must be visible in the admin audit log",
        )

    def test_block_update_writes_revision_and_audit_log(self):
        section = self._section()
        block_id = self._create_block(section, "rich_text", {"html": "<p>v1</p>"}).data["id"]
        before = CMSRevision.objects.filter(
            resource="sections", object_id=section.pk
        ).count()

        response = self.client.patch(
            f"/api/v1/admin/blocks/{block_id}/",
            {"title": "Renamed", "data": {"html": "<p>v2</p>"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        after = CMSRevision.objects.filter(
            resource="sections", object_id=section.pk
        ).count()
        self.assertGreater(after, before, "block update must add a revision")
        self.assertTrue(AuditLog.objects.filter(action="cms.blocks.update").exists())

    def test_block_delete_writes_audit_log(self):
        section = self._section()
        block_id = self._create_block(section, "rich_text", {"html": "<p>bye</p>"}).data["id"]
        response = self.client.delete(f"/api/v1/admin/blocks/{block_id}/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(ContentBlock.objects.filter(pk=block_id).exists())
        self.assertTrue(AuditLog.objects.filter(action="cms.blocks.update").exists())

    def test_reorder_writes_audit_log(self):
        section = self._section()
        first = self._create_block(section, "rich_text", {"html": "<p>1</p>"}).data["id"]
        second = self._create_block(section, "rich_text", {"html": "<p>2</p>"}).data["id"]
        AuditLog.objects.filter(action="cms.blocks.update").delete()

        response = self.client.post(
            "/api/v1/admin/blocks/reorder/",
            {"items": [{"id": second, "position": 1}, {"id": first, "position": 2}]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(ContentBlock.objects.get(pk=second).position, 1)
        self.assertEqual(ContentBlock.objects.get(pk=first).position, 2)
        self.assertTrue(AuditLog.objects.filter(action="cms.blocks.update").exists())

    # ------------------------------------------------------------------
    # 3. Public cache invalidation
    # ------------------------------------------------------------------
    def test_every_block_mutation_invalidates_the_public_cms_cache(self):
        section = self._section()
        block_id = self._create_block(section, "rich_text", {"html": "<p>1</p>"}).data["id"]

        for key in ("public:config:v1", "seo:sitemap:v1", "dest:map-points:v1"):
            cache.set(key, "stale", 300)
        self.client.patch(
            f"/api/v1/admin/blocks/{block_id}/", {"title": "x"}, format="json"
        )
        self.assertIsNone(cache.get("public:config:v1"))

        for key in ("public:config:v1", "seo:sitemap:v1", "dest:map-points:v1"):
            cache.set(key, "stale", 300)
        self.client.delete(f"/api/v1/admin/blocks/{block_id}/")
        self.assertIsNone(cache.get("public:config:v1"))

    # ------------------------------------------------------------------
    # 4. Draft isolation on legacy (never published) sections
    # ------------------------------------------------------------------
    def test_block_edit_on_legacy_published_section_does_not_self_publish(self):
        from .cms_publishing import sync_published_snapshot

        section = self._section(status="published", is_visible=True)
        # Freeze the pre-edit public state, exactly like a real publish.
        sync_published_snapshot(section)
        public_before = self._public_section_body(section.key)

        # A brand-new block on a section that has a frozen snapshot.
        self._create_block(section, "rich_text", {"html": "<p>draft only</p>"})

        public_after = self._public_section_body(section.key)
        self.assertEqual(
            public_before,
            public_after,
            "a block edit must stay a draft until an explicit Publish",
        )

    def test_first_block_edit_on_snapshotless_section_freezes_instead_of_publishing(self):
        section = self._section(status="published", is_visible=True)
        # No sync_published_snapshot() call: legacy row, public falls back to live.
        public_before = self._public_section_body(section.key)
        self.assertIsNotNone(public_before)

        self._create_block(section, "rich_text", {"html": "<p>should not leak</p>"})

        section.refresh_from_db()
        self.assertTrue(
            section.published_snapshot,
            "editing a snapshot-less published section must freeze its pre-edit state",
        )
        public_after = self._public_section_body(section.key)
        self.assertEqual(
            public_before,
            public_after,
            "the new block must not appear on the public site without a Publish",
        )

    def _public_section_body(self, key):
        anonymous = APIClient()
        payload = anonymous.get("/api/v1/config/public/").json()
        for page in payload.get("pages", []):
            for section in page.get("sections", []):
                if section.get("key") == key:
                    return section
        return None

    # ------------------------------------------------------------------
    # 5. Reorder input validation
    # ------------------------------------------------------------------
    def test_reorder_rejects_unknown_block_id(self):
        section = self._section()
        response = self.client.post(
            "/api/v1/admin/blocks/reorder/",
            {"items": [{"id": 999999, "position": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not exist", str(response.data).lower())

    def test_reorder_rejects_block_from_another_section(self):
        first = self._section("alpha")
        second = self._section("beta")
        other_block = self._create_block(second, "rich_text", {"html": "<p>x</p>"}).data["id"]

        response = self.client.post(
            f"/api/v1/admin/sections/{first.pk}/blocks/",
            {"action": "reorder", "items": [{"id": other_block, "position": 1}]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong", str(response.data))

    def test_reorder_rejects_out_of_range_position(self):
        section = self._section()
        block_id = self._create_block(section, "rich_text", {"html": "<p>x</p>"}).data["id"]
        for bad in (-1, 100001, "3", 1.5, True):
            with self.subTest(position=bad):
                response = self.client.post(
                    "/api/v1/admin/blocks/reorder/",
                    {"items": [{"id": block_id, "position": bad}]},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    ContentBlock.objects.get(pk=block_id).position,
                    1,
                    "a rejected position must not be written",
                )

    def test_reorder_rejects_non_list_items(self):
        response = self.client.post(
            "/api/v1/admin/blocks/reorder/", {"items": "nope"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_create_rejects_out_of_range_position(self):
        section = self._section()
        response = self._create_block(section, "rich_text", {"html": "<p>x</p>"}, position=-5)
        self.assertEqual(response.status_code, 400)
