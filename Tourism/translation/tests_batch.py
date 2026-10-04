from unittest import mock

from django.core.cache import cache
from django.test import TestCase


class TranslateBatchTests(TestCase):
    def setUp(self):
        cache.clear()

    def _post(self, texts, target="ne"):
        return self.client.post("/api/v1/translate/batch/", {"texts": texts, "target_language": target, "source_language": "en"},
                                content_type="application/json")

    def test_order_preserved_and_duplicates_translated_once(self):
        with mock.patch("translation.views.translate_text", side_effect=lambda t, *a: f"NE:{t}") as m:
            res = self._post(["Hotels", "Budget", "Hotels"])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["translations"], ["NE:Hotels", "NE:Budget", "NE:Hotels"])
        self.assertEqual(m.call_count, 2)

    def test_second_request_is_served_from_cache(self):
        with mock.patch("translation.views.translate_text", side_effect=lambda t, *a: f"NE:{t}") as m:
            self._post(["Hotels"])
            res = self._post(["Hotels"])
        self.assertEqual(res.json()["translations"], ["NE:Hotels"])
        self.assertEqual(m.call_count, 1)

    def test_provider_failure_returns_original_and_is_not_cached(self):
        with mock.patch("translation.views.translate_text", side_effect=lambda t, *a: t):
            self.assertEqual(self._post(["Hotels"]).json()["translations"], ["Hotels"])
        with mock.patch("translation.views.translate_text", side_effect=lambda t, *a: "होटल") as m:
            self.assertEqual(self._post(["Hotels"]).json()["translations"], ["होटल"])
        self.assertEqual(m.call_count, 1)

    def test_an_exception_for_one_item_does_not_fail_the_request(self):
        def flaky(text, *a):
            if text == "Bad":
                raise RuntimeError("boom")
            return f"NE:{text}"
        with mock.patch("translation.views.translate_text", side_effect=flaky):
            res = self._post(["Good", "Bad"])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["translations"], ["NE:Good", "Bad"])

    def test_oversized_batch_is_rejected(self):
        self.assertEqual(self._post([f"t{i}" for i in range(51)]).status_code, 400)
