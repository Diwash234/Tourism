from unittest import mock

from django.test import SimpleTestCase
from django.urls import resolve


class TranslateEndpointRoutingTests(SimpleTestCase):
    """The frontend posts to /api/v1/translate/batch/ on every language
    switch (src/i18n/index.js -> translatePageUi). The route was missing
    for months -- translation/urls.py was never included by any urlconf --
    so every batch 404'd, the frontend catch kept the English text, and the
    UI only ever switched the few strings served by the local dictionaries
    (the "language only partially switches" bug).

    Both api versions include tourist.urls, so reverse() here would return
    whichever was registered last; resolve() the literal paths instead to
    pin what the client actually requests."""

    def test_batch_url_is_routed(self):
        for prefix in ("/api/v1/", "/api/v2/"):
            match = resolve(f"{prefix}translate/batch/")
            self.assertEqual(match.url_name, "translate-batch")

    def test_single_text_url_is_routed(self):
        for prefix in ("/api/v1/", "/api/v2/"):
            match = resolve(f"{prefix}translate/")
            self.assertEqual(match.url_name, "translate-text")


class TranslateBatchEndpointTests(SimpleTestCase):
    def post_batch(self, payload):
        return self.client.post(
            "/api/v1/translate/batch/", payload, content_type="application/json"
        )

    def test_translates_each_item_in_order(self):
        with mock.patch(
            "translation.views.translate_text",
            side_effect=lambda text, *args, **kwargs: f"NE:{text}",
        ):
            response = self.post_batch(
                {"items": ["Hello", "World"], "target_language": "ne"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translations"], ["NE:Hello", "NE:World"])

    def test_one_failing_item_does_not_fail_the_batch(self):
        """A single poisonous string must not 500 the whole page batch --
        the caller silently keeps English for every item when the request
        errors. The failing item alone falls back to its original text."""

        def flaky(text, *args, **kwargs):
            if text == "poison":
                raise RuntimeError("provider exploded")
            return f"NE:{text}"

        with mock.patch("translation.views.translate_text", side_effect=flaky):
            response = self.post_batch(
                {"items": ["fine", "poison", "also fine"], "target_language": "ne"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["translations"], ["NE:fine", "poison", "NE:also fine"]
        )

    def test_identity_when_target_equals_source(self):
        response = self.post_batch(
            {"items": ["Hello"], "target_language": "en", "source_language": "en"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translations"], ["Hello"])

    def test_rejects_more_than_100_items(self):
        response = self.post_batch({"items": ["x"] * 101, "target_language": "ne"})
        self.assertEqual(response.status_code, 400)

    def test_rejects_non_list_items(self):
        response = self.post_batch({"items": "not-a-list", "target_language": "ne"})
        self.assertEqual(response.status_code, 400)

    def test_blank_items_survive(self):
        def fake(text, *args, **kwargs):
            return f"NE:{text}" if text else None

        with mock.patch("translation.views.translate_text", side_effect=fake):
            response = self.post_batch({"items": ["", None], "target_language": "ne"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["translations"], ["", ""])
