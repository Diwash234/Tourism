"""Tests for the ML service request bounds and capability catalog.

The recommendation endpoint previously accepted an unbounded ``top_n``/``limit``
and an unbounded ``destinations`` array, so a single client could force
arbitrarily large work on a single-process service. The service also had no
discoverable capability catalog.
"""
import unittest

from fastapi.testclient import TestClient

from app import ML_MODEL_CATALOG, app

client = TestClient(app)


class ModelCatalogTests(unittest.TestCase):
    def test_catalog_lists_capabilities_in_openai_shape(self):
        response = client.get("/v1/models")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["object"], "list")
        data = payload["data"]
        self.assertGreaterEqual(len(data), 6)
        self.assertEqual(len({model["id"] for model in data}), len(data), "ids must be unique")
        for model in data:
            self.assertEqual(model["object"], "model")
            self.assertEqual(model["owned_by"], "nepal-yatra-ml-service")
        self.assertIn("nepal-yatra-recommendation", {model["id"] for model in data})

    def test_catalog_is_available_with_a_trailing_slash(self):
        self.assertEqual(client.get("/v1/models/").status_code, 200)

    def test_model_detail_resolves_and_404s(self):
        found = client.get("/v1/models/nepal-yatra-recommendation")
        self.assertEqual(found.status_code, 200)
        self.assertEqual(found.json()["id"], "nepal-yatra-recommendation")
        self.assertEqual(client.get("/v1/models/does-not-exist").status_code, 404)

    def test_catalog_ids_are_unique(self):
        ids = [model["id"] for model in ML_MODEL_CATALOG]
        self.assertEqual(len(ids), len(set(ids)))


class RecommendationRequestBoundsTests(unittest.TestCase):
    def test_rejects_out_of_range_result_counts(self):
        for payload in ({"top_n": 0}, {"top_n": 9999}, {"limit": -1}, {"limit": 10_000}):
            with self.subTest(payload=payload):
                response = client.post("/recommendation/", json=payload)
                self.assertEqual(response.status_code, 422, response.text)

    def test_accepts_result_counts_within_bounds(self):
        for payload in ({"top_n": 1}, {"top_n": 50}, {"limit": 7}):
            with self.subTest(payload=payload):
                response = client.post("/recommendation/", json=payload)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["success"])

    def test_result_count_is_capped(self):
        response = client.post("/recommendation/", json={"top_n": 50})
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json()["results"]), 50)

    def test_rejects_out_of_range_coordinates(self):
        for payload in (
            {"latitude": 91.0},
            {"latitude": -91.0},
            {"longitude": 181.0},
            {"longitude": -181.0},
        ):
            with self.subTest(payload=payload):
                response = client.post("/recommendation/", json=payload)
                self.assertEqual(response.status_code, 422, response.text)

    def test_accepts_valid_coordinates(self):
        response = client.post(
            "/recommendation/", json={"latitude": 28.2096, "longitude": 83.9856, "top_n": 3}
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_rejects_oversized_destination_payload(self):
        response = client.post(
            "/recommendation/", json={"destinations": [{"id": i} for i in range(101)]}
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_rejects_oversized_interest_string(self):
        response = client.post("/recommendation/", json={"interest": "x" * 500})
        self.assertEqual(response.status_code, 422, response.text)


if __name__ == "__main__":
    unittest.main()
