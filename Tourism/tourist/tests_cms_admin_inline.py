"""The Django admin CMS section inline must enforce the same storage boundary
as the JSON API.

``ContentSectionInline`` used to be a bare ``TabularInline`` over the full
``ContentSection`` model, and ``ManagedPageAdmin`` had no ``save_formset``
override. Saving through the admin therefore bypassed
``sanitize_cms_html``, the ``config`` allow-list, the CMS revision history, the
audit log and the public CMS cache invalidation. Since the public config API
falls back to live section rows whenever ``published_snapshot`` is empty, an
admin form save could publish unsanitized markup with no publish step at all.

These tests pin the fixed behaviour.
"""
from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.test import RequestFactory, TestCase

from .admin import ManagedPageAdmin
from .models import ContentSection, ManagedPage, User


class ContentSectionInlineBoundaryTests(TestCase):
    def setUp(self):
        self.page = ManagedPage.objects.create(
            key="admin-boundary", route="/admin-boundary", title="Boundary", status="draft"
        )
        self.admin_user = User.objects.create_superuser(
            "inline-admin@test.local", "InlineAdmin!123"
        )
        self.factory = RequestFactory()
        self.request = self.factory.post("/admin/tourist/managedpage/")
        self.request.user = self.admin_user
        self.model_admin = ManagedPageAdmin(ManagedPage, AdminSite())

    def _formset(self, section, body):
        FormSet = self.model_admin.get_inline_instances(
            self.request, self.page
        )[0].get_formset(self.request)
        data = {
            "sections-TOTAL_FORMS": "1",
            "sections-INITIAL_FORMS": "1",
            "sections-MIN_NUM_FORMS": "0",
            "sections-MAX_NUM_FORMS": "1000",
            "sections-0-id": str(section.pk),
            "sections-0-page": str(self.page.pk),
            "sections-0-key": section.key,
            "sections-0-title": section.title,
            "sections-0-subtitle": "",
            "sections-0-body": body,
            "sections-0-section_type": "text",
            "sections-0-layout_variant": "default",
            "sections-0-display_order": "1",
            "sections-0-is_visible": "on",
            "sections-0-is_reusable": "",
            "sections-0-status": "draft",
        }
        return FormSet(data=data, instance=self.page)

    def _save(self, body):
        section = ContentSection.objects.create(
            page=self.page,
            key="inline",
            title="Inline section",
            body="<p>old body</p>",
            section_type="text",
            status="draft",
        )
        formset = self._formset(section, body)
        self.assertTrue(formset.is_valid(), formset.errors)
        # save_formset is the ModelAdmin hook that runs before formset.save().
        self.model_admin.save_formset(self.request, None, formset, change=True)
        section.refresh_from_db()
        return section

    def test_admin_inline_sanitizes_section_body(self):
        section = self._save(
            '<p>keep me</p><script>alert(1)</script><img src=x onerror="steal()">'
        )
        self.assertIn("keep me", section.body)
        self.assertNotIn("<script", section.body.lower())
        self.assertNotIn("onerror", section.body.lower())

    def test_admin_inline_strips_javascript_urls(self):
        section = self._save('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn("javascript:", section.body.lower())

    def test_admin_inline_invalidates_public_cms_cache(self):
        cache.set("public:config:v1", {"stale": True}, 300)
        cache.set("seo:sitemap:v1", "stale", 300)
        self._save("<p>a fresh body</p>")
        self.assertIsNone(
            cache.get("public:config:v1"),
            "saving sections in the admin must invalidate the public CMS cache",
        )
        self.assertIsNone(cache.get("seo:sitemap:v1"))

    def test_admin_inline_whitelists_section_config(self):
        section = ContentSection.objects.create(
            page=self.page,
            key="cfg",
            title="Config section",
            body="<p>old</p>",
            section_type="text",
            status="draft",
            config={"unknown_key": "<script>bad()</script>", "align": "center"},
        )
        FormSet = self.model_admin.get_inline_instances(
            self.request, self.page
        )[0].get_formset(self.request)
        data = {
            "sections-TOTAL_FORMS": "1",
            "sections-INITIAL_FORMS": "1",
            "sections-MIN_NUM_FORMS": "0",
            "sections-MAX_NUM_FORMS": "1000",
            "sections-0-id": str(section.pk),
            "sections-0-page": str(self.page.pk),
            "sections-0-key": section.key,
            "sections-0-title": section.title,
            "sections-0-subtitle": "",
            "sections-0-body": "<p>new</p>",
            "sections-0-section_type": "text",
            "sections-0-layout_variant": "default",
            "sections-0-display_order": "1",
            "sections-0-is_visible": "on",
            "sections-0-is_reusable": "",
            "sections-0-status": "draft",
        }
        formset = FormSet(data=data, instance=self.page)
        self.assertTrue(formset.is_valid(), formset.errors)

        # Feed an unknown key straight onto the instance, as an un-whitelisted
        # config would arrive.
        formset.forms[0].instance.config = {
            "unknown_key": "<script>bad()</script>",
            "align": "center",
        }
        self.model_admin.save_formset(self.request, None, formset, change=True)

        section.refresh_from_db()
        self.assertNotIn("unknown_key", section.config or {})
        self.assertNotIn("<script", str(section.config).lower())
