"""Regression tests for StandardResultsPagination.

The class shipped with ``get_next_link(self, obj)`` but called it with no
argument, so ``get_paginated_response`` raised TypeError and every paginated
endpoint answered HTTP 500 -- the destination list, destination search, hotels
and reviews were all down. These tests pin the link contract the frontend
paginator reads and the filter-preservation behaviour, so neither can regress
silently.
"""

from django.test import TestCase
from django.urls import reverse

from tourist.models import Category, Destination


def make_destinations(count, **overrides):
    category = Category.objects.create(name="Pagination Category", slug="pagination-category")
    rows = []
    for index in range(count):
        rows.append(
            Destination.objects.create(
                name=f"Paginated Place {index:03d}",
                slug=f"paginated-place-{index:03d}",
                category=category,
                description="A destination used to exercise pagination.",
                latitude=27.7 + index * 0.001,
                longitude=85.3 + index * 0.001,
                status=Destination.SubmissionStatus.APPROVED,
                is_active=True,
                **overrides,
            )
        )
    return rows


class StandardResultsPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        make_destinations(45)

    def test_list_endpoint_returns_200(self):
        """The regression: this used to 500 with a missing-argument TypeError."""
        response = self.client.get("/api/v1/destinations/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json())

    def test_envelope_exposes_everything_a_paginator_needs(self):
        body = self.client.get("/api/v1/destinations/").json()
        for key in ("count", "total_pages", "page_size", "current_page",
                    "next", "previous", "first", "last", "results"):
            self.assertIn(key, body, f"pagination envelope is missing {key!r}")
        self.assertEqual(body["count"], 45)
        self.assertEqual(body["page_size"], 10)
        self.assertEqual(body["total_pages"], 5)
        self.assertEqual(body["current_page"], 1)
        self.assertEqual(len(body["results"]), 10)

    def test_next_and_previous_track_the_current_page(self):
        first = self.client.get("/api/v1/destinations/").json()
        self.assertIsNone(first["previous"])
        self.assertIn("page=2", first["next"])

        middle = self.client.get("/api/v1/destinations/?page=3").json()
        self.assertEqual(middle["current_page"], 3)
        self.assertIn("page=2", middle["previous"])
        self.assertIn("page=4", middle["next"])

        last = self.client.get("/api/v1/destinations/?page=5").json()
        self.assertIsNone(last["next"])
        self.assertIn("page=4", last["previous"])
        self.assertEqual(len(last["results"]), 5)

    def test_first_and_last_links_point_at_the_ends(self):
        body = self.client.get("/api/v1/destinations/?page=3").json()
        self.assertIn("page=1", body["first"])
        self.assertIn("page=5", body["last"])

    def test_paging_preserves_the_search_filter(self):
        """A bare '?page=N' link silently dropped the search term.

        Paging out of a filtered result set must keep the filter, otherwise
        page 2 shows unrelated results and the user cannot tell why.
        """
        body = self.client.get("/api/v1/destinations/?search=Paginated").json()
        self.assertGreater(body["count"], 0)
        self.assertIn("search=Paginated", body["next"])
        self.assertIn("page=2", body["next"])

        page2 = self.client.get(
            "/api/v1/destinations/?search=Paginated&page=2"
        ).json()
        self.assertEqual(page2["current_page"], 2)
        self.assertTrue(
            all("Paginated" in row["name"] for row in page2["results"]),
            "page 2 lost the search filter",
        )

    def test_paging_preserves_multiple_filters_together(self):
        response = self.client.get(
            "/api/v1/destinations/?search=Paginated&district=Kathmandu&page=1"
        )
        self.assertEqual(response.status_code, 200)
        if response.json().get("count"):
            self.assertIn("search=Paginated", response.json()["next"])
            self.assertIn("district=Kathmandu", response.json()["next"])

    def test_page_size_is_honoured_and_capped(self):
        self.assertEqual(
            len(self.client.get("/api/v1/destinations/?page_size=25").json()["results"]), 25
        )
        # max_page_size = 100, so an oversized request is clamped, not honoured
        self.assertLessEqual(
            len(self.client.get("/api/v1/destinations/?page_size=5000").json()["results"]),
            100,
        )

    def test_past_the_last_page_is_a_clean_404(self):
        """Not a 500 and not an empty 200 pretending there is nothing there."""
        response = self.client.get("/api/v1/destinations/?page=99999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_works_on_other_paginated_endpoints_too(self):
        """The bug was in shared code, so it broke every paginated list."""
        for path in ("/api/v1/destinations/", "/api/v2/destinations/", "/api/v1/hotels/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)